"""Deterministic return ownership and invalidation routing for conception V2.

The persisted return request contains only fields admitted by the authoritative
schema.  ``issue_kind`` is an invocation-time routing key encoded in the
schema's existing ``owner_basis`` text so a validator can recompute the route;
it is deliberately not added as a new contract field.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from .contracts import ContractRuntime, ContractValidationError


STAGE_ORDER = ("B0", "S1", "W1", "E1", "T1", "C1", "Q1", "P1", "H1")
_OWNER_BASIS_PREFIX = "§14.1 rule="


class ReturnRoutingError(ValueError):
    """A stable, fail-closed return routing error."""

    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(f"{code}: {message}")


@dataclass(frozen=True)
class RouteSpec:
    owner: str
    target_stage: str
    resume_stage: str
    resume_point: str
    invalidated_stages: tuple[str, ...]
    invalidated_h1_artifacts: tuple[str, ...]


_ISSUE_ROUTES: dict[str, tuple[str, str]] = {
    "baseline_packaging": ("B0", "B0"),
    "storyline": ("S1", "S1"),
    "world": ("W1", "W1"),
    "environment": ("E1", "E1"),
    "event_timeline": ("T1", "T1"),
    "character": ("C1", "C1"),
    "semantic_review": ("Q1", "Q1"),
    "package_assembly": ("P1", "P1"),
    "h1_plan": ("H1-A", "H1-A-plan"),
    "h1_assembly": ("H1-A", "H1-A-assemble"),
    "h1_fragment": ("H1-B", "H1-B"),
    "h1_html": ("H1-C", "H1-C"),
    "structural_fact_dependency": ("I2", "B0"),
}

_AUTHOR_PREFIX_OWNER = {
    "INT": "I0",
    "SUB": "I1",
    "WLD": "I2",
    "CHR": "I3",
    "CAU": "I4",
    "NAR": "I5",
}

_H1_INVALIDATION = {
    "H1-A-plan": ("plan", "fragments", "assembly", "html", "completion"),
    "H1-B": ("fragments", "assembly", "html", "completion"),
    "H1-A-assemble": ("assembly", "html", "completion"),
    "H1-C": ("html", "completion"),
}


def _fail(code: str, message: str) -> None:
    raise ReturnRoutingError(code, message)


def _author_owner(evidence_ids: Sequence[str]) -> str:
    owners: set[str] = set()
    for evidence_id in evidence_ids:
        prefix = evidence_id.split("-", 1)[0] if isinstance(evidence_id, str) else ""
        owner = _AUTHOR_PREFIX_OWNER.get(prefix)
        if owner is None:
            _fail(
                "ROUTE_NO_RESOLVER",
                f"author-locked evidence has no I0-I5 prefix resolver: {evidence_id!r}",
            )
        owners.add(owner)
    if len(owners) != 1:
        _fail(
            "ROUTE_AMBIGUOUS_OWNER",
            f"author-locked evidence resolves to multiple owners: {sorted(owners)}",
        )
    return next(iter(owners))


def _route_spec(issue_kind: str, evidence_ids: Sequence[str]) -> RouteSpec:
    if issue_kind == "author_locked":
        owner = _author_owner(evidence_ids)
        target_stage = owner
        resume_stage = "B0"
        resume_point = "B0"
    else:
        route = _ISSUE_ROUTES.get(issue_kind)
        if route is None:
            _fail("ROUTE_NO_RESOLVER", f"unknown issue kind: {issue_kind!r}")
        owner, resume_point = route
        target_stage = "H1" if owner.startswith("H1-") else owner
        resume_stage = "B0" if owner.startswith("I") else target_stage

    suffix_start = "B0" if target_stage.startswith("I") else target_stage
    try:
        start_index = STAGE_ORDER.index(suffix_start)
    except ValueError:
        _fail(
            "ROUTE_NO_RESOLVER",
            f"target stage has no invalidation suffix: {target_stage!r}",
        )
    invalidated_stages = STAGE_ORDER[start_index:]
    invalidated_h1 = (
        _H1_INVALIDATION[resume_point]
        if target_stage == "H1"
        else _H1_INVALIDATION["H1-A-plan"]
    )
    return RouteSpec(
        owner=owner,
        target_stage=target_stage,
        resume_stage=resume_stage,
        resume_point=resume_point,
        invalidated_stages=invalidated_stages,
        invalidated_h1_artifacts=invalidated_h1,
    )


def _issue_kind(owner_basis: Any) -> str:
    if not isinstance(owner_basis, str) or not owner_basis.startswith(
        _OWNER_BASIS_PREFIX
    ):
        _fail(
            "ROUTE_OWNER_BASIS_INVALID",
            "owner_basis does not contain the deterministic §14.1 rule key",
        )
    issue_kind = owner_basis[len(_OWNER_BASIS_PREFIX) :]
    if not issue_kind:
        _fail("ROUTE_OWNER_BASIS_INVALID", "owner_basis rule key is empty")
    return issue_kind


def validate_return_request(
    request: Mapping[str, Any],
    *,
    runtime: ContractRuntime | None = None,
) -> RouteSpec:
    """Schema-validate *request* and recompute all deterministic route fields."""

    contract_runtime = runtime or ContractRuntime()
    try:
        contract_runtime.validate(request, "return-request.schema.json")
    except ContractValidationError as error:
        _fail("ROUTE_SCHEMA_INVALID", str(error))

    issue_kind = _issue_kind(request.get("owner_basis"))
    evidence_ids = request.get("evidence_ids")
    if not isinstance(evidence_ids, list):
        _fail("ROUTE_SCHEMA_INVALID", "evidence_ids must be an array")
    spec = _route_spec(issue_kind, evidence_ids)

    expected = {
        "calculated_owner": spec.owner,
        "target_stage": spec.target_stage,
        "resume_stage": spec.resume_stage,
        "resume_point": spec.resume_point,
        "invalidated_stages": list(spec.invalidated_stages),
        "invalidated_h1_artifacts": list(spec.invalidated_h1_artifacts),
    }
    for field, value in expected.items():
        if request.get(field) != value:
            _fail(
                "ROUTE_DERIVATION_MISMATCH",
                f"{field} must be deterministically derived as {value!r}",
            )

    if request["origin_kind"] == "author":
        expected_kind = "author_revision"
    elif spec.target_stage.startswith("I"):
        expected_kind = "upstream_reentry"
    else:
        expected_kind = "local_revision"
    if request["return_kind"] != expected_kind:
        _fail(
            "ROUTE_KIND_MISMATCH",
            f"return_kind must be {expected_kind!r} for this route",
        )
    return spec


def route_return(
    *,
    run_id: str,
    return_id: str,
    origin_kind: str,
    origin_stage: str | None,
    issue_kind: str,
    problem: str,
    evidence_ids: Sequence[str],
    violated_contract: str,
    required_revision: str,
    author_decision: Mapping[str, str] | None,
    has_current_author_decision: bool,
    has_current_conception_completion: bool,
    runtime: ContractRuntime | None = None,
) -> dict[str, Any]:
    """Build a schema-valid return request from the §14 ownership table."""

    if not evidence_ids:
        _fail("ROUTE_EVIDENCE_REQUIRED", "at least one evidence ID is required")
    spec = _route_spec(issue_kind, evidence_ids)
    if origin_kind == "author":
        return_kind = "author_revision"
    elif spec.target_stage.startswith("I"):
        return_kind = "upstream_reentry"
    else:
        return_kind = "local_revision"

    request = {
        "schema_version": "2.0",
        "run_id": run_id,
        "return_id": return_id,
        "return_kind": return_kind,
        "origin_kind": origin_kind,
        "origin_stage": origin_stage,
        "author_decision": (
            dict(author_decision) if author_decision is not None else None
        ),
        "problem": problem,
        "evidence_ids": list(evidence_ids),
        "violated_contract": violated_contract,
        "calculated_owner": spec.owner,
        "owner_basis": f"{_OWNER_BASIS_PREFIX}{issue_kind}",
        "required_revision": required_revision,
        "target_stage": spec.target_stage,
        "resume_stage": spec.resume_stage,
        "resume_point": spec.resume_point,
        "invalidated_stages": list(spec.invalidated_stages),
        "invalidated_h1_artifacts": list(spec.invalidated_h1_artifacts),
        "invalidate_author_decision": (
            has_current_author_decision or origin_kind == "author"
        ),
        "invalidate_conception_completion": (
            has_current_conception_completion or origin_kind == "author"
        ),
        "status": "active",
    }
    validate_return_request(request, runtime=runtime)
    return request


__all__ = [
    "ReturnRoutingError",
    "RouteSpec",
    "STAGE_ORDER",
    "route_return",
    "validate_return_request",
]
