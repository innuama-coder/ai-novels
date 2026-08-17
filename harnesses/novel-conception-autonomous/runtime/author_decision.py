"""Validate and record an externally sealed author decision.

This module never invents, defaults, classifies, or rewrites author intent.
The caller supplies a sealed ``author-decision.json`` that already selects one
and only one public-contract branch.
"""

from __future__ import annotations

import copy
import json
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence

from .canonical import canonical_sha256, sha256_file
from .canonical import verify_manifest_integrity
from .contracts import ContractRuntime, ContractValidationError
from .coordinator import SealedDocument, StateTransition, seal_document
from .return_routing import ReturnRoutingError, route_return, validate_return_request


class AuthorDecisionError(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(f"{code}: {message}")


@dataclass(frozen=True)
class AuthorDecisionReceipt:
    decision: SealedDocument
    branch: str
    transition: StateTransition
    return_request: SealedDocument | None


_SCOPE_ROUTES = {
    "report": "h1_plan",
    "fragment": "h1_fragment",
    "html": "h1_html",
}
_STAGE_PREFIX_ROUTES = {
    "B0": "baseline_packaging",
    "S1": "storyline",
    "SLD": "storyline",
    "SL": "storyline",
    "SLC": "storyline",
    "W1": "world",
    "WR": "world",
    "WF": "world",
    "WS": "world",
    "END": "world",
    "E1": "environment",
    "ENV": "environment",
    "ZONE": "environment",
    "T1": "event_timeline",
    "EVD": "event_timeline",
    "EV": "event_timeline",
    "C1": "character",
    "CHD": "character",
    "SLOT": "character",
    "REL": "character",
    "DEV": "character",
    "Q1": "semantic_review",
    "FND": "semantic_review",
    "P1": "package_assembly",
}
_AUTHOR_PREFIXES = {"INT", "SUB", "WLD", "CHR", "CAU", "NAR"}
_SOURCE_ID_PATTERN = re.compile(
    r"^(INT|SUB|WLD|CHR|CAU|NAR|SLD|SL|SLC|WR|WF|WS|END|ENV|ZONE|"
    r"EVD|EV|CHD|SLOT|REL|FND|DEV)-[A-Za-z0-9._-]+$"
)


def _fail(code: str, message: str) -> None:
    raise AuthorDecisionError(code, message)


def _validate_sealed(
    event: SealedDocument, *, runtime: ContractRuntime
) -> None:
    if event.reference.get("sha256") != canonical_sha256(event.data):
        _fail("AUTHOR_DECISION_STALE_EVENT", "event hash does not bind its body")
    try:
        runtime.validate(event.data, "author-decision.schema.json")
    except ContractValidationError as error:
        _fail("AUTHOR_DECISION_SCHEMA_INVALID", str(error))


def _binding(
    root: str | Path,
    *,
    completion_path: str,
    manifest_path: str,
) -> dict[str, str]:
    package = Path(root).resolve()
    return {
        "completion_path": completion_path,
        "completion_sha256": sha256_file(package / "stage-completion.json"),
        "manifest_path": manifest_path,
        "manifest_sha256": sha256_file(package / "package-manifest.json"),
    }


def _logical_package_root(
    artifact_path: str,
    *,
    filename: str,
    pattern: str,
    code: str,
) -> str:
    if not isinstance(artifact_path, str) or "\\" in artifact_path:
        _fail(code, "logical artifact path is not canonical POSIX")
    path = PurePosixPath(artifact_path)
    root = path.parent.as_posix()
    if (
        path.name != filename
        or path.is_absolute()
        or ".." in path.parts
        or path.as_posix() != artifact_path
        or re.fullmatch(pattern, root) is None
    ):
        _fail(code, "logical artifact path is outside the accepted package root")
    return root


def _declared_source_ids(value: Any) -> set[str]:
    """Collect only values in explicit source registries or source fields."""

    found: set[str] = set()
    if isinstance(value, Mapping):
        for key, child in value.items():
            candidates: list[Any] = []
            if key == "source_id":
                candidates = [child]
            elif key == "source_ids" and isinstance(child, list):
                candidates = child
            elif key == "control_registry" and isinstance(child, list):
                candidates = [
                    item.get("id")
                    for item in child
                    if isinstance(item, Mapping)
                ]
            elif key == "authority_partition" and isinstance(child, Mapping):
                candidates = [
                    item
                    for partition in child.values()
                    if isinstance(partition, list)
                    for item in partition
                ]
            elif key in {
                "mandatory_controls",
                "development_freedoms",
                "must_ask",
                "open_items",
            } and isinstance(child, list):
                candidates = child
            found.update(
                candidate
                for candidate in candidates
                if isinstance(candidate, str)
                and _SOURCE_ID_PATTERN.fullmatch(candidate)
            )
            found.update(_declared_source_ids(child))
    elif isinstance(value, list):
        for child in value:
            found.update(_declared_source_ids(child))
    return found


def _package_source_ids(root: Path) -> set[str]:
    values: set[str] = set()
    for path in root.rglob("*.json"):
        try:
            values.update(
                _declared_source_ids(
                    json.loads(path.read_text(encoding="utf-8"))
                )
            )
        except (OSError, UnicodeError, json.JSONDecodeError):
            continue
    return values


def _validate_package(
    root: Path, *, profile: str, runtime: ContractRuntime, code: str
) -> dict[str, Any]:
    try:
        manifest = json.loads(
            (root / "package-manifest.json").read_text(encoding="utf-8")
        )
        runtime.validate(manifest, "package-manifest.schema.json")
        verify_manifest_integrity(manifest, root=root)
    except Exception as error:
        _fail(code, str(error))
    if manifest.get("package_profile") != profile or manifest.get("verdict") != "ready":
        _fail(code, f"expected ready {profile} package")
    return manifest


def validate_author_decision_event(
    event: SealedDocument,
    *,
    coordinator: Any,
    p1_package: str | Path | None = None,
    h1_package: str | Path | None = None,
    html_package: str | Path | None = None,
    run_state: SealedDocument | None = None,
    runtime: ContractRuntime | None = None,
) -> str:
    """Validate externality, current-state binding, and optional package bytes."""

    contract_runtime = runtime or ContractRuntime()
    _validate_sealed(event, runtime=contract_runtime)
    state = coordinator.state
    if (
        event.data["run_id"] != state["run_id"]
        or state["status"] != "waiting_author"
        or state["active_return"] is not None
        or state["author_decision"] is not None
        or list(state["current_stage_completions"]) != [
            "B0", "S1", "W1", "E1", "T1", "C1", "Q1", "P1", "H1"
        ]
    ):
        _fail(
            "AUTHOR_DECISION_NOT_CURRENT",
            "event requires the current completed H1 waiting state",
        )
    if run_state is not None and (
        run_state.reference != coordinator.state_reference
        or run_state.data != state
    ):
        _fail("AUTHOR_DECISION_STATE_MISMATCH", "run-state is not current")

    if p1_package is not None:
        p1_root = Path(p1_package).resolve()
        _validate_package(
            p1_root,
            profile="conception-package",
            runtime=contract_runtime,
            code="AUTHOR_DECISION_P1_INVALID",
        )
        expected_machine = _binding(
            p1_root,
            completion_path="P1/stage-completion.json",
            manifest_path="P1/package-manifest.json",
        )
        if event.data["machine_package"] != expected_machine:
            _fail("AUTHOR_DECISION_P1_MISMATCH", "event does not bind current P1")
        if state["current_stage_completions"]["P1"] != {
            "stage": "P1",
            "path": expected_machine["completion_path"],
            "sha256": expected_machine["completion_sha256"],
        }:
            _fail("AUTHOR_DECISION_P1_MISMATCH", "P1 completion is not current")
    if h1_package is not None:
        h1_root = Path(h1_package).resolve()
        _validate_package(
            h1_root,
            profile="h1-stage",
            runtime=contract_runtime,
            code="AUTHOR_DECISION_H1_INVALID",
        )
        current_h1 = state["current_stage_completions"]["H1"]
        h1_logical_root = _logical_package_root(
            current_h1["path"],
            filename="stage-completion.json",
            pattern=r"H1/stage(?:-attempt-0*[1-9][0-9]*)?",
            code="AUTHOR_DECISION_H1_MISMATCH",
        )
        expected_human = _binding(
            h1_root,
            completion_path=f"{h1_logical_root}/stage-completion.json",
            manifest_path=f"{h1_logical_root}/package-manifest.json",
        )
        actual = event.data["human_review_package"]
        for field, value in expected_human.items():
            if actual[field] != value:
                _fail(
                    "AUTHOR_DECISION_H1_MISMATCH",
                    "event does not bind current H1",
                )
        if state["current_stage_completions"]["H1"] != {
            "stage": "H1",
            "path": expected_human["completion_path"],
            "sha256": expected_human["completion_sha256"],
        }:
            _fail("AUTHOR_DECISION_H1_MISMATCH", "H1 completion is not current")
        try:
            execution = json.loads(
                (h1_root / "execution-record.json").read_text(encoding="utf-8")
            )
            html_manifest = execution["workspace_artifacts"]["html_manifest"]
            if (
                not isinstance(html_manifest, Mapping)
                or set(html_manifest) != {"path", "sha256"}
                or sha256_file(
                    h1_root / "sources" / "html-package-manifest.json"
                )
                != html_manifest["sha256"]
            ):
                raise ValueError("unbound HTML manifest")
            html_logical_root = _logical_package_root(
                html_manifest["path"],
                filename="package-manifest.json",
                pattern=r"H1/html(?:-attempt-0*[1-9][0-9]*)?",
                code="AUTHOR_DECISION_HTML_MISMATCH",
            )
        except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
            _fail("AUTHOR_DECISION_H1_INVALID", str(error))
    else:
        html_logical_root = "H1/html"
    if html_package is not None:
        html_root = Path(html_package).resolve()
        _validate_package(
            html_root,
            profile="h1-html",
            runtime=contract_runtime,
            code="AUTHOR_DECISION_HTML_INVALID",
        )
        html = html_root / "human-review-report.html"
        actual = event.data["human_review_package"]
        if (
            actual["html_path"]
            != f"{html_logical_root}/human-review-report.html"
            or actual["html_sha256"] != sha256_file(html)
        ):
            _fail("AUTHOR_DECISION_HTML_MISMATCH", "event does not bind HTML")
    if event.data["decision"] == "revise":
        if p1_package is not None:
            source_ids = _package_source_ids(Path(p1_package).resolve())
            requested_sources = {
                source_id
                for target in event.data["revision_targets"]
                for source_id in target["source_ids"]
            }
            missing_sources = requested_sources - source_ids
            if missing_sources:
                _fail(
                    "AUTHOR_DECISION_SOURCE_ID_INVALID",
                    f"unknown P1 source IDs: {sorted(missing_sources)}",
                )
        if html_package is not None:
            document = (
                Path(html_package).resolve() / "human-review-report.html"
            ).read_text(encoding="utf-8")
            visible = set(
                re.findall(r'data-(?:element|node|visual)-id="([^"]+)"', document)
            )
            requested_visible = {
                element_id
                for target in event.data["revision_targets"]
                for element_id in target["visible_element_ids"]
            }
            missing_visible = requested_visible - visible
            if missing_visible:
                _fail(
                    "AUTHOR_DECISION_VISIBLE_ID_INVALID",
                    f"unknown H1 visible IDs: {sorted(missing_visible)}",
                )
    return event.data["decision"]


def _target_issue(target: Mapping[str, Any]) -> str:
    scope = target["target_scope"]
    if scope in _SCOPE_ROUTES:
        return _SCOPE_ROUTES[scope]
    source_ids = target["source_ids"]
    prefixes = {
        source_id.split("-", 1)[0]
        for source_id in source_ids
        if isinstance(source_id, str)
    }
    if prefixes and prefixes <= _AUTHOR_PREFIXES:
        return "author_locked"
    routes = {_STAGE_PREFIX_ROUTES.get(prefix) for prefix in prefixes}
    if len(routes) != 1 or None in routes:
        _fail(
            "AUTHOR_DECISION_OWNER_UNRESOLVED",
            "conception target source IDs do not resolve to one owner",
        )
    return next(iter(routes))


def _route_revision(
    event: SealedDocument,
    *,
    return_id: str,
    runtime: ContractRuntime,
) -> SealedDocument:
    targets: Sequence[Mapping[str, Any]] = event.data["revision_targets"]
    routed: list[tuple[str, dict[str, Any]]] = []
    for index, target in enumerate(targets):
        issue = _target_issue(target)
        evidence = list(target["source_ids"]) or list(target["visible_element_ids"])
        try:
            request = route_return(
                run_id=event.data["run_id"],
                return_id=f"{return_id}-{index + 1}",
                origin_kind="author",
                origin_stage=None,
                issue_kind=issue,
                problem=target["requested_change"],
                evidence_ids=evidence,
                violated_contract=f"author revision target_scope={target['target_scope']}",
                required_revision=target["requested_change"],
                author_decision=event.reference,
                has_current_author_decision=True,
                has_current_conception_completion=False,
                runtime=runtime,
            )
        except ReturnRoutingError as error:
            _fail(error.code, str(error))
        routed.append((issue, request))
    route_keys = {
        (
            item["calculated_owner"],
            item["target_stage"],
            item["resume_stage"],
            item["resume_point"],
        )
        for _, item in routed
    }
    if len(route_keys) != 1:
        _fail(
            "AUTHOR_DECISION_CROSS_OWNER_REVISION",
            "split revision targets by deterministic owner/resume point",
        )
    base = copy.deepcopy(routed[0][1])
    base["return_id"] = return_id
    base["problem"] = "\n".join(
        target["requested_change"] for target in targets
    )
    base["required_revision"] = base["problem"]
    base["evidence_ids"] = sorted(
        {
            value
            for target in targets
            for value in (
                list(target["source_ids"])
                or list(target["visible_element_ids"])
            )
        }
    )
    validate_return_request(base, runtime=runtime)
    return seal_document(base, f"returns/{return_id}.json")


def record_author_decision(
    output_path: str | Path | None = None,
    *,
    event: SealedDocument,
    coordinator: Any,
    next_state_path: str,
    p1_package: str | Path | None = None,
    h1_package: str | Path | None = None,
    html_package: str | Path | None = None,
    run_state: SealedDocument | None = None,
    return_id: str = "RET-AUTHOR-REVISION",
    runtime: ContractRuntime | None = None,
) -> AuthorDecisionReceipt:
    """Record exactly the externally selected branch and no other branch."""

    del output_path  # The external sealed event is authoritative; never rewrite it.
    contract_runtime = runtime or ContractRuntime()
    branch = validate_author_decision_event(
        event,
        coordinator=coordinator,
        p1_package=p1_package,
        h1_package=h1_package,
        html_package=html_package,
        run_state=run_state,
        runtime=contract_runtime,
    )
    if branch == "revise":
        request = _route_revision(
            event, return_id=return_id, runtime=contract_runtime
        )
        transition = coordinator.apply_return_request(
            request=request,
            next_state_path=next_state_path,
            conception_completion_current=False,
        )
    else:
        request = None
        transition = coordinator.accept_author_decision(
            decision=event, next_state_path=next_state_path
        )
    return AuthorDecisionReceipt(
        decision=event,
        branch=branch,
        transition=transition,
        return_request=request,
    )


__all__ = [
    "AuthorDecisionError",
    "AuthorDecisionReceipt",
    "record_author_decision",
    "validate_author_decision_event",
]
