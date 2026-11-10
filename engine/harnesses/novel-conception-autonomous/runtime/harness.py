"""Portable orchestration entry point for the autonomous conception V2 chain.

This module deliberately starts at the already-rendered H1 boundary.  Earlier
stage skills remain independent owners; the harness only publishes the formal
H1 completion, consumes one externally sealed author decision, and, for the
approved branch only, publishes the final development-admission completion.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .author_decision import AuthorDecisionReceipt, record_author_decision
from .contracts import ContractRuntime
from .final_completion import FinalCompletionReceipt, publish_final_completion
from .h1_completion import H1CompletionReceipt, publish_h1_completion
from .coordinator import STAGE_ORDER, SealedDocument


class HarnessRunError(ValueError):
    """Stable fail-closed public harness error."""

    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(f"{code}: {message}")


@dataclass(frozen=True)
class HarnessRunReceipt:
    branch: str
    h1: H1CompletionReceipt
    decision: AuthorDecisionReceipt
    final: FinalCompletionReceipt | None
    state: SealedDocument


_STATE_KEYS = frozenset({"h1", "approved", "revise", "rejected", "final"})


def _fail(code: str, message: str) -> None:
    raise HarnessRunError(code, message)


def _validate_paths(next_state_paths: Mapping[str, str]) -> None:
    if set(next_state_paths) != _STATE_KEYS:
        _fail(
            "HARN_STATE_PATHS_INVALID",
            "next_state_paths must contain exactly h1/approved/revise/rejected/final",
        )
    values = list(next_state_paths.values())
    if any(not isinstance(value, str) or not value.strip() for value in values):
        _fail("HARN_STATE_PATHS_INVALID", "state paths must be non-empty strings")
    if len(values) != len(set(values)):
        _fail("HARN_STATE_PATHS_INVALID", "state paths must be unique")


def _sealed_transition(transition: Any) -> SealedDocument:
    return SealedDocument(
        data=transition.snapshot,
        reference=transition.reference,
    )


def _is_path_alias(path: Path) -> bool:
    """Detect an alias on the caller-supplied output root itself.

    The public boundary owns this path object and its H1/stage children.  It
    deliberately does not attempt an unbounded audit of every ancestor.
    """

    if path.is_symlink():
        return True
    is_junction = getattr(path, "is_junction", None)
    return bool(is_junction is not None and is_junction())


def _validate_output_root(root: Path) -> bool:
    """Return whether this invocation is recovering one exact H1 orphan.

    Fresh invocations still require an absent or empty root.  The only
    non-empty shape admitted here is ``H1/stage``; the formal H1 publisher owns
    validation of every file inside that stage package.
    """

    if not root.exists():
        return False
    if not root.is_dir() or root.is_symlink():
        _fail(
            "HARN_OUTPUT_ROOT_INVALID",
            "output_root must be a real directory",
        )
    children = list(root.iterdir())
    if not children:
        return False
    if len(children) != 1 or children[0].name != "H1":
        _fail(
            "HARN_OUTPUT_ROOT_INVALID",
            "non-empty output_root may contain only an H1/stage orphan",
        )
    h1_root = children[0]
    if not h1_root.is_dir() or h1_root.is_symlink():
        _fail(
            "HARN_OUTPUT_ROOT_INVALID",
            "H1 retry container must be a real directory",
        )
    h1_children = list(h1_root.iterdir())
    if (
        len(h1_children) != 1
        or h1_children[0].name != "stage"
        or not h1_children[0].is_dir()
        or h1_children[0].is_symlink()
    ):
        _fail(
            "HARN_OUTPUT_ROOT_INVALID",
            "non-empty output_root must have exactly H1/stage",
        )
    return True


def run_from_rendered_h1(
    output_root,
    *,
    coordinator,
    stage_packages,
    p1_package,
    plan_package,
    plan_input_gate,
    plan_workspace_state,
    fragment_package,
    fragment_workspace_state,
    assembly_package,
    assembly_workspace_state,
    html_package,
    rendered_workspace,
    author_event,
    development_handoff,
    next_state_paths,
    runtime=None,
):
    """Run the formal H1 -> author gate -> optional final-completion boundary.

    ``author_event`` is consumed exactly as supplied.  The harness never creates
    or edits an author decision.  ``revise`` and ``rejected`` are terminal
    receipts for this invocation and therefore carry ``final=None``.
    """

    contract_runtime = runtime or ContractRuntime()
    if not isinstance(next_state_paths, Mapping):
        _fail("HARN_STATE_PATHS_INVALID", "next_state_paths must be a mapping")
    _validate_paths(next_state_paths)
    supplied_root = Path(output_root)
    if _is_path_alias(supplied_root):
        _fail(
            "HARN_OUTPUT_ROOT_INVALID",
            "output_root itself must not be a symlink or junction",
        )
    root = supplied_root.resolve()
    _validate_output_root(root)
    if not isinstance(stage_packages, Mapping):
        _fail("HARN_STAGE_PACKAGES_INVALID", "stage_packages must be a mapping")
    if set(stage_packages) != set(STAGE_ORDER[:-1]):
        _fail(
            "HARN_STAGE_PACKAGES_INVALID",
            "stage_packages must contain exactly B0 through P1 and no H1",
        )

    h1_root = root / "H1" / "stage"
    final_root = root / "completion"
    h1 = publish_h1_completion(
        h1_root,
        p1_package=p1_package,
        plan_package=plan_package,
        plan_input_gate=plan_input_gate,
        plan_workspace_state=plan_workspace_state,
        fragment_package=fragment_package,
        fragment_workspace_state=fragment_workspace_state,
        assembly_package=assembly_package,
        assembly_workspace_state=assembly_workspace_state,
        html_package=html_package,
        rendered_workspace=rendered_workspace,
        coordinator=coordinator,
        next_state_path=next_state_paths["h1"],
        runtime=contract_runtime,
    )
    waiting_state = _sealed_transition(h1.transition)
    branch = author_event.data.get("decision") if hasattr(author_event, "data") else None
    if branch not in {"approved", "revise", "rejected"}:
        _fail("HARN_AUTHOR_BRANCH_INVALID", "external decision branch is invalid")
    decision = record_author_decision(
        event=author_event,
        coordinator=coordinator,
        next_state_path=next_state_paths[branch],
        p1_package=p1_package,
        h1_package=h1_root,
        html_package=html_package,
        run_state=waiting_state,
        runtime=contract_runtime,
    )
    decision_state = _sealed_transition(decision.transition)
    final = None
    if branch == "approved":
        current_packages = dict(stage_packages)
        current_packages["H1"] = h1_root
        final = publish_final_completion(
            final_root,
            run_state=decision_state,
            stage_packages=current_packages,
            p1_package=p1_package,
            h1_package=h1_root,
            html_package=html_package,
            author_decision=author_event,
            development_handoff=development_handoff,
            coordinator=coordinator,
            next_state_path=next_state_paths["final"],
            runtime=contract_runtime,
        )
        state = _sealed_transition(final.transition)
    else:
        state = decision_state
    return HarnessRunReceipt(
        branch=branch,
        h1=h1,
        decision=decision,
        final=final,
        state=state,
    )


__all__ = [
    "HarnessRunError",
    "HarnessRunReceipt",
    "run_from_rendered_h1",
]
