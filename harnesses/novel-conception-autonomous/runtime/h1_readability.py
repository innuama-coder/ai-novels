"""Production-owned H1 author-facing readability review contract.

This boundary is deliberately outside the shared autonomous schema catalog so
adding the human-facing gate cannot change sealed B0--P1 implementation
identities.  It validates a review against exact author-facing bytes and the
producer identities that created the plan and fragments.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence

from jsonschema import Draft202012Validator

from . import canonical as rt
from .coordinator import SealedDocument, seal_document


DIMENSIONS = (
    "natural_zh",
    "readability",
    "humanized_character_voice",
    "scene_not_spec",
    "excludes_internal_ids_and_audit_jargon",
)
REVIEW_ROOT = "reviews/h1-human-readability"


class H1ReadabilityError(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(f"{code}: {message}")


def _fail(code: str, message: str) -> None:
    raise H1ReadabilityError(code, message)


def _schema() -> dict[str, Any]:
    path = (
        Path(__file__).resolve().parent
        / "production_contracts"
        / "h1-human-readability-review.schema.json"
    )
    return json.loads(path.read_text(encoding="utf-8"))


def _validate_schema(value: Mapping[str, Any]) -> None:
    errors = sorted(
        Draft202012Validator(_schema()).iter_errors(dict(value)),
        key=lambda item: list(item.absolute_path),
    )
    if errors:
        first = errors[0]
        location = "/".join(str(item) for item in first.absolute_path)
        _fail("H1_READABILITY_REVIEW_SCHEMA_INVALID", f"{location}: {first.message}")


def _contained_file(
    root: Path, reference: Mapping[str, Any], *, code: str
) -> Path:
    logical = reference.get("path")
    if not isinstance(logical, str) or "\\" in logical:
        _fail(code, "reference path must be canonical POSIX")
    parts = PurePosixPath(logical)
    if parts.is_absolute() or any(part in {"", ".", ".."} for part in parts.parts):
        _fail(code, "reference path is not contained")
    physical = root.joinpath(*parts.parts).resolve()
    try:
        physical.relative_to(root.resolve())
    except ValueError:
        _fail(code, "reference escapes root")
    if not physical.is_file() or rt.sha256_file(physical) != reference.get("sha256"):
        _fail(code, logical)
    return physical


def expected_inputs(
    *,
    artifact_root: str | Path,
    html: Mapping[str, Any],
    report: Mapping[str, Any],
    fragment_manifest: Mapping[str, Any],
    fragment_package: Mapping[str, Any],
    h1_completion: Mapping[str, Any] | None = None,
    h1_manifest: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    root = Path(artifact_root).resolve()
    html_path = _contained_file(root, html, code="H1_READABILITY_HTML_INVALID")
    report_path = _contained_file(root, report, code="H1_READABILITY_REPORT_INVALID")
    manifest_path = _contained_file(
        root, fragment_manifest, code="H1_READABILITY_FRAGMENT_MANIFEST_INVALID"
    )
    package_path = _contained_file(
        root, fragment_package, code="H1_READABILITY_FRAGMENT_PACKAGE_INVALID"
    )
    for optional, code in (
        (h1_completion, "H1_READABILITY_COMPLETION_INVALID"),
        (h1_manifest, "H1_READABILITY_H1_MANIFEST_INVALID"),
    ):
        if optional is not None:
            _contained_file(root, optional, code=code)
    try:
        package = json.loads(package_path.read_text(encoding="utf-8"))
        fragments = package["fragments"]
    except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError) as error:
        _fail("H1_READABILITY_FRAGMENT_PACKAGE_INVALID", str(error))
    projected: list[dict[str, str]] = []
    seen: set[str] = set()
    for fragment in fragments:
        fragment_id = fragment.get("id")
        text = fragment.get("text")
        if not isinstance(fragment_id, str) or fragment_id in seen or not isinstance(text, str):
            _fail("H1_READABILITY_FRAGMENT_PACKAGE_INVALID", "fragment identity/text")
        seen.add(fragment_id)
        projected.append(
            {
                "fragment_id": fragment_id,
                "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            }
        )
    if not projected:
        _fail("H1_READABILITY_FRAGMENT_PACKAGE_INVALID", "no fragments")
    # Reading all author-facing bytes here makes mutation checks part of the
    # review boundary even though their exact refs are returned unchanged.
    html_path.read_text(encoding="utf-8")
    report_path.read_text(encoding="utf-8")
    manifest_path.read_bytes()
    return {
        "h1_completion": copy.deepcopy(dict(h1_completion)) if h1_completion else None,
        "h1_manifest": copy.deepcopy(dict(h1_manifest)) if h1_manifest else None,
        "html": copy.deepcopy(dict(html)),
        "report": copy.deepcopy(dict(report)),
        "fragment_manifest": copy.deepcopy(dict(fragment_manifest)),
        "fragment_package": copy.deepcopy(dict(fragment_package)),
        "fragments": projected,
    }


def _manifest(root: Path, *, profile: str) -> dict[str, Any]:
    try:
        value = json.loads((root / "package-manifest.json").read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        _fail("H1_READABILITY_PACKAGE_INVALID", str(error))
    if value.get("package_profile") != profile or value.get("verdict") != "ready":
        _fail("H1_READABILITY_PACKAGE_INVALID", profile)
    try:
        rt.verify_manifest_integrity(value, root=root)
    except rt.ManifestIntegrityError as error:
        _fail("H1_READABILITY_PACKAGE_INVALID", str(error))
    return value


def prepublish_contract(
    *,
    plan_package: str | Path,
    fragment_package_root: str | Path,
    assembly_package: str | Path,
    html_package: str | Path,
    rendered_workspace: SealedDocument,
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    """Derive exact review inputs and producer identities from sealed packages."""

    roots = {
        "plan": Path(plan_package).resolve(),
        "fragment": Path(fragment_package_root).resolve(),
        "assembly": Path(assembly_package).resolve(),
        "html": Path(html_package).resolve(),
    }
    manifests = {
        key: _manifest(roots[key], profile=profile)
        for key, profile in (
            ("plan", "h1-plan"),
            ("fragment", "h1-fragments"),
            ("assembly", "h1-assembly"),
            ("html", "h1-html"),
        )
    }
    artifacts = rendered_workspace.data.get("artifacts", {})
    for key, field in (
        ("plan", "plan_manifest"),
        ("fragment", "fragment_manifest"),
        ("assembly", "assembly_manifest"),
        ("html", "html_manifest"),
    ):
        expected = artifacts.get(field)
        if not isinstance(expected, dict) or expected.get("sha256") != rt.sha256_file(
            roots[key] / "package-manifest.json"
        ):
            _fail("H1_READABILITY_WORKSPACE_STALE", field)
    logical_roots = {
        key: PurePosixPath(artifacts[f"{key}_manifest"]["path"]).parent.as_posix()
        for key in ("plan", "fragment", "assembly", "html")
    }
    roles = {key: manifests[key]["artifact_roles"] for key in manifests}

    def logical_ref(key: str, role: str) -> dict[str, str]:
        local = roles[key][role]
        physical = roots[key].joinpath(*PurePosixPath(local["path"]).parts)
        if rt.sha256_file(physical) != local["sha256"]:
            _fail("H1_READABILITY_PACKAGE_INVALID", f"{key}:{role}")
        return {
            "path": f"{logical_roots[key]}/{local['path']}",
            "sha256": local["sha256"],
        }

    fragment_package_ref = logical_ref("fragment", "fragment_package")
    fragment_package_value = json.loads(
        roots["fragment"].joinpath(
            *PurePosixPath(roles["fragment"]["fragment_package"]["path"]).parts
        ).read_text(encoding="utf-8")
    )
    fragments = [
        {
            "fragment_id": item["id"],
            "text_sha256": hashlib.sha256(item["text"].encode("utf-8")).hexdigest(),
        }
        for item in fragment_package_value["fragments"]
    ]
    if not fragments or len({item["fragment_id"] for item in fragments}) != len(fragments):
        _fail("H1_READABILITY_FRAGMENT_PACKAGE_INVALID", "fragment coverage")
    inputs = {
        "h1_completion": None,
        "h1_manifest": None,
        "html": logical_ref("html", "html"),
        "report": logical_ref("assembly", "human_review_report_json"),
        "fragment_manifest": copy.deepcopy(artifacts["fragment_manifest"]),
        "fragment_package": fragment_package_ref,
        "fragments": fragments,
    }
    identities: list[dict[str, str]] = []
    for key in ("plan", "fragment"):
        session = json.loads(
            roots[key].joinpath(
                *PurePosixPath(roles[key]["generation_session"]["path"]).parts
            ).read_text(encoding="utf-8")
        )
        identity = session.get("identity") or session.get("work_identity")
        if not isinstance(identity, dict) or not {
            "task_id", "thread_id"
        } <= set(identity):
            _fail("H1_READABILITY_PRODUCER_IDENTITY_INVALID", key)
        identities.append(
            {"task_id": identity["task_id"], "thread_id": identity["thread_id"]}
        )
    return inputs, identities


def validate_review(
    review: Mapping[str, Any],
    *,
    expected_run_id: str,
    expected_session_id: str,
    expected_phase: str,
    inputs: Mapping[str, Any],
    producer_identities: Sequence[Mapping[str, str]],
    expected_verdict: str,
) -> dict[str, Any]:
    _validate_schema(review)
    reviewer = review["reviewer"]
    if any(
        reviewer["task_id"] == identity.get("task_id")
        or reviewer["thread_id"] == identity.get("thread_id")
        for identity in producer_identities
    ):
        _fail("H1_READABILITY_REVIEW_NOT_INDEPENDENT", "reviewer reused producer identity")
    if (
        review["run_id"] != expected_run_id
        or review["session_id"] != expected_session_id
        or review["phase"] != expected_phase
        or review["inputs"] != dict(inputs)
        or [item["id"] for item in review["dimensions"]] != list(DIMENSIONS)
        or review["verdict"] != expected_verdict
    ):
        _fail("H1_READABILITY_REVIEW_STALE", review["review_id"])
    dimensions = {item["id"]: item["verdict"] for item in review["dimensions"]}
    if expected_verdict == "pass":
        if any(value != "pass" for value in dimensions.values()) or review["findings"]:
            _fail("H1_READABILITY_REVIEW_NOT_PASS", review["review_id"])
    else:
        if all(value == "pass" for value in dimensions.values()) or not review["findings"]:
            _fail("H1_READABILITY_FAILURE_INVALID", review["review_id"])
        # Evidence containment is checked below using caller-supplied texts in
        # ``validate_failure_evidence``; keeping it separate avoids hidden I/O.
    return copy.deepcopy(dict(review))


def validate_failure_evidence(
    review: Mapping[str, Any], *, report_text: str, fragment_texts: Mapping[str, str]
) -> None:
    for finding in review["findings"]:
        haystack = (
            report_text
            if finding["artifact_kind"] == "report"
            else fragment_texts.get(finding["artifact_id"])
        )
        if not isinstance(haystack, str) or finding["evidence"] not in haystack:
            _fail("H1_READABILITY_FAILURE_EVIDENCE_INVALID", finding["finding_id"])


def seal_review(review: Mapping[str, Any]) -> SealedDocument:
    _validate_schema(review)
    return seal_document(
        dict(review), f"{REVIEW_ROOT}/{review['review_id']}.json"
    )


__all__ = [
    "DIMENSIONS",
    "H1ReadabilityError",
    "expected_inputs",
    "prepublish_contract",
    "seal_review",
    "validate_failure_evidence",
    "validate_review",
]
