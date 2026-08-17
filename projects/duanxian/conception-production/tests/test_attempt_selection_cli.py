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
    module_name = "duanxian_attempt_selection_test_entrypoint"
    spec = importlib.util.spec_from_file_location(module_name, ENTRYPOINT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def test_workspace_selects_attempt_one_and_two(entrypoint, tmp_path):
    assert entrypoint._workspace(tmp_path, "W1") == (
        tmp_path / "workspaces" / "W1-attempt-01"
    )
    assert entrypoint._workspace(tmp_path, "W1", attempt=2) == (
        tmp_path / "workspaces" / "W1-attempt-02"
    )


@pytest.mark.parametrize("attempt", [0, -1, True, None, 1.5, "2"])
def test_workspace_rejects_non_positive_attempts(entrypoint, tmp_path, attempt):
    with pytest.raises(ValueError, match="positive integer"):
        entrypoint._workspace(tmp_path, "W1", attempt=attempt)


@pytest.mark.parametrize(
    ("attempt", "explicit", "expected_name"),
    [(1, False, "W1-attempt-01"), (2, True, "W1-attempt-02")],
)
def test_stage_lifecycle_never_drifts_between_attempt_workspaces(
    entrypoint, monkeypatch, tmp_path, attempt, explicit, expected_name
):
    run_root = tmp_path / "run"
    payload_path = tmp_path / "payload.json"
    payload_path.write_text(json.dumps({"candidate": "phase"}), encoding="utf-8")
    gate = SimpleNamespace(reference={"path": "gate.json", "sha256": "a" * 64})
    order = SimpleNamespace(data={"action": "W1"})
    captured: dict[str, Path] = {}

    class Runtime:
        @staticmethod
        def start_w1_session(workspace, **kwargs):
            captured["start"] = workspace
            return {"session_id": "W1-session", "phases": []}

        @staticmethod
        def submit_w1_phase(workspace, **kwargs):
            captured["submit"] = workspace
            return {"path": "phase.json", "sha256": "b" * 64}

        @staticmethod
        def run_w1(package, **kwargs):
            captured["finalize"] = kwargs["controlled_workspace"]
            return {"world": "model"}

    store = SimpleNamespace(
        load_document=lambda reference: gate,
        pending_work_order=lambda: order,
    )
    context = SimpleNamespace(
        store=store,
        state=SimpleNamespace(data={"revision": 2}),
        active_return=None,
    )

    def execute_stage_work(context_arg, *, work_order, actor, executor):
        assert context_arg is context
        executor("coordinator", gate)
        receipt = SimpleNamespace(
            completion=SimpleNamespace(
                data={"stage": "W1", "status": "completed"},
                reference={"path": "completion.json", "sha256": "c" * 64},
            )
        )
        successor = SimpleNamespace(state=SimpleNamespace(data={"revision": 3}))
        return receipt, successor

    monkeypatch.setattr(entrypoint, "_paths", lambda run_id: (run_root, tmp_path))
    monkeypatch.setattr(
        entrypoint,
        "issue_stage",
        lambda run_id, stage: {"input_gate": gate.reference},
    )
    monkeypatch.setattr(entrypoint, "_stage_runtime", lambda stage: Runtime)
    monkeypatch.setattr(
        entrypoint.prod, "resume_production_run", lambda path: context
    )
    monkeypatch.setattr(entrypoint.prod, "execute_stage_work", execute_stage_work)

    if explicit:
        start = entrypoint.start_stage("run-14", "W1", attempt=attempt)
        submit = entrypoint.submit_stage(
            "run-14", "W1", "world-rules", payload_path, attempt=attempt
        )
        finalize = entrypoint.finalize_stage("run-14", "W1", attempt=attempt)
    else:
        start = entrypoint.start_stage("run-14", "W1")
        submit = entrypoint.submit_stage(
            "run-14", "W1", "world-rules", payload_path
        )
        finalize = entrypoint.finalize_stage("run-14", "W1")

    expected = run_root / "workspaces" / expected_name
    assert captured == {"start": expected, "submit": expected, "finalize": expected}
    for result in (start, submit, finalize):
        assert result["attempt"] == attempt
        assert result["workspace"] == str(expected)


@pytest.mark.parametrize(
    ("action", "extra_args"),
    [
        ("start-w1", []),
        ("submit-w1", ["--phase", "world-rules", "--payload", "payload.json"]),
        ("finalize-w1", []),
    ],
)
def test_cli_routes_attempt_to_non_s1_lifecycle_only(
    entrypoint, monkeypatch, capsys, action, extra_args
):
    captured = {}

    monkeypatch.setattr(
        entrypoint,
        "start_stage",
        lambda *args, **kwargs: captured.update(args=args, kwargs=kwargs) or {},
    )
    monkeypatch.setattr(
        entrypoint,
        "submit_stage",
        lambda *args, **kwargs: captured.update(args=args, kwargs=kwargs) or {},
    )
    monkeypatch.setattr(
        entrypoint,
        "finalize_stage",
        lambda *args, **kwargs: captured.update(args=args, kwargs=kwargs) or {},
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [str(ENTRYPOINT), "run-14", action, *extra_args, "--attempt", "2"],
    )

    entrypoint.main()
    capsys.readouterr()

    assert captured["kwargs"] == {"attempt": 2}


def test_cli_does_not_change_issue_or_s1_protocol(entrypoint, monkeypatch, capsys):
    calls = []
    monkeypatch.setattr(
        entrypoint,
        "issue_stage",
        lambda *args, **kwargs: calls.append((args, kwargs)) or {},
    )
    monkeypatch.setattr(
        entrypoint,
        "start_stage",
        lambda *args, **kwargs: calls.append((args, kwargs)) or {},
    )

    monkeypatch.setattr(
        sys,
        "argv",
        [str(ENTRYPOINT), "run-14", "issue-w1", "--attempt", "2"],
    )
    entrypoint.main()
    capsys.readouterr()

    monkeypatch.setattr(
        sys,
        "argv",
        [str(ENTRYPOINT), "run-14", "start-s1", "--attempt", "2"],
    )
    entrypoint.main()
    capsys.readouterr()

    assert calls == [(('run-14', 'W1'), {}), (('run-14', 'S1'), {})]


@pytest.mark.parametrize(
    ("action", "function_name"),
    [
        ("issue-q1", "issue_q1"),
        ("start-q1-controller", "start_q1_controller"),
    ],
)
def test_cli_attempt_option_does_not_change_q1_protocol(
    entrypoint, monkeypatch, capsys, action, function_name
):
    calls = []
    monkeypatch.setattr(
        entrypoint,
        function_name,
        lambda *args, **kwargs: calls.append((args, kwargs)) or {},
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [str(ENTRYPOINT), "run-14", action, "--attempt", "2"],
    )

    entrypoint.main()
    capsys.readouterr()

    assert calls == [(('run-14',), {})]


@pytest.mark.parametrize("attempt", ["0", "-1", "not-an-integer"])
def test_cli_rejects_non_positive_attempt(entrypoint, monkeypatch, attempt):
    called = False

    def start_stage(*args, **kwargs):
        nonlocal called
        called = True
        return {}

    monkeypatch.setattr(entrypoint, "start_stage", start_stage)
    monkeypatch.setattr(
        sys,
        "argv",
        [str(ENTRYPOINT), "run-14", "start-w1", "--attempt", attempt],
    )

    with pytest.raises(SystemExit) as exit_info:
        entrypoint.main()

    assert exit_info.value.code == 2
    assert called is False


def test_retry_attempt_two_isolated_from_fully_sealed_incomplete_attempt_one(
    entrypoint, monkeypatch, tmp_path
):
    run_root = tmp_path / "run"
    attempt_one = run_root / "workspaces" / "W1-attempt-01"
    attempt_two = run_root / "workspaces" / "W1-attempt-02"
    evidence_one = attempt_one / "generation-evidence"
    evidence_one.mkdir(parents=True)
    (attempt_one / "generation-session.json").write_text(
        json.dumps(
            {
                "session_id": "W1-attempt-01-session",
                "phases": [f"phase-{index}" for index in range(1, 6)],
            }
        ),
        encoding="utf-8",
    )
    for index in range(1, 6):
        (evidence_one / f"{index:02d}-phase-{index}.json").write_text(
            json.dumps({"sequence": index, "sealed": True}),
            encoding="utf-8",
        )
    assert not (run_root / "W1" / "stage-completion.json").exists()

    def snapshot(path: Path) -> dict[str, bytes]:
        return {
            item.relative_to(path).as_posix(): item.read_bytes()
            for item in sorted(path.rglob("*"))
            if item.is_file()
        }

    attempt_one_before = snapshot(attempt_one)
    payload_path = tmp_path / "phase-two-payload.json"
    payload_path.write_text(json.dumps({"candidate": "attempt-02"}), encoding="utf-8")
    gate = SimpleNamespace(reference={"path": "gate.json", "sha256": "a" * 64})
    order = SimpleNamespace(data={"action": "W1"})
    captured: dict[str, Path] = {}

    class Runtime:
        @staticmethod
        def start_w1_session(workspace, **kwargs):
            captured["start"] = workspace
            assert workspace == attempt_two
            assert not workspace.exists()
            workspace.mkdir(parents=True)
            session = {
                "session_id": "W1-attempt-02-session",
                "phases": ["world-rules"],
            }
            (workspace / "generation-session.json").write_text(
                json.dumps(session), encoding="utf-8"
            )
            return session

        @staticmethod
        def submit_w1_phase(workspace, **kwargs):
            captured["submit"] = workspace
            assert workspace == attempt_two
            session = json.loads(
                (workspace / "generation-session.json").read_text(encoding="utf-8")
            )
            assert session["session_id"] == "W1-attempt-02-session"
            evidence = workspace / "generation-evidence"
            evidence.mkdir()
            target = evidence / "01-world-rules.json"
            target.write_text(json.dumps(kwargs["payload"]), encoding="utf-8")
            return {"path": str(target), "sha256": "b" * 64}

        @staticmethod
        def run_w1(package, **kwargs):
            captured["finalize"] = kwargs["controlled_workspace"]
            assert kwargs["controlled_workspace"] == attempt_two
            assert (
                kwargs["controlled_workspace"] / "generation-evidence" / "01-world-rules.json"
            ).exists()
            return {"world": "attempt-02-model"}

    store = SimpleNamespace(
        load_document=lambda reference: gate,
        pending_work_order=lambda: order,
    )
    context = SimpleNamespace(
        store=store,
        state=SimpleNamespace(data={"revision": 2}),
        active_return=None,
    )

    def execute_stage_work(context_arg, *, work_order, actor, executor):
        assert context_arg is context
        executor("coordinator", gate)
        receipt = SimpleNamespace(
            completion=SimpleNamespace(
                data={"stage": "W1", "status": "completed"},
                reference={"path": "W1/stage-completion.json", "sha256": "c" * 64},
            )
        )
        successor = SimpleNamespace(state=SimpleNamespace(data={"revision": 3}))
        return receipt, successor

    monkeypatch.setattr(entrypoint, "_paths", lambda run_id: (run_root, tmp_path))
    monkeypatch.setattr(
        entrypoint,
        "issue_stage",
        lambda run_id, stage: {"input_gate": gate.reference},
    )
    monkeypatch.setattr(entrypoint, "_stage_runtime", lambda stage: Runtime)
    monkeypatch.setattr(
        entrypoint.prod, "resume_production_run", lambda path: context
    )
    monkeypatch.setattr(entrypoint.prod, "execute_stage_work", execute_stage_work)

    start = entrypoint.start_stage("run-14", "W1", attempt=2)
    assert snapshot(attempt_one) == attempt_one_before
    submit = entrypoint.submit_stage(
        "run-14", "W1", "world-rules", payload_path, attempt=2
    )
    assert snapshot(attempt_one) == attempt_one_before
    finalize = entrypoint.finalize_stage("run-14", "W1", attempt=2)

    assert snapshot(attempt_one) == attempt_one_before
    assert captured == {"start": attempt_two, "submit": attempt_two, "finalize": attempt_two}
    for result in (start, submit, finalize):
        assert result["attempt"] == 2
        assert result["workspace"] == str(attempt_two)
