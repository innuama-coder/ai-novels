"""Production T1 runner for autonomous novel-conception V2."""

from __future__ import annotations

import sys as _sys
from pathlib import Path as _Path
_ENGINE = _Path(__file__).resolve()
_ENGINE = _ENGINE.parent
_ENGINE = _ENGINE.parent
_ENGINE = _ENGINE.parent
_ENGINE = _ENGINE.parent
_sys.path.insert(0, str(_ENGINE))
import sys as _sys
from pathlib import Path as _Path
_ENGINE = _Path(__file__).resolve()
_ENGINE = _ENGINE.parent
_ENGINE = _ENGINE.parent
_ENGINE = _ENGINE.parent
_sys.path.insert(0, str(_ENGINE))

import copy
import importlib
import json
import os
import re
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Mapping, Sequence


rt = importlib.import_module("harnesses.novel-conception-autonomous.runtime")
stage_identity = importlib.import_module(
    "harnesses.novel-conception-autonomous.runtime.stage_implementation_identity"
)
s1_runtime = importlib.import_module(
    "skills.novel-storyline-architecture-designer.scripts.run_v2"
)
w1_runtime = importlib.import_module(
    "skills.novel-world-model-designer.scripts.run_v2"
)
e1_runtime = importlib.import_module(
    "skills.novel-environment-system-designer.scripts.run_v2"
)
t1_contract_22 = importlib.import_module(
    "skills.novel-event-timeline-designer.scripts.contract_22"
)
t1_contract_23 = importlib.import_module(
    "skills.novel-event-timeline-designer.scripts.contract_23"
)
t1_contract_24 = importlib.import_module(
    "skills.novel-event-timeline-designer.scripts.contract_24"
)
t1_contract_25 = importlib.import_module(
    "skills.novel-event-timeline-designer.scripts.contract_25"
)
_HERE = Path(__file__).resolve()
_REPO = _HERE.parents[3]
_SKILL = _HERE.parents[1]
_S1_SKILL = _REPO / "skills" / "novel-storyline-architecture-designer"
_W1_SKILL = _REPO / "skills" / "novel-world-model-designer"
_E1_SKILL = _REPO / "skills" / "novel-environment-system-designer"
_SCHEMAS = _REPO / "docs" / "ai-novel-workflow" / "contracts" / "autonomous-v2"

PHASES = (
    "event-demand-scan",
    "global-timeline",
    "event-and-causality-model",
    "cross-line-state-test",
    "final-event-model",
)
PHASE_FIELDS = {
    "event-demand-scan": (
        "event_demands",
        "e1_universe_digest_bundle",
        "e1_capability_graph_digest",
        "e1_occurrence_requirement_digest",
    ),
    "global-timeline": (
        "design_decisions",
        "event_span",
        "timeline_axes",
        "narrative_timing_constraints",
        "initial_condition_registry",
        "initial_anchor_option_selection_ledger",
        "planned_event_registry",
        "process_state_subject_registry",
        "planned_proposition_registry",
        "planned_causal_edges",
        "transition_event_cover",
        "milestone_event_buckets",
        "connection_event_paths",
        "obligation_event_plan",
        "capability_occurrence_event_cover",
        "authority_token_instance_ledger",
        "lifecycle_scope",
        "lifecycle_contract_registry",
    ),
    "event-and-causality-model": (
        "proposition_registry",
        "major_events",
        "causal_edges",
        "environment_placement",
    ),
    "cross-line-state-test": (
        "storyline_event_sequences",
        "connection_realization",
        "obligation_realizations",
        "state_ledger",
        "information_changes",
        "event_coverage_ledger",
        "authority_partition",
        "derivation_claims",
        "open_items",
    ),
    "final-event-model": ("model",),
}
_LEGACY_PHASE_FIELDS_2_1 = {
    "event-demand-scan": ("event_demands",),
    "global-timeline": (
        "design_decisions",
        "event_span",
        "timeline_axes",
        "narrative_timing_constraints",
    ),
    "event-and-causality-model": (
        "proposition_registry",
        "major_events",
        "causal_edges",
        "environment_placement",
    ),
    "cross-line-state-test": (
        "storyline_event_sequences",
        "connection_realization",
        "obligation_realizations",
        "state_ledger",
        "information_changes",
        "event_coverage_ledger",
        "authority_partition",
        "derivation_claims",
        "open_items",
    ),
    "final-event-model": ("model",),
}
_LEGACY_PHASE_FIELDS_2_0 = {
    "event-demand-scan": ("event_demands",),
    "global-timeline": (
        "design_decisions",
        "event_span",
        "timeline_axes",
        "narrative_timing_constraints",
    ),
    "event-and-causality-model": (
        "major_events",
        "causal_edges",
        "environment_placement",
    ),
    "cross-line-state-test": (
        "storyline_event_sequences",
        "connection_realization",
        "state_ledger",
        "information_changes",
        "event_coverage_ledger",
        "authority_partition",
        "derivation_claims",
        "open_items",
    ),
    "final-event-model": ("model",),
}
_FORBIDDEN_MODEL_KEYS = {
    "storylines",
    "world_model",
    "environment_system",
    "characters",
    "character_profiles",
    "scenes",
    "scene_text",
    "prose",
}
_FORBIDDEN_NESTED_KEYS = {
    "psychology",
    "inner_monologue",
    "scene_text",
    "dialogue",
    "camera",
    "chapter",
    "chapter_plan",
}
_ALLOWED_ROOT_FILES = {
    "input-gate.json",
    "event-timeline.json",
    "generation-session.json",
    "generation-evidence-index.json",
    "execution-record.json",
    "event-preview.md",
    "validation.json",
    "package-manifest.json",
    "stage-completion.json",
}
_ALLOWED_SOURCE_PREFIXES = (
    "sources/B0/",
    "sources/S1/",
    "sources/W1/",
    "sources/E1/",
)

_RESPONSIBILITY_ORDER = (
    "background",
    "setup",
    "trigger",
    "development",
    "turn_or_crisis",
    "result",
    "aftermath",
)
_RESPONSIBILITY_TOKEN = re.compile(
    r"\[RESP:(background|setup|trigger|development|turn_or_crisis|result|aftermath)\]"
)
_WORLD_TIME_TOKEN = re.compile(r"\[WT:(\d{6})\]")
_TIMING_TOKEN = re.compile(
    r"\[REL:(linear|concurrent|memory|analepsis|convergence|association|independent-root)\]"
)
_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_LEDGER_KIND_TOKEN = re.compile(r"\[KIND:(state|resource|authority)\]")
_CAUSAL_MECHANISM = re.compile(
    r"^\[CAUSE_RESULT_SHA256:([0-9a-f]{64})\]"
    r"\[CAUSE_PRESSURE_SHA256:([0-9a-f]{64})\]\s+(.+)$"
)
_CAUSAL_CONDITION = re.compile(
    r"^\[PRECONDITION_SHA256:([0-9a-f]{64})\]\s+(.+)$"
)

CURRENT_MODEL_SCHEMA_VERSION = "2.5"
LEGACY_MODEL_SCHEMA_VERSIONS = frozenset({"2.0", "2.1", "2.2", "2.3", "2.4"})
T1_PLAN_REVIEW_PROTOCOL = "t1-initial-event-plan-semantics-v5"
_TRUSTED_LEGACY_IMPLEMENTATION_PAIRS = {
    "2.0": frozenset(
        {
            (
                "59b5101b12b55ac6ecc01bc7c624c242565f0be02662efcca0e2417113858028",
                "e3d46b4f72d50f1495fd895c77441bc75c9067fcb45e21cdd83fc54e9595b56c",
            )
        }
    ),
    "2.1": frozenset(),
    # The last 2.2 producer/runtime pair is preserved for exact historical
    # package replay.  Its package allowlist remains independently closed.
    "2.2": frozenset(
        {
            (
                "39b8d29b1860476e0e4653a35716a76ce5ddf9d5ec006a5c6f92b0935fe98487",
                "6aa9eebadb677b7054b521bc54a47f554783c0064759617d505f75fd82956dc2",
            )
        }
    ),
    # T1 2.3 reached a sealed implementation/session identity but never
    # produced a released ready package.  Trust the exact implementation
    # snapshot for provenance audit; package replay remains independently
    # closed by the empty package-identity inventory below.
    "2.3": frozenset(
        {
            (
                "21c94ef28a13a5273772dd1bf48ffdb5bd9aa852504960d478180663d1d9c45f",
                "4c0074e9e19eb57a717d03527f7dcd23e36185e632cb6e5966b58c19b8cae8b8",
            )
        }
    ),
    "2.4": frozenset(),
}
_TRUSTED_LEGACY_IMPLEMENTATION_BINDING_SETS = {
    "2.3": frozenset(
        {
            frozenset(
                {
                    ("runtime/b0_completion.py", "04375ce0eb5ea39a8e8ec1eff2da39c3ac43002bf1303c6bc1dde0c0e763aba1"),
                    ("runtime/baseline.py", "452dac5e08d553d76826aa3f1ba6d9b48111aa3285a9e0c5c64d50486afca97b"),
                    ("runtime/canonical.py", "342091e7858c029a4773ec5108d9627a92fc9729d447859a9da71c29e9ab0c8f"),
                    ("runtime/contracts.py", "0db52d2f1036cf7d558628e1e41f6736c710c4b751a74d3cd17b2a8516c8e0d3"),
                    ("runtime/coordinator.py", "e4ea4e3a1c70978a2d625b42300fe4c48c324042559f0289a2d097b0ddf962ae"),
                    ("schemas/author-control-baseline.schema.json", "7c01d4aae910b470bf143617654dae7c85a092fd24a9f8355f8f7f77c6517661"),
                    ("schemas/canonical-common.schema.json", "ebda26bb43b66370a436767e8a88a6b32ce487c9da9d2b6a4823e93210646a09"),
                    ("schemas/common-defs.schema.json", "79f88f24f3de2ad76383acd459b907abb888eaf336defb4a36c12dcb6f5fddb4"),
                    ("schemas/environment-system.schema.json", "49247f3d132b8f13c39e7a61d40cc95206f86b087e41d935feffde7e25ff767e"),
                    ("schemas/event-timeline.schema.json", "4c0074e9e19eb57a717d03527f7dcd23e36185e632cb6e5966b58c19b8cae8b8"),
                    ("schemas/input-gate.schema.json", "d57ff990e16ae094d51467c3edee66ceff68e5a2dc87ccb90f46eae77267f0d5"),
                    ("schemas/package-manifest.schema.json", "6c808fd9ea6d892eeb0a588b89f4c681740968d3e597a6039f89cc8bd387350e"),
                    ("schemas/stage-completion.schema.json", "f9f50dd3fe8f442420a245f24a4ffef9529837f7f8fa7d1c894f179a45e8f217"),
                    ("schemas/storyline-architecture.schema.json", "a56c5bc748320ea80c62ccf93008eac782aaf3e816285c3680d501e3d8d1fc0a"),
                    ("schemas/world-model.schema.json", "b1b9a9e82d72e9c02fc3974ee5d1d44ac3ae100e26b80830dfdded7a7703eaa6"),
                    ("skill/SKILL.md", "4c40ae1516095042a877621409a95250146b2c40f37d15ccd02212995c5e66a2"),
                    ("skill/contract_22.py", "3b35c4c638596c541315c69bc387d389732f54c4aacb51e982230e7ddd9b829b"),
                    ("skill/contract_23.py", "b5e48027c8cb86e16cbdfb2a6f903a015dde5d38b6958ee96acdd2cf9f719995"),
                    ("skill/openai.yaml", "9c2aa1b0be9e5c48cce109974a03e29f689b66102b161c23f68defc6ffba0eee"),
                    ("skill/run_v2.py", "21c94ef28a13a5273772dd1bf48ffdb5bd9aa852504960d478180663d1d9c45f"),
                    ("skill/runtime-contract.md", "f51992278650876b36d28eb7de0b3874563748c75b90c3ec2733874442c55ba3"),
                    ("upstream/E1-run_v2.py", "bff7f4c6884aaa5d4c1f74c9968ffff03bdf636da6fecaabd53482e8e005bfcd"),
                    ("upstream/E1-runtime-contract.md", "d94849190d74a687fc167b5dbcbd3ab1bf3fe04cb17d10355b25563ef88fa9b2"),
                    ("upstream/S1-run_v2.py", "9894a35e664a142e65ac440e8c37a6cf81ce46d1a78fdb55c1c77c6c8f4e4151"),
                    ("upstream/S1-runtime-contract.md", "ff936f26a794aab3f11bc85e10b4f6c3d85be4f026cbdb7ad4925c591ed6f478"),
                    ("upstream/W1-run_v2.py", "f36b712eb8617745acf60487281cb2faa7566162f71e8cb788308cec641619f4"),
                    ("upstream/W1-runtime-contract.md", "59ca6f17e4c3dda4996a996962e47ee5420a3dbf8beb13da676fca810e9d4ac2"),
                }
            )
        }
    )
}
_TRUSTED_LEGACY_PACKAGE_IDENTITIES = {
    "2.0": frozenset(
        {
            (
                "fe98a8c4a68672fa103d02504b2da2a0bef1562246d584fa0da9e3471030f427",
                "7a411fc81c7c801c811d74c8e0e88eee77453be568030a2c61acfdd7b9eadc87",
                "176334765ace736820882539786f80a593f652abd21ab36c22c00147aa3ba171",
            )
        }
    ),
    "2.1": frozenset(),
    "2.2": frozenset(),
    "2.3": frozenset(),
    "2.4": frozenset(),
}


class T1Error(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(f"{code}: {message}")


@dataclass(frozen=True)
class T1RunReceipt:
    package_root: Path
    model: dict[str, Any]
    manifest: dict[str, Any]
    completion: Any
    transition: Any


def _fail(code: str, message: str) -> None:
    raise T1Error(code, message)


def _validate_authority_disjoint(partition: Mapping[str, Any]) -> None:
    names = (
        "author_locked",
        "autonomous_owned",
        "downstream_freedom",
        "author_open",
    )
    values = {name: set(partition[name]) for name in names}
    for index, left in enumerate(names):
        for right in names[index + 1 :]:
            overlap = sorted(values[left] & values[right])
            if overlap:
                _fail(
                    "T1_AUTHORITY_PARTITION_OVERLAP",
                    f"{left}/{right}: {overlap}",
                )


def _read(path: Path, code: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        _fail(code, f"{path}: {error}")
    if not isinstance(value, dict):
        _fail(code, f"{path} root must be an object")
    return value


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(rt.canonical_json(value), encoding="utf-8", newline="")


def _is_current_model(model: Mapping[str, Any]) -> bool:
    version = model.get("schema_version")
    if version == CURRENT_MODEL_SCHEMA_VERSION:
        return True
    if version in LEGACY_MODEL_SCHEMA_VERSIONS:
        return False
    _fail("T1_MODEL_SCHEMA_VERSION_UNSUPPORTED", str(version))


def _require_generation_schema(model: Mapping[str, Any]) -> None:
    if model.get("schema_version") != CURRENT_MODEL_SCHEMA_VERSION:
        _fail(
            "T1_LEGACY_GENERATION_FORBIDDEN",
            "T1 schemas 2.0/2.1/2.2/2.3/2.4 are read-only; only exact trusted ready package identities replay",
        )


def _validate_legacy_package_provenance(
    model: Mapping[str, Any],
    catalog: Mapping[str, Mapping[str, str]],
) -> None:
    version = model.get("schema_version")
    runtime_ref = catalog.get("skill/run_v2.py")
    schema_ref = catalog.get("schemas/event-timeline.schema.json")
    pair = (
        runtime_ref.get("sha256") if isinstance(runtime_ref, Mapping) else None,
        schema_ref.get("sha256") if isinstance(schema_ref, Mapping) else None,
    )
    if pair not in _TRUSTED_LEGACY_IMPLEMENTATION_PAIRS.get(
        version, frozenset()
    ):
        _fail("T1_LEGACY_PROVENANCE_UNTRUSTED", f"{version}: {pair}")
    trusted_binding_sets = _TRUSTED_LEGACY_IMPLEMENTATION_BINDING_SETS.get(
        version
    )
    if trusted_binding_sets is not None:
        observed = frozenset(
            (
                identity,
                reference.get("sha256")
                if isinstance(reference, Mapping)
                else None,
            )
            for identity, reference in catalog.items()
        )
        if observed not in trusted_binding_sets:
            _fail(
                "T1_LEGACY_PROVENANCE_UNTRUSTED",
                f"{version}: full implementation binding set",
            )


def _validate_trusted_legacy_model_schema(
    root: Path,
    model: Mapping[str, Any],
    catalog: Mapping[str, Mapping[str, str]],
) -> None:
    _validate_legacy_package_provenance(model, catalog)
    identity = (
        rt.sha256_file(root / "package-manifest.json"),
        rt.sha256_file(root / "stage-completion.json"),
        rt.sha256_file(root / "event-timeline.json"),
    )
    if identity not in _TRUSTED_LEGACY_PACKAGE_IDENTITIES.get(
        model.get("schema_version"), frozenset()
    ):
        _fail(
            "T1_LEGACY_PACKAGE_IDENTITY_UNTRUSTED",
            f"{model.get('schema_version')}: {identity}",
        )
    for identity in ("skill/run_v2.py", "schemas/event-timeline.schema.json"):
        reference = catalog.get(identity)
        if not isinstance(reference, Mapping):
            _fail("T1_LEGACY_PROVENANCE_UNTRUSTED", identity)
        try:
            rt.verify_artifact_reference(reference, root=root)
        except Exception as error:
            _fail("T1_LEGACY_PROVENANCE_UNTRUSTED", str(error))
    try:
        legacy_runtime = rt.ContractRuntime(
            root / "implementation" / "schemas",
            expected_schema_count=None,
        )
        legacy_runtime.validate(model, "event-timeline.schema.json")
    except Exception as error:
        _fail("T1_LEGACY_MODEL_SCHEMA_INVALID", str(error))


def _validate_legacy_upstream_snapshot(
    root: Path,
    *,
    stage: str,
    canonical_name: str,
    runtime: Any,
) -> None:
    manifest = _read(root / "package-manifest.json", f"T1_{stage}_INVALID")
    completion = _read(root / "stage-completion.json", f"T1_{stage}_INVALID")
    try:
        runtime.validate(manifest, "package-manifest.schema.json")
        rt.verify_manifest_integrity(manifest, root=root)
        runtime.validate(completion, "stage-completion.schema.json")
    except Exception as error:
        _fail(f"T1_{stage}_INVALID", str(error))
    canonical = rt.artifact_reference(root / canonical_name, root=root)
    canonical_entries = [
        item
        for item in manifest.get("files", [])
        if isinstance(item, Mapping) and item.get("path") == canonical_name
    ]
    legacy_role = manifest.get("artifact_roles", {}).get("canonical")
    if (
        canonical_entries != [canonical]
        or (legacy_role is not None and legacy_role != canonical)
        or completion.get("stage") != stage
        or completion.get("status") != "ready"
        or completion.get("manifest", {}).get("sha256")
        != rt.sha256_file(root / "package-manifest.json")
    ):
        _fail(f"T1_{stage}_INVALID", "legacy upstream snapshot is unbound")


def _logical(prefix: str, name: str) -> str:
    value = PurePosixPath(prefix, name).as_posix() if prefix else name
    if value.startswith("/") or ".." in PurePosixPath(value).parts:
        _fail("T1_PATH_INVALID", value)
    return value


def _implementation_paths() -> dict[str, Path]:
    runtime_dir = _REPO / "harnesses" / "novel-conception-autonomous" / "runtime"
    values = {
        "skill/run_v2.py": _HERE,
        "skill/contract_22.py": _SKILL / "scripts" / "contract_22.py",
        "skill/contract_23.py": _SKILL / "scripts" / "contract_23.py",
        "skill/contract_24.py": _SKILL / "scripts" / "contract_24.py",
        "skill/contract_25.py": _SKILL / "scripts" / "contract_25.py",
        "skill/SKILL.md": _SKILL / "SKILL.md",
        "skill/runtime-contract.md": _SKILL / "references" / "runtime-contract.md",
        "skill/openai.yaml": _SKILL / "agents" / "openai.yaml",
    }
    for name in (
        "canonical.py",
        "contracts.py",
        "coordinator.py",
        "stage_implementation_identity.py",
    ):
        values[f"runtime/{name}"] = runtime_dir / name
    for name in (
        "event-timeline.schema.json",
        "canonical-common.schema.json",
        "common-defs.schema.json",
        "input-gate.schema.json",
        "package-manifest.schema.json",
        "stage-completion.schema.json",
    ):
        values[f"schemas/{name}"] = _SCHEMAS / name
    return values


def _implementation_bindings() -> list[dict[str, str]]:
    return [
        {"identity": identity, "sha256": rt.sha256_file(path)}
        for identity, path in sorted(_implementation_paths().items())
    ]


def _stage_reference(root: Path, stage: str) -> dict[str, str]:
    path = root / "stage-completion.json"
    _read(path, f"T1_{stage}_INVALID")
    return {
        "stage": stage,
        "path": f"{stage}/stage-completion.json",
        "sha256": rt.sha256_file(path),
    }


def _sealed_upstream_reference(
    package_root: Path,
    sealed_reference: Mapping[str, Any],
    *,
    stage: str,
    run_id: str,
    previous_stage_completions: Sequence[Mapping[str, Any]],
    runtime: Any,
) -> dict[str, str]:
    """Prove that a gate-selected completion belongs to ``package_root``.

    Rebuilt upstream stages may live below immutable attempt workspaces, so the
    coordinator gate owns the logical completion path.  The physical package
    directory need not be named after the stage.  Its completion body and raw
    hash must nevertheless match the sealed reference, and its logical
    manifest/validation paths must be canonical siblings whose hashes bind the
    actual package root.
    """

    code = f"T1_{stage}_INVALID"
    completion_path = package_root / "stage-completion.json"
    completion = _read(completion_path, code)
    reference = copy.deepcopy(dict(sealed_reference))
    try:
        runtime.validate(completion, "stage-completion.schema.json")
    except Exception as error:
        _fail(code, str(error))
    if set(reference) != {"stage", "path", "sha256"}:
        _fail(code, f"sealed {stage} reference has an invalid shape")
    path = reference.get("path")
    digest = reference.get("sha256")
    if (
        reference.get("stage") != stage
        or not isinstance(path, str)
        or not isinstance(digest, str)
        or _HEX64.fullmatch(digest) is None
    ):
        _fail(code, f"sealed {stage} reference identity is invalid")
    logical_path = PurePosixPath(path)
    if (
        "\\" in path
        or logical_path.is_absolute()
        or logical_path.as_posix() != path
        or any(part in {"", ".", ".."} for part in logical_path.parts)
        or logical_path.name != "stage-completion.json"
        or len(logical_path.parts) < 2
    ):
        _fail(code, f"sealed {stage} completion path is not canonical")
    if (
        rt.sha256_file(completion_path) != digest
        or rt.canonical_sha256(completion) != digest
    ):
        _fail(code, f"sealed {stage} completion body or hash differs")
    if (
        completion.get("stage") != stage
        or completion.get("status") != "ready"
        or completion.get("run_id") != run_id
        or completion.get("previous_stage_completions")
        != list(previous_stage_completions)
    ):
        _fail(code, f"sealed completion is not this run's ready {stage}")
    logical_root = logical_path.parent
    if (
        completion.get("manifest")
        != {
            "path": (logical_root / "package-manifest.json").as_posix(),
            "sha256": rt.sha256_file(package_root / "package-manifest.json"),
        }
        or completion.get("validation")
        != {
            "path": (logical_root / "validation.json").as_posix(),
            "sha256": rt.sha256_file(package_root / "validation.json"),
        }
    ):
        _fail(
            code,
            f"sealed {stage} path is foreign to the completion's package lineage",
        )
    return reference


def _require_embedded_completion(
    path: Path, expected: Mapping[str, Any], *, code: str
) -> None:
    if (
        not path.is_file()
        or rt.sha256_file(path) != expected["sha256"]
        or rt.canonical_sha256(_read(path, code)) != expected["sha256"]
    ):
        _fail(code, f"{path} does not bind the gate-selected completion")


def _source_artifacts(
    b0_root: Path, s1_root: Path, w1_root: Path, e1_root: Path
) -> list[dict[str, str]]:
    selected = {
        "B0": (
            b0_root,
            (
                "author-control-baseline.json",
                "package-manifest.json",
                "stage-completion.json",
            ),
        ),
        "S1": (
            s1_root,
            (
                "storyline-architecture.json",
                "package-manifest.json",
                "stage-completion.json",
            ),
        ),
        "W1": (
            w1_root,
            (
                "world-model.json",
                "package-manifest.json",
                "stage-completion.json",
            ),
        ),
        "E1": (
            e1_root,
            (
                "environment-system.json",
                "package-manifest.json",
                "stage-completion.json",
            ),
        ),
    }
    return [
        {
            "path": f"sources/{stage}/{name}",
            "sha256": rt.sha256_file(root / name),
        }
        for stage, (root, names) in selected.items()
        for name in names
    ]


def _upstream_package_bindings(
    b0_root: Path, s1_root: Path, w1_root: Path, e1_root: Path
) -> list[dict[str, Any]]:
    roots = {"B0": b0_root, "S1": s1_root, "W1": w1_root, "E1": e1_root}
    return [
        {
            "stage": stage,
            "manifest": {
                "path": f"sources/{stage}/package-manifest.json",
                "sha256": rt.sha256_file(root / "package-manifest.json"),
            },
            "completion": {
                "path": f"sources/{stage}/stage-completion.json",
                "sha256": rt.sha256_file(root / "stage-completion.json"),
            },
        }
        for stage, root in roots.items()
    ]


def _e1_semantic_review_bindings(e1_root: Path) -> list[dict[str, Any]]:
    """Bind the exact review artifacts sealed by E1 P3 and P4 evidence."""

    phase_contract = (
        (
            "03-zones-and-topology.json",
            "e1-authority-capability-semantics-v1",
            "authority-capability-semantics",
        ),
        (
            "04-storyline-hosting-test.json",
            "e1-transition-support-semantics-v1",
            "transition-support-semantics",
        ),
    )
    found: list[dict[str, Any]] = []
    for evidence_name, protocol, review_kind in phase_contract:
        evidence_path = e1_root / "generation-evidence" / evidence_name
        evidence = _read(evidence_path, "T1_E1_REVIEW_BINDING_INVALID")
        manifest_ref = evidence.get("semantic_review")
        if not isinstance(manifest_ref, Mapping):
            _fail("T1_E1_REVIEW_BINDING_INVALID", protocol)
        manifest_logical = PurePosixPath(str(manifest_ref.get("path", "")))
        if manifest_logical.is_absolute() or ".." in manifest_logical.parts:
            _fail("T1_E1_REVIEW_BINDING_INVALID", protocol)
        manifest_path = e1_root / Path(*manifest_logical.parts)
        if not manifest_path.is_file() or rt.sha256_file(manifest_path) != manifest_ref.get("sha256"):
            _fail("T1_E1_REVIEW_BINDING_INVALID", protocol)
        manifest = _read(manifest_path, "T1_E1_REVIEW_BINDING_INVALID")
        artifacts = manifest.get("artifacts")
        if (
            manifest.get("review_protocol") != protocol
            or not isinstance(artifacts, list)
            or len(artifacts) != 5
        ):
            _fail("T1_E1_REVIEW_BINDING_INVALID", protocol)
        artifact_by_name: dict[str, tuple[Mapping[str, Any], Path]] = {}
        for artifact in artifacts:
            if not isinstance(artifact, Mapping):
                _fail("T1_E1_REVIEW_BINDING_INVALID", protocol)
            logical = PurePosixPath(str(artifact.get("path", "")))
            if logical.is_absolute() or ".." in logical.parts:
                _fail("T1_E1_REVIEW_BINDING_INVALID", protocol)
            path = e1_root / Path(*logical.parts)
            if not path.is_file() or rt.sha256_file(path) != artifact.get("sha256"):
                _fail("T1_E1_REVIEW_BINDING_INVALID", protocol)
            artifact_by_name[logical.name] = (artifact, path)
        if set(artifact_by_name) != {
            "candidate.json",
            "request.json",
            "review-task-output.json",
            "review.json",
            "validation.json",
        }:
            _fail("T1_E1_REVIEW_BINDING_INVALID", protocol)
        candidate_ref, candidate_path = artifact_by_name["candidate.json"]
        request_ref, request_path = artifact_by_name["request.json"]
        task_output_ref, task_output_path = artifact_by_name["review-task-output.json"]
        review_ref, review_path = artifact_by_name["review.json"]
        validation_ref, validation_path = artifact_by_name["validation.json"]
        request = _read(request_path, "T1_E1_REVIEW_BINDING_INVALID")
        task_output = _read(task_output_path, "T1_E1_REVIEW_BINDING_INVALID")
        review = _read(review_path, "T1_E1_REVIEW_BINDING_INVALID")
        validation = _read(validation_path, "T1_E1_REVIEW_BINDING_INVALID")
        candidate = _read(candidate_path, "T1_E1_REVIEW_BINDING_INVALID")
        receipt = review.get("reviewer_task_receipt")
        expected_verdict_payload = {"claim_verdicts": review.get("claim_verdicts")}
        if review_kind == "transition-support-semantics":
            expected_verdict_payload["record_verdicts"] = review.get("record_verdicts")
        expected_task_output = {
            "schema_version": "1.0",
            "stage": "E1",
            "review_kind": review_kind,
            "task_id": receipt.get("task_id") if isinstance(receipt, Mapping) else None,
            "producer_thread_id": request.get("producer_thread_id"),
            "reviewer_thread_id": review.get("reviewer_thread_id"),
            "candidate_sha256": request.get("candidate_sha256"),
            "request": request_ref,
            "verdict_payload": expected_verdict_payload,
        }
        expected_validation = {
            "schema_version": "1.0",
            "stage": "E1",
            "review_kind": review_kind,
            "review_protocol": protocol,
            "candidate_sha256": request.get("candidate_sha256"),
            "verdict": "ready",
            "candidate": candidate_ref,
            "request": request_ref,
            "review": review_ref,
            "review_task_output": task_output_ref,
        }
        expected_manifest = {
            "schema_version": "1.0",
            "stage": "E1",
            "review_kind": review_kind,
            "review_protocol": protocol,
            "candidate_sha256": request.get("candidate_sha256"),
            "artifacts": [
                candidate_ref,
                request_ref,
                task_output_ref,
                review_ref,
                validation_ref,
            ],
        }
        if (
            manifest != expected_manifest
            or request.get("review_kind") != review_kind
            or request.get("review_protocol") != protocol
            or request.get("candidate_sha256") != review.get("candidate_sha256")
            or request.get("candidate_sha256") != manifest.get("candidate_sha256")
            or request.get("candidate_sha256") != rt.canonical_sha256(candidate)
            or request.get("session_id") != evidence.get("session_id")
            or review.get("review_kind") != review_kind
            or review.get("review_protocol") != protocol
            or review.get("verdict") != "pass"
            or review.get("request") != request_ref
            or not isinstance(receipt, Mapping)
            or set(receipt) != {
                "task_id",
                "producer_thread_id",
                "reviewer_thread_id",
                "output_artifact",
                "output_sha256",
            }
            or not isinstance(receipt.get("task_id"), str)
            or not receipt.get("task_id", "").strip()
            or not isinstance(review.get("reviewer_thread_id"), str)
            or not review.get("reviewer_thread_id", "").strip()
            or review.get("reviewer_thread_id") == request.get("producer_thread_id")
            or receipt.get("producer_thread_id") != request.get("producer_thread_id")
            or receipt.get("reviewer_thread_id") != review.get("reviewer_thread_id")
            or receipt.get("output_artifact") != task_output_ref
            or receipt.get("output_sha256") != rt.canonical_sha256(task_output)
            or task_output != expected_task_output
            or validation != expected_validation
        ):
            _fail("T1_E1_REVIEW_BINDING_INVALID", protocol)
        found.append(
            {
                "review_protocol": protocol,
                "phase_evidence": {
                    "path": f"sources/E1/generation-evidence/{evidence_name}",
                    "sha256": rt.sha256_file(evidence_path),
                },
                "manifest": {
                    "path": f"sources/E1/{manifest_logical.as_posix()}",
                    "sha256": manifest_ref["sha256"],
                },
                "candidate": {"path": f"sources/E1/{candidate_ref['path']}", "sha256": candidate_ref["sha256"]},
                "request": {"path": f"sources/E1/{request_ref['path']}", "sha256": request_ref["sha256"]},
                "review_task_output": {
                    "path": f"sources/E1/{task_output_ref['path']}",
                    "sha256": task_output_ref["sha256"],
                },
                "review": {"path": f"sources/E1/{review_ref['path']}", "sha256": review_ref["sha256"]},
                "validation": {"path": f"sources/E1/{validation_ref['path']}", "sha256": validation_ref["sha256"]},
                "candidate_sha256": request["candidate_sha256"],
            }
        )
    return found


def _controls(
    b0_root: Path, baseline: Mapping[str, Any]
) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    for entry in baseline["design_artifacts"]:
        source = rt.verify_artifact_reference(entry["artifact"], root=b0_root)
        for value in rt.extract_controls(source, entry["domain"]):
            found.append({**value, "domain": entry["domain"]})
    found.sort(key=lambda item: item["id"])
    return found


def _object_bindings(
    values: Sequence[Mapping[str, Any]], *, extra: str | None = None
) -> list[dict[str, str]]:
    return [
        {
            "id": item["id"],
            **({extra: str(item[extra])} if extra is not None else {}),
            "value_sha256": rt.canonical_sha256(item),
        }
        for item in values
    ]


def _control_bindings(
    controls: Sequence[Mapping[str, Any]],
) -> list[dict[str, str]]:
    return [
        {
            "id": item["id"],
            "domain": item["domain"],
            "heading": item["heading"],
            "value_sha256": rt.canonical_sha256(item["value"]),
        }
        for item in controls
    ]


def _session_id(
    thread_id: str,
    gate: Mapping[str, str],
    b0: Mapping[str, str],
    s1: Mapping[str, str],
    w1: Mapping[str, str],
    e1: Mapping[str, str],
) -> str:
    return "T1-" + rt.canonical_sha256([thread_id, gate, b0, s1, w1, e1])[:20]


def _session_context(
    *,
    baseline_package: str | Path,
    storyline_package: str | Path,
    world_package: str | Path,
    environment_package: str | Path,
    input_gate: Any,
    runtime: Any,
    full_validation: bool = True,
) -> tuple[
    Path,
    Path,
    Path,
    Path,
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    list[dict[str, Any]],
    dict[str, str],
    dict[str, str],
    dict[str, str],
    dict[str, str],
]:
    b0_root = Path(baseline_package).resolve()
    s1_root = Path(storyline_package).resolve()
    w1_root = Path(world_package).resolve()
    e1_root = Path(environment_package).resolve()
    if full_validation:
        try:
            rt.validate_baseline_package(b0_root, runtime=runtime)
        except Exception as error:
            _fail("T1_B0_INVALID", str(error))
        try:
            s1_runtime.validate_s1_package(s1_root, runtime=runtime)
        except Exception as error:
            _fail("T1_S1_INVALID", str(error))
        try:
            w1_runtime.validate_w1_package(w1_root, runtime=runtime)
        except Exception as error:
            _fail("T1_W1_INVALID", str(error))
        try:
            e1_runtime.validate_e1_package(e1_root, runtime=runtime)
        except Exception as error:
            _fail("T1_E1_INVALID", str(error))
    baseline = _read(
        b0_root / "author-control-baseline.json", "T1_B0_INVALID"
    )
    storyline = _read(
        s1_root / "storyline-architecture.json", "T1_S1_INVALID"
    )
    world = _read(w1_root / "world-model.json", "T1_W1_INVALID")
    environment = _read(
        e1_root / "environment-system.json", "T1_E1_INVALID"
    )
    if environment.get("schema_version") != e1_runtime.CURRENT_MODEL_SCHEMA_VERSION:
        _fail(
            "T1_E1_LEGACY_INPUT_FORBIDDEN",
            "new T1 generation requires the current E1 production contract",
        )
    if {
        baseline["run_id"],
        storyline["run_id"],
        world["run_id"],
        environment["run_id"],
    } != {
        baseline["run_id"]
    }:
        _fail("T1_RUN_ID_MISMATCH", "B0/S1/W1/E1 runs differ")
    try:
        runtime.validate(input_gate.data, "input-gate.schema.json")
    except Exception as error:
        _fail("T1_GATE_INVALID", str(error))
    if rt.canonical_sha256(input_gate.data) != input_gate.reference.get("sha256"):
        _fail("T1_GATE_INVALID", "gate reference does not bind its body")
    sealed_b0 = input_gate.data.get("baseline_completion")
    sealed_upstreams = input_gate.data.get("upstream_completions")
    if (
        not isinstance(sealed_b0, Mapping)
        or not isinstance(sealed_upstreams, list)
        or len(sealed_upstreams) != 3
        or any(not isinstance(item, Mapping) for item in sealed_upstreams)
    ):
        _fail(
            "T1_GATE_INVALID",
            "gate does not select exactly B0, S1, W1, and E1",
        )
    b0_ref = _sealed_upstream_reference(
        b0_root,
        sealed_b0,
        stage="B0",
        run_id=baseline["run_id"],
        previous_stage_completions=[],
        runtime=runtime,
    )
    s1_ref = _sealed_upstream_reference(
        s1_root,
        sealed_upstreams[0],
        stage="S1",
        run_id=baseline["run_id"],
        previous_stage_completions=[],
        runtime=runtime,
    )
    w1_ref = _sealed_upstream_reference(
        w1_root,
        sealed_upstreams[1],
        stage="W1",
        run_id=baseline["run_id"],
        previous_stage_completions=[s1_ref],
        runtime=runtime,
    )
    e1_ref = _sealed_upstream_reference(
        e1_root,
        sealed_upstreams[2],
        stage="E1",
        run_id=baseline["run_id"],
        previous_stage_completions=[s1_ref, w1_ref],
        runtime=runtime,
    )
    try:
        for path, expected in (
            (s1_root / "sources" / "B0" / "stage-completion.json", b0_ref),
            (w1_root / "sources" / "B0" / "stage-completion.json", b0_ref),
            (w1_root / "sources" / "S1" / "stage-completion.json", s1_ref),
            (e1_root / "sources" / "B0" / "stage-completion.json", b0_ref),
            (e1_root / "sources" / "S1" / "stage-completion.json", s1_ref),
            (e1_root / "sources" / "W1" / "stage-completion.json", w1_ref),
        ):
            _require_embedded_completion(
                path, expected, code="T1_UPSTREAM_LINEAGE_MISMATCH"
            )
    except T1Error:
        raise
    except (OSError, KeyError) as error:
        _fail("T1_UPSTREAM_LINEAGE_MISMATCH", str(error))
    if (
        input_gate.data.get("target_stage") != "T1"
        or input_gate.data.get("run_id") != baseline["run_id"]
        or input_gate.data.get("baseline_completion") != b0_ref
        or input_gate.data.get("upstream_completions")
        != [s1_ref, w1_ref, e1_ref]
    ):
        _fail("T1_GATE_INVALID", "gate is not the exact T1/B0/S1/W1/E1 gate")
    return (
        b0_root,
        s1_root,
        w1_root,
        e1_root,
        baseline,
        storyline,
        world,
        environment,
        _controls(b0_root, baseline),
        b0_ref,
        s1_ref,
        w1_ref,
        e1_ref,
    )


def _nested_forbidden(value: Any) -> str | None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if key in _FORBIDDEN_NESTED_KEYS:
                return key
            found = _nested_forbidden(child)
            if found is not None:
                return found
    elif isinstance(value, list):
        for child in value:
            found = _nested_forbidden(child)
            if found is not None:
                return found
    return None


def _boundary_check(model: Mapping[str, Any]) -> None:
    forbidden = sorted(set(model) & _FORBIDDEN_MODEL_KEYS)
    if forbidden:
        _fail("T1_BOUNDARY_VIOLATION", f"forbidden top-level fields: {forbidden}")
    nested = _nested_forbidden(model)
    if nested is not None:
        _fail("T1_BOUNDARY_VIOLATION", f"forbidden event/prose field: {nested}")


def _unique_by_id(values: Sequence[Mapping[str, Any]], code: str) -> dict[str, Mapping[str, Any]]:
    indexed = {item["id"]: item for item in values}
    if len(indexed) != len(values):
        _fail(code, "IDs repeat")
    return indexed


def _world_time(value: str, event_id: str) -> int:
    match = _WORLD_TIME_TOKEN.fullmatch(value)
    if match is None:
        _fail("T1_WORLD_TIME_INVALID", event_id)
    return int(match.group(1))


def _responsibilities(event: Mapping[str, Any]) -> list[str]:
    roles = _RESPONSIBILITY_TOKEN.findall(event["responsibility"])
    if not roles or len(roles) != len(set(roles)):
        _fail("T1_EVENT_RESPONSIBILITY_INVALID", event["id"])
    indices = [_RESPONSIBILITY_ORDER.index(role) for role in roles]
    if indices != sorted(indices) or any(
        right - left > 1 for left, right in zip(indices, indices[1:])
    ):
        _fail("T1_EVENT_RESPONSIBILITY_INVALID", event["id"])
    return roles


def _timing_relation(item: Mapping[str, Any]) -> str:
    values = _TIMING_TOKEN.findall(item["constraint"])
    if len(values) != 1:
        _fail("T1_TIMING_CONSTRAINT_INVALID", item["id"])
    return values[0]


def _ledger_kind(item: Mapping[str, Any]) -> str:
    values = _LEDGER_KIND_TOKEN.findall(item["consequence"])
    if len(values) != 1:
        _fail("T1_LEDGER_KIND_INVALID", item["id"])
    return values[0]


def _non_placeholder(value: str) -> bool:
    return value.strip().lower() not in {
        "none",
        "n/a",
        "na",
        "unknown",
        "tbd",
        "placeholder",
        "无",
        "未知",
        "待定",
    }


def _event_line_for_requirement(
    requirement: Mapping[str, Any], lines: Mapping[str, Mapping[str, Any]]
) -> str:
    found = [source for source in requirement["source_ids"] if source in lines]
    if len(found) != 1:
        _fail("T1_EVENT_REQUIREMENT_DANGLING", requirement["id"])
    return found[0]


def _is_acyclic(events: set[str], pairs: set[tuple[str, str]]) -> bool:
    incoming = {event_id: 0 for event_id in events}
    adjacency = {event_id: set() for event_id in events}
    for left, right in pairs:
        if right not in adjacency[left]:
            adjacency[left].add(right)
            incoming[right] += 1
    queue = [item for item, count in incoming.items() if count == 0]
    visited = 0
    while queue:
        current = queue.pop()
        visited += 1
        for target in adjacency[current]:
            incoming[target] -= 1
            if incoming[target] == 0:
                queue.append(target)
    return visited == len(events)


def _causally_reaches(
    source_id: str,
    target_id: str,
    edge_pairs: set[tuple[str, str]],
) -> bool:
    """Return whether source reaches target through one or more causal edges."""

    frontier = [source_id]
    visited = {source_id}
    while frontier:
        current = frontier.pop()
        for left, right in edge_pairs:
            if left != current or right in visited:
                continue
            if right == target_id:
                return True
            visited.add(right)
            frontier.append(right)
    return False


def _topological_order_index(
    events: set[str], pairs: set[tuple[str, str]]
) -> dict[str, int]:
    """Return a deterministic DAG order used only to break world-time ties."""

    incoming = {event_id: 0 for event_id in events}
    adjacency = {event_id: set() for event_id in events}
    for left, right in pairs:
        if right not in adjacency[left]:
            adjacency[left].add(right)
            incoming[right] += 1
    ready = sorted(
        event_id for event_id, count in incoming.items() if count == 0
    )
    order: dict[str, int] = {}
    while ready:
        current = ready.pop(0)
        order[current] = len(order)
        for target in sorted(adjacency[current]):
            incoming[target] -= 1
            if incoming[target] == 0:
                ready.append(target)
                ready.sort()
    if len(order) != len(events):
        _fail("T1_CAUSAL_CYCLE", "event graph is cyclic")
    return order


def _validate_proposition_contract(
    model: Mapping[str, Any],
    storyline: Mapping[str, Any],
    events: Mapping[str, Mapping[str, Any]],
    event_times: Mapping[str, int],
    edge_pairs: set[tuple[str, str]],
    state_anchor_by_line_index: Mapping[tuple[str, int], Mapping[str, Any]],
) -> tuple[dict[str, Mapping[str, Any]], dict[str, Mapping[str, Any]]]:
    """Recompute event truth/disclosure semantics and every S1 obligation."""

    if "story_obligation_register" not in storyline:
        _fail(
            "T1_UPSTREAM_OBLIGATION_REGISTER_MISSING",
            "S1 must provide story_obligation_register",
        )
    obligation_plans = {
        item["obligation_id"]: item
        for item in model.get("obligation_event_plan", [])
    }
    obligations = _unique_by_id(
        storyline["story_obligation_register"],
        "T1_STORY_OBLIGATION_DUPLICATE",
    )
    propositions = _unique_by_id(
        model["proposition_registry"], "T1_PROPOSITION_DUPLICATE"
    )
    if len({item["statement"] for item in propositions.values()}) != len(
        propositions
    ):
        _fail(
            "T1_PROPOSITION_STATEMENT_DUPLICATE",
            "one truth claim cannot be cloned under multiple proposition IDs",
        )
    realizations = _unique_by_id(
        model["obligation_realizations"],
        "T1_OBLIGATION_REALIZATION_DUPLICATE",
    )
    by_obligation: dict[str, Mapping[str, Any]] = {}
    for realization in realizations.values():
        obligation_id = realization["obligation_id"]
        if obligation_id not in obligations or obligation_id in by_obligation:
            _fail("T1_OBLIGATION_REALIZATION_MISMATCH", obligation_id)
        by_obligation[obligation_id] = realization
    if set(by_obligation) != set(obligations):
        _fail(
            "T1_OBLIGATION_REALIZATION_MISMATCH",
            "every S1 story obligation must be realized exactly once",
        )

    required_by_event: dict[str, set[str]] = {}
    produced_by_event: dict[str, set[str]] = {}
    disclosed_by_event: dict[str, set[str]] = {}
    producers: dict[str, set[str]] = {item: set() for item in propositions}
    disclosures: dict[str, set[str]] = {item: set() for item in propositions}
    used: set[str] = set()
    for event_id, event in events.items():
        required = set(event["requires_proposition_ids"])
        produced = set(event["produces_proposition_ids"])
        disclosed = set(event["discloses_proposition_ids"])
        if not (required | produced | disclosed).issubset(propositions):
            _fail("T1_EVENT_PROPOSITION_DANGLING", event_id)
        required_by_event[event_id] = required
        produced_by_event[event_id] = produced
        disclosed_by_event[event_id] = disclosed
        used.update(required | produced | disclosed)
        for proposition_id in produced:
            producers[proposition_id].add(event_id)
        for proposition_id in disclosed:
            disclosures[proposition_id].add(event_id)

    for realization in realizations.values():
        realized = {
            *realization["antecedent_proposition_ids"],
            realization["consequent_proposition_id"],
        }
        if not realized.issubset(propositions):
            _fail(
                "T1_OBLIGATION_PROPOSITION_MISMATCH",
                realization["obligation_id"],
            )
        used.update(realized)

    if used != set(propositions):
        _fail(
            "T1_PROPOSITION_REGISTRY_MISMATCH",
            "every registered proposition must participate in an event",
        )
    for proposition_id, proposition in propositions.items():
        producer_ids = producers[proposition_id]
        if proposition["initially_true"]:
            if producer_ids:
                _fail("T1_PROPOSITION_ORIGIN_CONFLICT", proposition_id)
        elif not producer_ids:
            _fail("T1_PROPOSITION_PRODUCER_MISSING", proposition_id)
        if (
            proposition["terminality"] == "unique_terminal"
            and len(producer_ids) != 1
        ):
            _fail("T1_UNIQUE_TERMINAL_VIOLATION", proposition_id)
    unique_terminal_ids = {
        proposition_id
        for proposition_id, proposition in propositions.items()
        if proposition["terminality"] == "unique_terminal"
    }
    for sequence in model["storyline_event_sequences"]:
        final_event_id = sequence["event_ids"][-1]
        if not (
            produced_by_event[final_event_id] & unique_terminal_ids
        ):
            _fail(
                "T1_STORYLINE_TERMINAL_PROPOSITION_MISSING",
                sequence["storyline_id"],
            )

    for event_id, required in required_by_event.items():
        for proposition_id in required:
            proposition = propositions[proposition_id]
            if proposition["initially_true"]:
                continue
            if not any(
                source_id != event_id
                and event_times[source_id] <= event_times[event_id]
                and _causally_reaches(source_id, event_id, edge_pairs)
                for source_id in producers[proposition_id]
            ):
                _fail(
                    "T1_REQUIRED_PROPOSITION_UNREACHABLE",
                    f"{event_id} requires {proposition_id}",
                )
    for event_id, disclosed in disclosed_by_event.items():
        for proposition_id in disclosed:
            proposition = propositions[proposition_id]
            if proposition["initially_true"]:
                continue
            if not any(
                event_times[source_id] <= event_times[event_id]
                for source_id in producers[proposition_id]
            ):
                _fail(
                    "T1_DISCLOSURE_BEFORE_PRODUCTION",
                    f"{event_id} discloses {proposition_id}",
                )

    def anchor(value: Mapping[str, Any], obligation_id: str) -> Mapping[str, Any]:
        key = (value["storyline_id"], value["state_index"])
        observed = state_anchor_by_line_index.get(key)
        if observed is None or observed["state"] != value["state"]:
            _fail("T1_OBLIGATION_ANCHOR_MISMATCH", obligation_id)
        return observed

    for obligation_id, obligation in obligations.items():
        realization = by_obligation[obligation_id]
        obligation_plan = obligation_plans.get(obligation_id)
        if realization["kind"] != obligation["kind"]:
            _fail("T1_OBLIGATION_REALIZATION_MISMATCH", obligation_id)
        antecedent_anchors = [
            anchor(item, obligation_id)
            for item in obligation["antecedent_anchors"]
        ]
        consequent_anchor = anchor(
            obligation["consequent_anchor"], obligation_id
        )
        antecedent_props = realization["antecedent_proposition_ids"]
        consequent_prop = realization["consequent_proposition_id"]
        if (
            len(antecedent_props) != len(antecedent_anchors)
            or len(set(antecedent_props)) != len(antecedent_props)
            or consequent_prop not in propositions
            or not set(antecedent_props).issubset(propositions)
        ):
            _fail("T1_OBLIGATION_PROPOSITION_MISMATCH", obligation_id)
        kind = obligation["kind"]
        consequent_event = consequent_anchor["event_id"]
        if model.get("schema_version") == CURRENT_MODEL_SCHEMA_VERSION and kind in {
            "first_disclosure",
            "must_remain_unknown",
        }:
            if obligation_plan is None:
                _fail("T1_OBLIGATION_WITNESS_MISMATCH", obligation_id)
            consequent_event = obligation_plan["consequent_event_id"]
            anchor_value = obligation["consequent_anchor"]
            arrival_span = next(
                (
                    item["event_ids"]
                    for item in model["transition_event_cover"]
                    if item["storyline_id"] == anchor_value["storyline_id"]
                    and item["to_state_index"] == anchor_value["state_index"]
                ),
                [consequent_anchor["event_id"]]
                if anchor_value["state_index"] == 0
                else [],
            )
            if consequent_event not in arrival_span:
                _fail("T1_OBLIGATION_WITNESS_MISMATCH", obligation_id)
        expected_events = list(
            dict.fromkeys(
                [item["event_id"] for item in antecedent_anchors]
                + [consequent_event]
            )
        )
        if realization["event_ids"] != expected_events:
            _fail("T1_OBLIGATION_WITNESS_MISMATCH", obligation_id)
        for proposition_id in [*antecedent_props, consequent_prop]:
            if obligation_id not in propositions[proposition_id]["source_ids"]:
                _fail("T1_OBLIGATION_PROPOSITION_MISMATCH", obligation_id)

        if kind in {"first_disclosure", "must_remain_unknown"}:
            if consequent_prop != obligation["proposition_id"]:
                _fail("T1_OBLIGATION_PROPOSITION_MISMATCH", obligation_id)
            if propositions[consequent_prop]["audience"] != obligation["audience"]:
                _fail("T1_OBLIGATION_AUDIENCE_MISMATCH", obligation_id)
        elif obligation["proposition_id"] is not None:
            _fail("T1_OBLIGATION_PROPOSITION_MISMATCH", obligation_id)

        # Anchor propositions bind truth to the exact S1 state transition.
        if kind not in {"must_remain_unknown"}:
            for anchored, proposition_id in zip(
                antecedent_anchors, antecedent_props
            ):
                field = (
                    required_by_event
                    if anchored["side"] == "before"
                    else produced_by_event
                )
                if proposition_id not in field[anchored["event_id"]]:
                    _fail("T1_OBLIGATION_ANCHOR_PROPOSITION_MISMATCH", obligation_id)
        if kind not in {"first_disclosure", "must_remain_unknown"}:
            field = (
                required_by_event
                if consequent_anchor["side"] == "before"
                else produced_by_event
            )
            if consequent_prop not in field[consequent_anchor["event_id"]]:
                _fail("T1_OBLIGATION_ANCHOR_PROPOSITION_MISMATCH", obligation_id)

        antecedent_events = [item["event_id"] for item in antecedent_anchors]
        if kind in {"causes", "requires_all"}:
            if not set(antecedent_props).issubset(
                required_by_event[consequent_event]
            ):
                _fail("T1_REQUIRES_ALL_VIOLATION", obligation_id)
            for anchored, source_event in zip(
                antecedent_anchors, antecedent_events
            ):
                local_cause = (
                    source_event == consequent_event
                    and anchored["side"] == "before"
                    and consequent_anchor["side"] == "after"
                )
                if not local_cause and not _causally_reaches(
                    source_event, consequent_event, edge_pairs
                ):
                    _fail("T1_CAUSAL_OBLIGATION_UNREACHABLE", obligation_id)
        if kind == "strict_before" and not all(
            event_times[source_event] < event_times[consequent_event]
            for source_event in antecedent_events
        ):
            _fail("T1_STRICT_BEFORE_VIOLATION", obligation_id)
        if kind == "not_before" and not all(
            event_times[source_event] <= event_times[consequent_event]
            for source_event in antecedent_events
        ):
            _fail("T1_NOT_BEFORE_VIOLATION", obligation_id)
        if kind == "first_disclosure":
            if consequent_prop not in disclosed_by_event[consequent_event]:
                _fail("T1_FIRST_DISCLOSURE_VIOLATION", obligation_id)
            first_time = min(
                (event_times[item] for item in disclosures[consequent_prop]),
                default=None,
            )
            if first_time != event_times[consequent_event] or any(
                item != consequent_event
                and event_times[item] == first_time
                for item in disclosures[consequent_prop]
            ):
                _fail("T1_FIRST_DISCLOSURE_VIOLATION", obligation_id)
        if kind == "must_remain_unknown" and any(
            event_times[item] <= event_times[consequent_event]
            for item in disclosures[consequent_prop]
        ):
            _fail("T1_PREMATURE_DISCLOSURE", obligation_id)

    return propositions, realizations


def _state_anchors_for_line(
    line_id: str,
    required_states: Sequence[str],
    transition_ledgers: Sequence[Mapping[str, Any]],
    transition_spans: Sequence[Sequence[str]] | None = None,
) -> dict[tuple[str, int], dict[str, Any]]:
    """Map canonical state positions to exact transition-event sides."""

    if (
        len(required_states) < 2
        or len(transition_ledgers) != len(required_states) - 1
    ):
        _fail(
            "T1_STORYLINE_STATE_PROGRESSION_MISMATCH",
            line_id,
        )
    span_values = list(transition_spans or [
        ledger["trigger_ids"] for ledger in transition_ledgers
    ])
    if len(span_values) != len(transition_ledgers) or any(not item for item in span_values):
        _fail("T1_STORYLINE_STATE_PROGRESSION_MISMATCH", line_id)
    output = {
        (line_id, 0): {
            "event_id": span_values[0][0],
            "storyline_id": line_id,
            "state_index": 0,
            "state": required_states[0],
            "side": "before",
        }
    }
    for state_index, state in enumerate(required_states[1:], 1):
        output[(line_id, state_index)] = {
            "event_id": span_values[state_index - 1][-1],
            "storyline_id": line_id,
            "state_index": state_index,
            "state": state,
            "side": "after",
        }
    return output


def _validate_storyline_responsibility_progression(
    line_id: str,
    event_ids: Sequence[str],
    event_roles: Mapping[str, Sequence[str]],
) -> None:
    observed: list[str] = []
    responsibility_indices: list[int] = []
    for event_id in event_ids:
        for role in event_roles[event_id]:
            responsibility_indices.append(
                _RESPONSIBILITY_ORDER.index(role)
            )
            if role not in observed:
                observed.append(role)
    terminal_roles = set(event_roles[event_ids[-1]])
    if (
        observed != list(_RESPONSIBILITY_ORDER)
        or any(
            left > right
            for left, right in zip(
                responsibility_indices,
                responsibility_indices[1:],
            )
        )
        or not {"result", "aftermath"}.issubset(terminal_roles)
    ):
        _fail("T1_STORYLINE_CHAIN_INCOMPLETE", line_id)


def _validate_terminal_state_event(
    line_id: str,
    line_type: str,
    transition_ledgers: Sequence[Mapping[str, Any]],
    event_ids: Sequence[str],
    *,
    current_schema: bool = False,
    transition_spans: Sequence[Sequence[str]] | None = None,
    events: Mapping[str, Mapping[str, Any]] | None = None,
    connections: Mapping[str, Mapping[str, Any]] | None = None,
    connection_event_paths: Sequence[Mapping[str, Any]] = (),
    connection_path_readiness: Sequence[Mapping[str, Any]] = (),
    edge_pairs: set[tuple[str, str]] | None = None,
) -> None:
    """Close a line at its final transition, with one narrow SEND-tail exception.

    Historical schemas keep the original last-event rule.  In the current
    schema, a source line may retain post-terminal connection bridges only
    when E1 readiness and the exact source-anchor-to-target path already own
    them.  Such bridges transport a completed state; they cannot change it.
    """

    if line_type == "optional_melody":
        return
    if not transition_ledgers or not event_ids:
        _fail(
            "T1_STORYLINE_TERMINAL_STATE_EVENT_MISMATCH",
            line_id,
        )
    terminal_event_id = (
        transition_spans[-1][-1]
        if current_schema and transition_spans
        else transition_ledgers[-1]["trigger_ids"][0]
    )
    if terminal_event_id not in event_ids:
        _fail("T1_STORYLINE_TERMINAL_STATE_EVENT_MISMATCH", line_id)
    if len(event_ids) != len(set(event_ids)):
        _fail("T1_POST_TERMINAL_EVENT_DUPLICATE", line_id)
    terminal_index = event_ids.index(terminal_event_id)
    tail_ids = list(event_ids[terminal_index + 1 :])
    if not tail_ids:
        return
    if not current_schema:
        _fail("T1_STORYLINE_TERMINAL_STATE_EVENT_MISMATCH", line_id)
    if (
        not transition_spans
        or events is None
        or connections is None
        or edge_pairs is None
    ):
        _fail("T1_POST_TERMINAL_CONNECTION_PATH_INVALID", line_id)

    span_ids = [event_id for span in transition_spans for event_id in span]
    if (
        len(span_ids) != len(set(span_ids))
        or any(event_id not in event_ids for event_id in span_ids)
        or any(event_id in tail_ids for event_id in span_ids)
        or any(event_ids.index(event_id) > terminal_index for event_id in span_ids)
    ):
        _fail("T1_POST_TERMINAL_STATE_CHANGE", line_id)

    paths: dict[str, Mapping[str, Any]] = {}
    for path in connection_event_paths:
        connection_id = path["connection_id"]
        if connection_id in paths:
            _fail("T1_POST_TERMINAL_CONNECTION_PATH_INVALID", connection_id)
        paths[connection_id] = path
    readiness: dict[str, Mapping[str, Any]] = {}
    for record in connection_path_readiness:
        connection_id = record["connection_id"]
        if connection_id in readiness:
            _fail(
                "T1_POST_TERMINAL_CONNECTION_READINESS_MISMATCH",
                connection_id,
            )
        readiness[connection_id] = record

    terminal_state_index = len(transition_ledgers)
    expected_tail_ids: set[str] = set()
    bridge_owners: dict[str, str] = {}
    relevant_paths: list[tuple[Mapping[str, Any], list[str]]] = []
    for connection_id, path in paths.items():
        connection = connections.get(connection_id)
        if (
            connection is None
            or connection.get("relation") != "causal"
            or connection.get("from_storyline_id") != line_id
            or connection.get("from_state_index") != terminal_state_index
            or path.get("source_event_id") != terminal_event_id
        ):
            continue
        ready = readiness.get(connection_id)
        bridge_ids = list(path["bridge_event_ids"])
        predecessor_path = list(path["predecessor_path_event_ids"])
        if (
            path.get("relation") != "causal"
            or ready is None
            or ready.get("relation") != "causal"
            or len(bridge_ids) != len(set(bridge_ids))
            or predecessor_path
            != [terminal_event_id, *bridge_ids, path["target_event_id"]]
            or any(
                (left, right) not in edge_pairs
                for left, right in zip(predecessor_path, predecessor_path[1:])
            )
        ):
            _fail("T1_POST_TERMINAL_CONNECTION_PATH_INVALID", connection_id)

        flattened_transport_steps: list[str] = []
        source_bridge_ids: list[str] = []
        source_segment_open = True
        for bridge_id in bridge_ids:
            bridge = events.get(bridge_id)
            if bridge is None:
                _fail("T1_POST_TERMINAL_CONNECTION_PATH_INVALID", connection_id)
            bridge_kind = bridge.get("event_kind", bridge.get("kind"))
            subject_id = bridge.get(
                "subject_id", bridge.get("changed_subject", {}).get("subject_id")
            )
            subject_kind = bridge.get(
                "subject_kind", bridge.get("changed_subject", {}).get("subject_kind")
            )
            if (
                bridge_kind != "connection_bridge"
                or subject_kind == "state"
                or subject_id == line_id
                or bridge.get("lifecycle_effects", [])
            ):
                _fail("T1_POST_TERMINAL_STATE_CHANGE", bridge_id)
            flattened_transport_steps.extend(bridge["e1_capability_step_ids"])
            belongs_to_source = line_id in bridge["storyline_ids"]
            if belongs_to_source:
                if not source_segment_open:
                    _fail("T1_POST_TERMINAL_CONNECTION_PATH_INVALID", connection_id)
                source_bridge_ids.append(bridge_id)
                previous_owner = bridge_owners.setdefault(bridge_id, connection_id)
                if previous_owner != connection_id:
                    _fail("T1_POST_TERMINAL_EVENT_DUPLICATE", bridge_id)
                expected_tail_ids.add(bridge_id)
            else:
                source_segment_open = False
        if (
            len(flattened_transport_steps) != len(set(flattened_transport_steps))
            or set(flattened_transport_steps) != set(ready["transport_step_ids"])
        ):
            _fail(
                "T1_POST_TERMINAL_CONNECTION_READINESS_MISMATCH",
                connection_id,
            )
        relevant_paths.append((path, source_bridge_ids))

    if len(tail_ids) != len(expected_tail_ids) or set(tail_ids) != expected_tail_ids:
        _fail("T1_POST_TERMINAL_EVENT_INVALID", line_id)
    tail_positions = {event_id: index for index, event_id in enumerate(tail_ids)}
    for _path, source_bridge_ids in relevant_paths:
        if any(
            tail_positions[left] >= tail_positions[right]
            for left, right in zip(source_bridge_ids, source_bridge_ids[1:])
        ):
            _fail("T1_POST_TERMINAL_CONNECTION_PATH_INVALID", line_id)


def _validate_connection_realizations(
    realization_records: Sequence[Mapping[str, Any]],
    connections: Mapping[str, Mapping[str, Any]],
    state_anchor_by_line_index: Mapping[
        tuple[str, int], Mapping[str, Any]
    ],
    events: Mapping[str, Mapping[str, Any]],
    edges: Mapping[str, Mapping[str, Any]],
    edge_pairs: set[tuple[str, str]],
    timing: Mapping[str, Mapping[str, Any]],
    timing_relations: Mapping[str, str],
) -> None:
    """Validate exact S1 connection realization and cross-line edge ownership."""

    realizations = _unique_by_id(
        realization_records,
        "T1_CONNECTION_REALIZATION_DUPLICATE",
    )
    realization_by_connection: dict[str, Mapping[str, Any]] = {}
    cross_line_edge_claims: dict[str, list[str]] = {}

    def is_cross_line_edge(edge: Mapping[str, Any]) -> bool:
        return set(
            events[edge["from_event_id"]]["storyline_ids"]
        ).isdisjoint(
            events[edge["to_event_id"]]["storyline_ids"]
        )

    def has_causal_path(source_id: str, target_id: str) -> bool:
        frontier = [source_id]
        visited: set[str] = set()
        while frontier:
            current = frontier.pop()
            if current in visited:
                continue
            visited.add(current)
            for left, right in edge_pairs:
                if left != current:
                    continue
                if right == target_id:
                    return True
                if right not in visited:
                    frontier.append(right)
        return False

    for record in realizations.values():
        connection_id = record["connection_id"]
        connection = connections.get(connection_id)
        if (
            connection is None
            or connection_id in realization_by_connection
        ):
            _fail(
                "T1_CONNECTION_REALIZATION_MISMATCH",
                connection_id,
            )
        if record["relation"] != connection["relation"]:
            _fail(
                "T1_CONNECTION_RELATION_MISMATCH",
                connection_id,
            )
        expected_source_anchor = state_anchor_by_line_index.get(
            (
                connection["from_storyline_id"],
                connection["from_state_index"],
            )
        )
        expected_target_anchor = state_anchor_by_line_index.get(
            (
                connection["to_storyline_id"],
                connection["to_state_index"],
            )
        )
        if (
            expected_source_anchor is None
            or expected_target_anchor is None
            or expected_source_anchor["state"]
            != connection["from_state"]
            or expected_target_anchor["state"]
            != connection["to_state"]
        ):
            _fail(
                "T1_CONNECTION_CANONICAL_ANCHOR_INVALID",
                connection_id,
            )
        if record["source_anchor"] != expected_source_anchor:
            _fail(
                "T1_CONNECTION_SOURCE_ANCHOR_MISMATCH",
                connection_id,
            )
        if record["target_anchor"] != expected_target_anchor:
            _fail(
                "T1_CONNECTION_TARGET_ANCHOR_MISMATCH",
                connection_id,
            )
        timing_ids = record["timing_constraint_ids"]
        if (
            not timing_ids
            or any(item not in timing for item in timing_ids)
        ):
            _fail(
                "T1_CONNECTION_TIMING_MISMATCH",
                connection_id,
            )
        source_event_id = expected_source_anchor["event_id"]
        target_event_id = expected_target_anchor["event_id"]
        expected_relation = (
            "convergence"
            if connection["relation"] == "causal"
            else "association"
        )
        for timing_id in timing_ids:
            timing_record = timing[timing_id]
            if (
                timing_relations[timing_id] != expected_relation
                or not {
                    source_event_id,
                    target_event_id,
                }.issubset(timing_record["event_ids"])
            ):
                _fail(
                    "T1_CONNECTION_TIMING_MISMATCH",
                    connection_id,
                )

        if connection["relation"] == "causal":
            edge_ids = record["causal_edge_ids"]
            if record["realization_kind"] != "causal_handoff":
                _fail(
                    "T1_CONNECTION_REALIZATION_KIND_MISMATCH",
                    connection_id,
                )
            if any(edge_id not in edges for edge_id in edge_ids):
                _fail(
                    "T1_CONNECTION_CAUSAL_EDGE_MISMATCH",
                    connection_id,
                )
            path_edges = [edges[edge_id] for edge_id in edge_ids]
            if (
                not path_edges
                or path_edges[0]["from_event_id"]
                != source_event_id
                or path_edges[-1]["to_event_id"]
                != target_event_id
                or any(
                    left["to_event_id"] != right["from_event_id"]
                    for left, right in zip(
                        path_edges, path_edges[1:]
                    )
                )
                or any(
                    (
                        edge["from_event_id"],
                        edge["to_event_id"],
                    )
                    not in edge_pairs
                    for edge in path_edges
                )
            ):
                _fail(
                    "T1_CONNECTION_CAUSAL_PATH_MISMATCH",
                    connection_id,
                )
            path_event_ids = {
                source_event_id,
                *(edge["to_event_id"] for edge in path_edges),
            }
            if any(
                not path_event_ids.issubset(
                    timing[timing_id]["event_ids"]
                )
                for timing_id in timing_ids
            ):
                _fail(
                    "T1_CONNECTION_TIMING_MISMATCH",
                    connection_id,
                )
            owned_cross_line_edges = [
                edge
                for edge in path_edges
                if is_cross_line_edge(edge)
            ]
            if (
                not owned_cross_line_edges
                or any(
                    connection["from_storyline_id"]
                    not in events[edge["from_event_id"]][
                        "storyline_ids"
                    ]
                    or connection["to_storyline_id"]
                    not in events[edge["to_event_id"]][
                        "storyline_ids"
                    ]
                    for edge in owned_cross_line_edges
                )
            ):
                _fail(
                    "T1_CONNECTION_CROSS_LINE_EDGE_MISMATCH",
                    connection_id,
                )
            for edge in owned_cross_line_edges:
                cross_line_edge_claims.setdefault(
                    edge["id"], []
                ).append(connection_id)
        else:
            if (
                record["realization_kind"]
                != "associative_alignment"
                or record["causal_edge_ids"]
            ):
                _fail(
                    "T1_CONNECTION_ASSOCIATIVE_CAUSAL_CLAIM",
                    connection_id,
                )
            if (
                has_causal_path(source_event_id, target_event_id)
                or has_causal_path(target_event_id, source_event_id)
            ):
                _fail(
                    "T1_CONNECTION_ASSOCIATIVE_PREDECESSOR",
                    connection_id,
                )
        realization_by_connection[connection_id] = record

    if set(realization_by_connection) != set(connections):
        _fail(
            "T1_CONNECTION_REALIZATION_MISMATCH",
            "every SLC must be realized exactly once",
        )
    cross_line_edge_ids = {
        edge_id
        for edge_id, edge in edges.items()
        if is_cross_line_edge(edge)
    }
    if (
        set(cross_line_edge_claims) != cross_line_edge_ids
        or any(
            len(claims) != 1
            for claims in cross_line_edge_claims.values()
        )
    ):
        _fail(
            "T1_CROSS_LINE_CAUSAL_EDGE_OWNERSHIP_MISMATCH",
            "each cross-line causal edge requires exactly one causal SLC",
        )


def _validate_event_affordance_realizations(
    *,
    events: Mapping[str, Mapping[str, Any]],
    placements: Mapping[str, Mapping[str, Any]],
    affordances: Mapping[str, Mapping[str, Any]],
    coverage_by_requirement: Mapping[str, Mapping[str, Any]],
) -> None:
    realized_requirements_by_event: dict[str, set[str]] = {
        event_id: set() for event_id in events
    }
    for requirement_id, record in coverage_by_requirement.items():
        for event_id in record["realization_ids"]:
            realized_requirements_by_event[event_id].add(requirement_id)
    for event_id, event in events.items():
        placement = placements[event_id]
        placed = [affordances[item] for item in placement["affordance_ids"]]
        realized = realized_requirements_by_event[event_id]
        for requirement_id in realized:
            if not any(
                requirement_id in affordance["event_requirement_ids"]
                and affordance["environment_id"] == event["environment_id"]
                and event["initiating_action"] in affordance["allowed_actions"]
                and set(affordance["prerequisites"]).issubset(
                    event["preconditions"]
                )
                for affordance in placed
            ):
                _fail(
                    "T1_AFFORDANCE_REQUIREMENT_MISMATCH",
                    f"{requirement_id}/{event_id}",
                )
        for affordance in placed:
            if not set(affordance["event_requirement_ids"]) & realized:
                _fail(
                    "T1_AFFORDANCE_REQUIREMENT_MISMATCH",
                    f"unused {affordance['id']} on {event_id}",
                )


def _validate_event_capability_realizations_22(
    *,
    events: Mapping[str, Mapping[str, Any]],
    placements: Mapping[str, Mapping[str, Any]],
    environment: Mapping[str, Any],
) -> None:
    steps = _unique_by_id(
        environment["capability_step_registry"], "T1_E1_CAPABILITY_STEP_DUPLICATE"
    )
    facts = _unique_by_id(
        environment["capability_fact_registry"], "T1_E1_CAPABILITY_FACT_DUPLICATE"
    )
    affordances = _unique_by_id(
        environment["event_affordance_catalog"], "T1_AFFORDANCE_DUPLICATE"
    )
    for event_id, event in events.items():
        placement = placements[event_id]
        if set(placement["affordance_ids"]) != set(event["affordance_ids"]):
            _fail("T1_EVENT_PLACEMENT_PLAN_MISMATCH", event_id)
        event_steps = [steps.get(item) for item in event["e1_capability_step_ids"]]
        if any(item is None for item in event_steps):
            _fail("T1_EVENT_CAPABILITY_STEP_DANGLING", event_id)
        step_affordances = {item["affordance_id"] for item in event_steps}
        if not set(event["affordance_ids"]).issubset(step_affordances):
            _fail("T1_EVENT_CAPABILITY_AFFORDANCE_MISMATCH", event_id)
        if not any(item["action"] == event["initiating_action"] for item in event_steps):
            _fail("T1_EVENT_CAPABILITY_ACTION_MISMATCH", event_id)
        for step in event_steps:
            affordance = affordances.get(step["affordance_id"])
            if (
                step["environment_id"] != event["environment_id"]
                or affordance is None
                or affordance["environment_id"] != event["environment_id"]
                or step["action"] not in affordance["allowed_actions"]
            ):
                _fail("T1_EVENT_CAPABILITY_LOCALITY_MISMATCH", event_id)
        if not set(event["requires_capability_fact_ids"]).issubset(facts) or not set(
            event["produces_capability_fact_ids"]
        ).issubset(facts):
            _fail("T1_EVENT_CAPABILITY_FACT_DANGLING", event_id)


def _validate_model(
    model: Mapping[str, Any],
    baseline: Mapping[str, Any],
    storyline: Mapping[str, Any],
    world: Mapping[str, Any],
    environment: Mapping[str, Any],
    controls: Sequence[Mapping[str, Any]],
    runtime: Any,
    *,
    expected_gate: Mapping[str, str] | None = None,
    expected_sources: Sequence[Mapping[str, str]] | None = None,
    sealed_value: Callable[[Mapping[str, Any]], Any] | None = None,
) -> None:
    _boundary_check(model)
    try:
        runtime.validate(model, "event-timeline.schema.json")
    except Exception as error:
        _fail("T1_MODEL_SCHEMA_INVALID", str(error))
    if model.get("schema_version") == CURRENT_MODEL_SCHEMA_VERSION:
        e1_source = next(
            (
                item
                for item in (expected_sources or model.get("source_artifacts", []))
                if item.get("path") == "sources/E1/environment-system.json"
            ),
            None,
        )
        if not isinstance(e1_source, Mapping):
            _fail("T1_SOURCE_ARTIFACT_MISMATCH", "E1 canonical source")
        try:
            t1_contract_25.validate_p1_digests(
                model,
                environment,
                source_path="sources/E1/environment-system.json",
                source_sha256=e1_source["sha256"],
                canonical_sha256=rt.canonical_sha256,
            )
            t1_contract_25.validate_p2_plan(
                model,
                storyline,
                environment,
                rt.canonical_sha256,
                sealed_value=sealed_value,
            )
            t1_contract_25.validate_p3_exact(model, model)
        except t1_contract_25.Contract25Error as error:
            _fail(error.code, str(error))
    partition = model["authority_partition"]
    _validate_authority_disjoint(partition)
    if model["run_id"] != baseline["run_id"]:
        _fail("T1_RUN_ID_MISMATCH", "model belongs to another run")
    if model["event_demands"] != storyline["event_requirements"]:
        _fail(
            "T1_DEMAND_PROJECTION_MISMATCH",
            "T1 must consume exact S1 event requirements",
        )
    lines = _unique_by_id(storyline["storylines"], "T1_STORYLINE_DUPLICATE")
    requirements = _unique_by_id(
        storyline["event_requirements"], "T1_EVENT_REQUIREMENT_DUPLICATE"
    )
    requirement_line = {
        item_id: _event_line_for_requirement(item, lines)
        for item_id, item in requirements.items()
    }
    connections = _unique_by_id(
        storyline["connections"], "T1_CONNECTION_DUPLICATE"
    )
    environments = _unique_by_id(
        environment["environments"], "T1_ENVIRONMENT_DUPLICATE"
    )
    affordances = _unique_by_id(
        environment["event_affordance_catalog"], "T1_AFFORDANCE_DUPLICATE"
    )
    events = _unique_by_id(model["major_events"], "T1_EVENT_DUPLICATE")
    edges = _unique_by_id(model["causal_edges"], "T1_CAUSAL_EDGE_DUPLICATE")
    sequences = _unique_by_id(
        model["storyline_event_sequences"], "T1_SEQUENCE_DUPLICATE"
    )
    placements = {
        item["event_id"]: item for item in model["environment_placement"]
    }
    if len(placements) != len(model["environment_placement"]):
        _fail("T1_ENVIRONMENT_PLACEMENT_DUPLICATE", "event placement repeats")

    actor_slots = {
        slot for line in lines.values() for slot in line["actor_slot_ids"]
    }
    formal_objects: set[str] = set(lines) | actor_slots | set(environments)
    if model.get("schema_version") == CURRENT_MODEL_SCHEMA_VERSION:
        formal_objects.update(item["id"] for item in model["process_state_subject_registry"])
    resource_subjects = {
        item["id"] for item in world["resource_flows"]
    }
    authority_subjects = {
        item["id"] for item in world["authority_flows"]
    } | {item["id"] for item in environment["access_and_authority"]}
    world_rule_providers = {
        item["id"]: item
        for item in world["world_facts"]
        if item["kind"] == "rule"
    }
    world_system_providers = {
        item["id"]: item for item in world["systems"]
    }
    world_institution_providers = {
        item["id"]: item for item in world["institutions"]
    }
    access_providers = {
        item["id"]: item for item in environment["access_and_authority"]
    }
    transition_providers = {
        item["id"]: item for item in environment["transition_contracts"]
    }
    for source, fields in (
        (
            world,
            (
                "world_facts",
                "history_pressures",
                "institutions",
                "systems",
                "resource_flows",
                "authority_flows",
                "information_flows",
                "rule_conflict_matrix",
                "storyline_support_ledger",
            ),
        ),
        (
            environment,
            (
                "functional_zones",
                "environment_topology",
                "access_and_authority",
                "resource_and_information_channels",
                "hazards_and_failure_modes",
                "transition_contracts",
                "storyline_hosting_ledger",
                "event_affordance_catalog",
            ),
        ),
    ):
        for field in fields:
            formal_objects.update(item["id"] for item in source[field])

    event_times: dict[str, int] = {}
    event_roles: dict[str, list[str]] = {}
    for event_id, event in events.items():
        event_times[event_id] = _world_time(event["world_time"], event_id)
        event_roles[event_id] = _responsibilities(event)
        if not set(event["storyline_ids"]).issubset(lines):
            _fail("T1_EVENT_STORYLINE_DANGLING", event_id)
        allowed_slots = {
            slot
            for line_id in event["storyline_ids"]
            for slot in lines[line_id]["actor_slot_ids"]
        }
        if (
            not set(event["participant_slot_ids"]).issubset(allowed_slots)
            or event["initiator_slot_id"] not in event["participant_slot_ids"]
            or not set(event["counter_slot_ids"]).issubset(
                event["participant_slot_ids"]
            )
        ):
            _fail("T1_EVENT_PARTICIPATION_INVALID", event_id)
        if (
            not event["counter_slot_ids"]
            and not event["complication"].startswith("[NO_COUNTER:")
        ):
            _fail("T1_COUNTER_RESPONSIBILITY_MISSING", event_id)
        if event["environment_id"] not in environments:
            _fail("T1_EVENT_ENVIRONMENT_DANGLING", event_id)
        if set(event["before_state"]) != set(event["after_state"]):
            _fail("T1_EVENT_STATE_SHAPE_MISMATCH", event_id)
        changed = [
            subject
            for subject in event["before_state"]
            if event["before_state"][subject] != event["after_state"][subject]
        ]
        if len(changed) != 1 or changed[0] not in formal_objects:
            _fail("T1_EVENT_DOMINANT_CHANGE_INVALID", event_id)
        for field in (
            "initiating_action",
            "complication",
            "decisive_change",
            "direct_result",
            "next_pressure",
        ):
            if not _non_placeholder(event[field]):
                _fail("T1_EVENT_CONSEQUENCE_MISSING", f"{event_id}.{field}")

    if set(placements) != set(events):
        _fail("T1_ENVIRONMENT_PLACEMENT_MISMATCH", "one placement per event required")
    for event_id, placement in placements.items():
        event = events[event_id]
        if placement["environment_id"] != event["environment_id"]:
            _fail("T1_ENVIRONMENT_PLACEMENT_MISMATCH", event_id)
        for affordance_id in placement["affordance_ids"]:
            affordance = affordances.get(affordance_id)
            if affordance is None or affordance["environment_id"] != event["environment_id"]:
                _fail("T1_AFFORDANCE_ENVIRONMENT_MISMATCH", event_id)
            allowed_lines = {
                requirement_line[item]
                for item in affordance["event_requirement_ids"]
                if item in requirement_line
            }
            if not allowed_lines & set(event["storyline_ids"]):
                _fail("T1_AFFORDANCE_STORYLINE_MISMATCH", event_id)
            if event["initiating_action"] not in affordance["allowed_actions"]:
                _fail("T1_AFFORDANCE_ACTION_MISMATCH", event_id)
            if not set(affordance["prerequisites"]).issubset(event["preconditions"]):
                _fail("T1_AFFORDANCE_PRECONDITION_MISMATCH", event_id)

    edge_pairs: set[tuple[str, str]] = set()
    edge_keys: set[tuple[str, str, str]] = set()
    typed_edges = model.get("schema_version") == CURRENT_MODEL_SCHEMA_VERSION
    for edge in edges.values():
        left, right = edge["from_event_id"], edge["to_event_id"]
        if left not in events or right not in events or left == right:
            _fail("T1_CAUSAL_EDGE_DANGLING", edge["id"])
        mechanism = _CAUSAL_MECHANISM.fullmatch(edge["mechanism"])
        condition = _CAUSAL_CONDITION.fullmatch(edge["necessary_condition"])
        if (
            mechanism is None
            or condition is None
            or mechanism.group(1)
            != rt.canonical_sha256(events[left]["direct_result"])
            or mechanism.group(2)
            != rt.canonical_sha256(events[left]["next_pressure"])
            or condition.group(1)
            not in {
                rt.canonical_sha256(item)
                for item in events[right]["preconditions"]
            }
            or not _non_placeholder(mechanism.group(3))
            or not _non_placeholder(condition.group(2))
        ):
            _fail("T1_CAUSAL_SEMANTIC_BINDING_INVALID", edge["id"])
        pair = (left, right)
        edge_key = (
            left,
            right,
            edge["edge_kind"] if typed_edges else "legacy",
        )
        if edge_key in edge_keys:
            _fail("T1_CAUSAL_EDGE_DUPLICATE", edge["id"])
        edge_keys.add(edge_key)
        edge_pairs.add(pair)
    predecessor_pairs = {
        (predecessor, event_id)
        for event_id, event in events.items()
        for predecessor in event["predecessor_event_ids"]
    }
    if predecessor_pairs != edge_pairs:
        _fail("T1_CAUSAL_PREDECESSOR_MISMATCH", "edges and predecessors differ")
    if not _is_acyclic(set(events), edge_pairs):
        _fail("T1_CAUSAL_CYCLE", "event graph is cyclic")
    for left, right in edge_pairs:
        if event_times[left] > event_times[right]:
            _fail("T1_CAUSAL_TIME_CONTRADICTION", f"{left}->{right}")
    topological_order = _topological_order_index(set(events), edge_pairs)

    def effective_order_key(event_id: str) -> tuple[int, int]:
        return event_times[event_id], topological_order[event_id]

    timing = _unique_by_id(
        model["narrative_timing_constraints"], "T1_TIMING_DUPLICATE"
    )
    timing_relations: dict[str, str] = {}
    for item_id, item in timing.items():
        if not set(item["event_ids"]).issubset(events):
            _fail("T1_TIMING_EVENT_DANGLING", item_id)
        timing_relations[item_id] = _timing_relation(item)
    roots = {
        event_id for event_id, event in events.items()
        if not event["predecessor_event_ids"]
    }
    for root_id in roots:
        if "background" not in event_roles[root_id] or not any(
            root_id in item["event_ids"]
            and timing_relations[item_id] in {"concurrent", "independent-root"}
            for item_id, item in timing.items()
        ):
            _fail("T1_ROOT_EXPLANATION_MISSING", root_id)
    reachable = set(roots)
    changed = True
    while changed:
        changed = False
        for left, right in edge_pairs:
            if left in reachable and right not in reachable:
                reachable.add(right)
                changed = True
    if reachable != set(events):
        _fail("T1_CAUSAL_DISCONNECTED", "event not reachable from an explained root")

    sequence_by_line: dict[str, Mapping[str, Any]] = {}
    for sequence in sequences.values():
        line_id = sequence["storyline_id"]
        if line_id in sequence_by_line or line_id not in lines:
            _fail("T1_SEQUENCE_COVERAGE_MISMATCH", line_id)
        if (
            sequence["entry_state"] != lines[line_id]["start_state"]
            or sequence["exit_state"] != lines[line_id]["end_state"]
        ):
            _fail("T1_SEQUENCE_STATE_MISMATCH", line_id)
        event_ids = sequence["event_ids"]
        if any(item not in events for item in event_ids):
            _fail("T1_SEQUENCE_EVENT_DANGLING", line_id)
        if any(
            event_times[left] > event_times[right]
            or (
                event_times[left] == event_times[right]
                and not _causally_reaches(left, right, edge_pairs)
            )
            for left, right in zip(event_ids, event_ids[1:])
        ):
            _fail("T1_SEQUENCE_TIME_CONTRADICTION", line_id)
        if any(line_id not in events[item]["storyline_ids"] for item in event_ids):
            _fail("T1_SEQUENCE_MEMBERSHIP_MISMATCH", line_id)
        sequence_by_line[line_id] = sequence
    if set(sequence_by_line) != set(lines):
        _fail("T1_SEQUENCE_COVERAGE_MISMATCH", "one sequence per storyline required")
    for event_id, event in events.items():
        for line_id in event["storyline_ids"]:
            if event_id not in sequence_by_line[line_id]["event_ids"]:
                _fail("T1_SEQUENCE_MEMBERSHIP_MISMATCH", event_id)

    for line_id, line in lines.items():
        if line["type"] == "optional_melody":
            continue
        _validate_storyline_responsibility_progression(
            line_id,
            sequence_by_line[line_id]["event_ids"],
            event_roles,
        )

    coverage_by_requirement: dict[str, Mapping[str, Any]] = {}
    for record in model["event_coverage_ledger"]:
        if len(record["source_ids"]) != 1:
            _fail("T1_EVENT_COVERAGE_MISMATCH", record["id"])
        requirement_id = record["source_ids"][0]
        if (
            requirement_id not in requirements
            or requirement_id in coverage_by_requirement
            or not set(record["realization_ids"]).issubset(events)
        ):
            _fail("T1_EVENT_COVERAGE_MISMATCH", requirement_id)
        line_id = requirement_line[requirement_id]
        if any(
            line_id not in events[event_id]["storyline_ids"]
            for event_id in record["realization_ids"]
        ):
            _fail("T1_EVENT_COVERAGE_MISMATCH", requirement_id)
        coverage_by_requirement[requirement_id] = record
    if set(coverage_by_requirement) != set(requirements):
        _fail("T1_EVENT_COVERAGE_MISMATCH", "every EVD must be covered exactly once")

    if model["schema_version"] == CURRENT_MODEL_SCHEMA_VERSION:
        _validate_event_affordance_realizations(
            events=events,
            placements=placements,
            affordances=affordances,
            coverage_by_requirement=coverage_by_requirement,
        )

    # E1 may expose one EVD through several environment-local affordances.  T1
    # still owns exact EVD realization: every realized (EVD, event) pair must
    # select a placed affordance that names that EVD and admits this event's
    # local action and prerequisites.  A same-line affordance for another EVD
    # is not interchangeable and may not be carried as an unused bypass.
    if model["schema_version"] == CURRENT_MODEL_SCHEMA_VERSION:
        _validate_event_capability_realizations_22(
            events=events,
            placements=placements,
            environment=environment,
        )

    ledgers = _unique_by_id(model["state_ledger"], "T1_LEDGER_DUPLICATE")
    ledger_by_event_subject: dict[tuple[str, str], Mapping[str, Any]] = {}
    for ledger_id, ledger in ledgers.items():
        kind = _ledger_kind(ledger)
        subject = ledger["subject_id"]
        if subject not in formal_objects or len(ledger["trigger_ids"]) != 1:
            _fail("T1_LEDGER_SUBJECT_INVALID", ledger_id)
        trigger = ledger["trigger_ids"][0]
        if trigger not in events or subject not in events[trigger]["before_state"]:
            _fail("T1_LEDGER_EVENT_MISMATCH", ledger_id)
        expected_kind = (
            "resource"
            if subject in resource_subjects
            else "authority"
            if subject in authority_subjects
            else "state"
        )
        if kind != expected_kind:
            _fail("T1_LEDGER_KIND_INVALID", ledger_id)
        event = events[trigger]
        event_lines = set(event["storyline_ids"])
        placed_affordances = set(placements[trigger]["affordance_ids"])

        def provider_applies(provider_id: str) -> bool:
            if provider_id in world_rule_providers:
                return bool(
                    set(world_rule_providers[provider_id]["applies_to_ids"])
                    & event_lines
                )
            if provider_id in world_system_providers:
                return bool(
                    set(world_system_providers[provider_id]["storyline_ids"])
                    & event_lines
                )
            if provider_id in world_institution_providers:
                return bool(
                    set(world_institution_providers[provider_id]["storyline_ids"])
                    & event_lines
                )
            if provider_id in access_providers:
                return (
                    access_providers[provider_id]["subject_id"]
                    == event["environment_id"]
                )
            if provider_id in affordances:
                return provider_id in placed_affordances
            if provider_id in transition_providers:
                provider = transition_providers[provider_id]
                return (
                    provider["subject_id"] == event["environment_id"]
                    and bool(
                        set(provider["trigger_ids"]) & placed_affordances
                    )
                )
            return False

        if not all(
            provider_applies(provider_id)
            for provider_id in ledger["allowed_by_ids"]
        ):
            _fail("T1_LEDGER_PROVIDER_INVALID", ledger_id)
        if (
            ledger["from_state"] != events[trigger]["before_state"][subject]
            or ledger["to_state"] != events[trigger]["after_state"][subject]
            or ledger["from_state"] == ledger["to_state"]
        ):
            _fail("T1_LEDGER_EVENT_MISMATCH", ledger_id)
        key = (trigger, subject)
        if key in ledger_by_event_subject:
            _fail("T1_LEDGER_DUPLICATE", ledger_id)
        ledger_by_event_subject[key] = ledger
    for event_id, event in events.items():
        changed_subjects = [
            subject
            for subject in event["before_state"]
            if event["before_state"][subject] != event["after_state"][subject]
        ]
        if set(changed_subjects) != {
            subject for trigger, subject in ledger_by_event_subject if trigger == event_id
        }:
            _fail("T1_EVENT_LEDGER_BIDIRECTIONAL_MISMATCH", event_id)
    by_ledger_subject: dict[str, list[Mapping[str, Any]]] = {}
    for ledger in ledgers.values():
        by_ledger_subject.setdefault(ledger["subject_id"], []).append(ledger)
    for subject, subject_ledgers in by_ledger_subject.items():
        ordered = sorted(
            subject_ledgers,
            key=lambda item: effective_order_key(item["trigger_ids"][0]),
        )
        if any(
            left["to_state"] != right["from_state"]
            or (
                event_times[left["trigger_ids"][0]]
                == event_times[right["trigger_ids"][0]]
                and not _causally_reaches(
                    left["trigger_ids"][0],
                    right["trigger_ids"][0],
                    edge_pairs,
                )
            )
            for left, right in zip(ordered, ordered[1:])
        ):
            _fail("T1_LEDGER_CONTINUITY_BROKEN", subject)

    state_anchor_by_line_index: dict[
        tuple[str, int], dict[str, Any]
    ] = {}
    for line_id, line in lines.items():
        required_states = [
            line["start_state"],
            *line["state_changes"],
            line["end_state"],
        ]
        transition_ledgers = [
            ledger
            for event_id in sequence_by_line[line_id]["event_ids"]
            for ledger in ledgers.values()
            if ledger["subject_id"] == line_id
            and ledger["trigger_ids"] == [event_id]
        ]
        observed = [
            (ledger["from_state"], ledger["to_state"])
            for ledger in transition_ledgers
        ]
        expected = list(zip(required_states, required_states[1:]))
        if observed != expected:
            _fail("T1_STORYLINE_STATE_PROGRESSION_MISMATCH", line_id)
        transition_spans: list[Sequence[str]] = []
        if model.get("schema_version") == CURRENT_MODEL_SCHEMA_VERSION:
            transition_covers = sorted(
                (
                    item
                    for item in model["transition_event_cover"]
                    if item["storyline_id"] == line_id
                ),
                key=lambda item: item["from_state_index"],
            )
            transition_spans = [item["event_ids"] for item in transition_covers]
            sequence_ids = sequence_by_line[line_id]["event_ids"]
            if (
                len(transition_spans) != len(transition_ledgers)
                or any(
                    ledger["trigger_ids"] != [span[-1]]
                    for ledger, span in zip(transition_ledgers, transition_spans)
                )
                or any(
                    not any(
                        sequence_ids[index : index + len(span)] == list(span)
                        for index in range(len(sequence_ids) - len(span) + 1)
                    )
                    for span in transition_spans
                )
            ):
                _fail("T1_STORYLINE_TRANSITION_SPAN_PROJECTION_MISMATCH", line_id)
        _validate_terminal_state_event(
            line_id,
            line["type"],
            transition_ledgers,
            sequence_by_line[line_id]["event_ids"],
            current_schema=(
                model.get("schema_version") == CURRENT_MODEL_SCHEMA_VERSION
            ),
            transition_spans=transition_spans,
            events=events,
            connections=connections,
            connection_event_paths=model.get("connection_event_paths", []),
            connection_path_readiness=environment.get(
                "connection_path_readiness", []
            ),
            edge_pairs=edge_pairs,
        )
        state_anchor_by_line_index.update(
            _state_anchors_for_line(
                line_id,
                required_states,
                transition_ledgers,
                transition_spans
                if model.get("schema_version") == CURRENT_MODEL_SCHEMA_VERSION
                else None,
            )
        )

    propositions, obligation_realizations = _validate_proposition_contract(
        model,
        storyline,
        events,
        event_times,
        edge_pairs,
        state_anchor_by_line_index,
    )

    connection_edges = (
        {
            edge_id: edge
            for edge_id, edge in edges.items()
            if edge["edge_kind"] == "narrative_causal"
        }
        if typed_edges
        else edges
    )
    connection_edge_pairs = {
        (edge["from_event_id"], edge["to_event_id"])
        for edge in connection_edges.values()
    }
    _validate_connection_realizations(
        model["connection_realization"],
        connections,
        state_anchor_by_line_index,
        events,
        connection_edges,
        connection_edge_pairs,
        timing,
        timing_relations,
    )

    information = _unique_by_id(
        model["information_changes"], "T1_INFORMATION_DUPLICATE"
    )
    for info_id, change in information.items():
        if (
            change["subject_id"] not in formal_objects
            or not set(change["event_ids"]).issubset(events)
            or not set(change["visibility_ids"]).issubset(actor_slots)
            or change["before"] == change["after"]
        ):
            _fail("T1_INFORMATION_CHANGE_INVALID", info_id)
        for event_id in change["event_ids"]:
            if info_id not in events[event_id]["information_changes"]:
                _fail("T1_INFORMATION_BIDIRECTIONAL_MISMATCH", info_id)
    for event_id, event in events.items():
        expected_info = {
            info_id
            for info_id, change in information.items()
            if event_id in change["event_ids"]
        }
        if set(event["information_changes"]) != expected_info:
            _fail("T1_INFORMATION_BIDIRECTIONAL_MISMATCH", event_id)
    if model.get("schema_version") == CURRENT_MODEL_SCHEMA_VERSION:
        try:
            t1_contract_25.validate_information_projection(
                model, storyline, environment, events
            )
        except t1_contract_25.Contract25Error as error:
            _fail(error.code, str(error))
    by_info_subject: dict[str, list[Mapping[str, Any]]] = {}
    for change in information.values():
        by_info_subject.setdefault(change["subject_id"], []).append(change)
    for subject, changes in by_info_subject.items():
        ordered = sorted(
            changes,
            key=lambda item: effective_order_key(item["event_ids"][0]),
        )
        if any(
            left["after"] != right["before"]
            or (
                event_times[left["event_ids"][0]]
                == event_times[right["event_ids"][0]]
                and not _causally_reaches(
                    left["event_ids"][0],
                    right["event_ids"][0],
                    edge_pairs,
                )
            )
            for left, right in zip(ordered, ordered[1:])
        ):
            _fail("T1_INFORMATION_CONTINUITY_BROKEN", subject)

    span_start = _WORLD_TIME_TOKEN.fullmatch(model["event_span"]["start"])
    span_end = _WORLD_TIME_TOKEN.fullmatch(model["event_span"]["end"])
    if (
        span_start is None
        or span_end is None
        or int(span_start.group(1)) != min(event_times.values())
        or int(span_end.group(1)) != max(event_times.values())
    ):
        _fail("T1_EVENT_SPAN_MISMATCH", "span must equal event min/max")
    required_axes = {
        "world_time",
        "background_time",
        "event_time",
        "narrative_disclosure",
    }
    if set(model["timeline_axes"]["axes"]) != required_axes:
        _fail("T1_TIMELINE_AXES_INCOMPLETE", "four explicit axes required")

    locked = {
        item["id"]
        for item in baseline["control_registry"]
        if item["hardness"] == "author_locked"
    }
    author_open = {
        item["id"]
        for item in baseline["control_registry"]
        if item["hardness"] == "author_open"
    }
    owned_entities: dict[str, Mapping[str, Any]] = {
        **events,
        **edges,
        **sequences,
        **timing,
        **ledgers,
        **information,
        **propositions,
        **obligation_realizations,
        **{item["id"]: item for item in model["connection_realization"]},
        **{item["id"]: item for item in model["event_coverage_ledger"]},
    }
    if model.get("schema_version") == CURRENT_MODEL_SCHEMA_VERSION:
        owned_entities.update(
            {item["id"]: item for item in model["process_state_subject_registry"]}
        )
        owned_entities[model["lifecycle_scope"]["id"]] = model[
            "lifecycle_scope"
        ]
        owned_entities.update(
            {
                item["id"]: item
                for item in model["lifecycle_contract_registry"]
            }
        )
        owned_entities.update(
            {
                item["token_instance_id"]: item
                for item in model["authority_token_instance_ledger"]
            }
        )
    decisions = {item["id"]: item for item in model["design_decisions"]}
    if set(partition["author_locked"]) != locked:
        _fail("T1_AUTHORITY_PARTITION_MISMATCH", "author_locked differs from B0")
    if set(partition["author_open"]) != author_open:
        _fail("T1_AUTHORITY_PARTITION_MISMATCH", "author_open differs from B0")
    if set(partition["autonomous_owned"]) != set(owned_entities) | set(decisions):
        _fail("T1_AUTHORITY_PARTITION_MISMATCH", "T1 owned set is not exact")
    if set(partition["downstream_freedom"]) != actor_slots:
        _fail("T1_AUTHORITY_PARTITION_MISMATCH", "T1 handoff set is not exact")
    for decision in decisions.values():
        if (
            decision["owner"] != "T1"
            or decision["selection"] not in decision["options"]
            or not set(decision["projection_ids"]).issubset(owned_entities)
        ):
            _fail("T1_DECISION_INVALID", decision["id"])
    for claim in model["derivation_claims"]:
        if len(claim["projection_ids"]) == 1:
            projection = owned_entities.get(claim["projection_ids"][0])
            if projection is None or claim["value_sha256"] != rt.canonical_sha256(
                projection
            ):
                _fail("T1_DERIVATION_STALE", claim["id"])
    claimed = {
        item["projection_ids"][0]
        for item in model["derivation_claims"]
        if len(item["projection_ids"]) == 1
    }
    if not set(events).issubset(claimed) or not set(sequences).issubset(claimed):
        _fail(
            "T1_DERIVATION_INCOMPLETE",
            "each event and storyline sequence needs derivation evidence",
        )
    actual_open = {
        source_id
        for item in model["open_items"]
        for source_id in item["source_ids"]
    }
    if actual_open != author_open:
        _fail("T1_OPEN_ITEMS_MISMATCH", "author-open controls changed")
    if expected_gate is not None and model["input_gate"] != expected_gate:
        _fail("T1_GATE_REFERENCE_MISMATCH", "model gate is not stored gate")
    if expected_sources is not None and model["source_artifacts"] != list(
        expected_sources
    ):
        _fail(
            "T1_SOURCE_ARTIFACT_MISMATCH",
            "model does not bind exact B0/S1/W1/E1 sources",
        )


def start_t1_session(
    workspace: str | Path,
    *,
    baseline_package: str | Path,
    storyline_package: str | Path,
    world_package: str | Path,
    environment_package: str | Path,
    input_gate: Any,
    runtime: Any | None = None,
) -> dict[str, Any]:
    root = Path(workspace).resolve()
    if root.exists():
        _fail("T1_SESSION_EXISTS", str(root))
    thread_id = os.environ.get("CODEX_THREAD_ID", "").strip()
    if not thread_id:
        _fail("T1_THREAD_REQUIRED", "CODEX_THREAD_ID is required")
    contract_runtime = runtime or rt.ContractRuntime()
    (
        b0_root,
        s1_root,
        w1_root,
        e1_root,
        baseline,
        storyline,
        world,
        environment,
        controls,
        b0_ref,
        s1_ref,
        w1_ref,
        e1_ref,
    ) = _session_context(
        baseline_package=baseline_package,
        storyline_package=storyline_package,
        world_package=world_package,
        environment_package=environment_package,
        input_gate=input_gate,
        runtime=contract_runtime,
    )
    session = {
        "schema_version": "2.0",
        "run_id": baseline["run_id"],
        "stage": "T1",
        "session_id": _session_id(
            thread_id, input_gate.reference, b0_ref, s1_ref, w1_ref, e1_ref
        ),
        "thread_id": thread_id,
        "input_gate": copy.deepcopy(input_gate.reference),
        "state_before": copy.deepcopy(input_gate.data["run_state"]),
        "baseline_completion": b0_ref,
        "upstream_completions": [s1_ref, w1_ref, e1_ref],
        "source_artifacts": _source_artifacts(
            b0_root, s1_root, w1_root, e1_root
        ),
        "upstream_package_bindings": _upstream_package_bindings(
            b0_root, s1_root, w1_root, e1_root
        ),
        "e1_semantic_review_bindings": _e1_semantic_review_bindings(e1_root),
        "control_bindings": _control_bindings(controls),
        "storyline_bindings": _object_bindings(
            storyline["storylines"], extra="type"
        ),
        "event_requirement_bindings": _object_bindings(
            storyline["event_requirements"], extra="target_stage"
        ),
        "storyline_connection_bindings": _object_bindings(
            storyline["connections"], extra="type"
        ),
        "storyline_state_bindings": [
            {
                "id": item["id"],
                "value_sha256": rt.canonical_sha256(
                    [
                        item["start_state"],
                        *item["state_changes"],
                        item["end_state"],
                    ]
                ),
            }
            for item in storyline["storylines"]
        ],
        "world_rule_bindings": _object_bindings(
            [
                *world["world_facts"],
                *world["systems"],
                *world["institutions"],
                *world["resource_flows"],
                *world["authority_flows"],
            ]
        ),
        "environment_bindings": _object_bindings(
            environment["environments"]
        ),
        "affordance_bindings": _object_bindings(
            environment["event_affordance_catalog"]
        ),
        "implementation_bindings": _implementation_bindings(),
        "plan_review_protocol": T1_PLAN_REVIEW_PROTOCOL,
        "phases": list(PHASES),
    }
    root.mkdir(parents=True)
    _write(root / "generation-session.json", session)
    return copy.deepcopy(session)


def _validated_session(
    workspace: Path,
    *,
    baseline_package: str | Path,
    storyline_package: str | Path,
    world_package: str | Path,
    environment_package: str | Path,
    input_gate: Any,
    runtime: Any,
    full_validation: bool = True,
) -> tuple[
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    list[dict[str, Any]],
]:
    session = _read(workspace / "generation-session.json", "T1_SESSION_INVALID")
    (
        b0_root,
        s1_root,
        w1_root,
        e1_root,
        baseline,
        storyline,
        world,
        environment,
        controls,
        b0_ref,
        s1_ref,
        w1_ref,
        e1_ref,
    ) = _session_context(
        baseline_package=baseline_package,
        storyline_package=storyline_package,
        world_package=world_package,
        environment_package=environment_package,
        input_gate=input_gate,
        runtime=runtime,
        full_validation=full_validation,
    )
    thread_id = os.environ.get("CODEX_THREAD_ID", "").strip()
    expected = {
        "schema_version": "2.0",
        "run_id": baseline["run_id"],
        "stage": "T1",
        "session_id": _session_id(
            thread_id, input_gate.reference, b0_ref, s1_ref, w1_ref, e1_ref
        ),
        "thread_id": thread_id,
        "input_gate": copy.deepcopy(input_gate.reference),
        "state_before": copy.deepcopy(input_gate.data["run_state"]),
        "baseline_completion": b0_ref,
        "upstream_completions": [s1_ref, w1_ref, e1_ref],
        "source_artifacts": _source_artifacts(
            b0_root, s1_root, w1_root, e1_root
        ),
        "upstream_package_bindings": _upstream_package_bindings(
            b0_root, s1_root, w1_root, e1_root
        ),
        "e1_semantic_review_bindings": _e1_semantic_review_bindings(e1_root),
        "control_bindings": _control_bindings(controls),
        "storyline_bindings": _object_bindings(
            storyline["storylines"], extra="type"
        ),
        "event_requirement_bindings": _object_bindings(
            storyline["event_requirements"], extra="target_stage"
        ),
        "storyline_connection_bindings": _object_bindings(
            storyline["connections"], extra="type"
        ),
        "storyline_state_bindings": [
            {
                "id": item["id"],
                "value_sha256": rt.canonical_sha256(
                    [
                        item["start_state"],
                        *item["state_changes"],
                        item["end_state"],
                    ]
                ),
            }
            for item in storyline["storylines"]
        ],
        "world_rule_bindings": _object_bindings(
            [
                *world["world_facts"],
                *world["systems"],
                *world["institutions"],
                *world["resource_flows"],
                *world["authority_flows"],
            ]
        ),
        "environment_bindings": _object_bindings(
            environment["environments"]
        ),
        "affordance_bindings": _object_bindings(
            environment["event_affordance_catalog"]
        ),
        "implementation_bindings": _implementation_bindings(),
        "plan_review_protocol": T1_PLAN_REVIEW_PROTOCOL,
        "phases": list(PHASES),
    }
    if not thread_id or session != expected:
        _fail(
            "T1_SESSION_INVALID",
            "session no longer binds B0/S1/W1/E1/gate/thread",
        )
    return session, baseline, storyline, world, environment, controls


def _sealed_phase_payload(
    root: Path, *, sequence: int, phase: str
) -> Mapping[str, Any]:
    evidence = _read(
        root / "generation-evidence" / f"{sequence:02d}-{phase}.json",
        "T1_EVIDENCE_MISSING",
    )
    payload = evidence.get("payload")
    if (
        not isinstance(payload, Mapping)
        or evidence.get("phase") != phase
        or evidence.get("payload_sha256") != rt.canonical_sha256(payload)
    ):
        _fail("T1_EVIDENCE_INVALID", phase)
    return payload


def _resolve_json_pointer(value: Any, pointer: str) -> Any:
    if pointer == "":
        return value
    if not isinstance(pointer, str) or not pointer.startswith("/"):
        _fail("T1_JSON_POINTER_INVALID", str(pointer))
    current = value
    for raw in pointer[1:].split("/"):
        token = raw.replace("~1", "/").replace("~0", "~")
        if isinstance(current, Mapping) and token in current:
            current = current[token]
        elif isinstance(current, list) and token.isdigit() and int(token) < len(current):
            current = current[int(token)]
        else:
            _fail("T1_JSON_POINTER_INVALID", pointer)
    return current


def _sealed_initial_value(root: Path, origin: Mapping[str, Any]) -> Any:
    source = origin["source_artifact"]
    path = PurePosixPath(source["path"])
    if path.is_absolute() or ".." in path.parts:
        _fail("T1_TOKEN_INSTANCE_INITIAL_SOURCE_STALE", source["path"])
    candidate = root / Path(*path.parts)
    if not candidate.is_file() or rt.sha256_file(candidate) != source["sha256"]:
        _fail("T1_TOKEN_INSTANCE_INITIAL_SOURCE_STALE", source["path"])
    return _resolve_json_pointer(_read(candidate, "T1_TOKEN_INSTANCE_INITIAL_SOURCE_STALE"), origin["source_pointer"])


def _sealed_initial_value_from_packages(
    origin: Mapping[str, Any], *,
    baseline_package: str | Path, storyline_package: str | Path,
    world_package: str | Path, environment_package: str | Path,
) -> Any:
    source = origin["source_artifact"]
    logical = PurePosixPath(source["path"])
    roots = {
        "B0": Path(baseline_package).resolve(),
        "S1": Path(storyline_package).resolve(),
        "W1": Path(world_package).resolve(),
        "E1": Path(environment_package).resolve(),
    }
    if len(logical.parts) < 3 or logical.parts[0] != "sources" or logical.parts[1] not in roots or ".." in logical.parts:
        _fail("T1_TOKEN_INSTANCE_INITIAL_SOURCE_STALE", source["path"])
    candidate = roots[logical.parts[1]] / Path(*logical.parts[2:])
    if not candidate.is_file() or rt.sha256_file(candidate) != source["sha256"]:
        _fail("T1_TOKEN_INSTANCE_INITIAL_SOURCE_STALE", source["path"])
    return _resolve_json_pointer(_read(candidate, "T1_TOKEN_INSTANCE_INITIAL_SOURCE_STALE"), origin["source_pointer"])


def _plan_review_paths(
    root: Path, candidate_sha256: str
) -> tuple[Path, Path, Path, Path, Path, Path]:
    review_root = root / "semantic-reviews" / T1_PLAN_REVIEW_PROTOCOL / candidate_sha256
    return (
        review_root / "candidate.json",
        review_root / "request.json",
        review_root / "review-task-output.json",
        review_root / "review.json",
        review_root / "validation.json",
        review_root / "package-manifest.json",
    )


def _plan_review_claims(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    return t1_contract_25.semantic_claim_records(payload, rt.canonical_sha256)


def _expected_plan_review_request(
    root: Path, *, session: Mapping[str, Any], payload: Mapping[str, Any]
) -> dict[str, Any]:
    p1 = root / "generation-evidence" / "01-event-demand-scan.json"
    candidate_sha256 = rt.canonical_sha256(payload)
    implementation = {
        item["identity"]: item["sha256"] for item in session["implementation_bindings"]
    }
    return {
        "schema_version": "1.0",
        "stage": "T1",
        "review_kind": "initial-event-plan-semantics",
        "review_protocol": T1_PLAN_REVIEW_PROTOCOL,
        "run_id": session["run_id"],
        "session_id": session["session_id"],
        "producer_thread_id": session["thread_id"],
        "generation_session": rt.artifact_reference(root / "generation-session.json", root=root),
        "input_gate": copy.deepcopy(session["input_gate"]),
        "prior_phase_evidence": [rt.artifact_reference(p1, root=root)],
        "candidate_path": (
            f"semantic-reviews/{T1_PLAN_REVIEW_PROTOCOL}/"
            f"{candidate_sha256}/candidate.json"
        ),
        "candidate_sha256": candidate_sha256,
        "upstream_packages": copy.deepcopy(session["upstream_package_bindings"]),
        "e1_semantic_review_packages": copy.deepcopy(session["e1_semantic_review_bindings"]),
        "implementation_sha256": implementation["skill/run_v2.py"],
        "schema_sha256": implementation["schemas/event-timeline.schema.json"],
        "protocol_sha256": implementation["skill/runtime-contract.md"],
        "planned_claim_ids": [item["claim_id"] for item in _plan_review_claims(payload)],
        "claims": _plan_review_claims(payload),
        "review_contract": {
            "coverage": "Every planned claim must receive exactly one verdict.",
            "scope": "Review initial decomposition/classification, option selection, atomic events, transitions, connections, disclosure propositions and their communication-capable occurrences/recipients, authority instances and process subjects.",
            "boundary": "Do not add story facts, environments, permissions, psychology or prose.",
        },
    }


def start_t1_plan_semantic_review(
    workspace: str | Path,
    *,
    baseline_package: str | Path,
    storyline_package: str | Path,
    world_package: str | Path,
    environment_package: str | Path,
    input_gate: Any,
    payload: Mapping[str, Any],
    runtime: Any | None = None,
) -> dict[str, Any]:
    root = Path(workspace).resolve()
    contract_runtime = runtime or rt.ContractRuntime()
    session, _baseline, storyline, _world, environment, _controls_value = _validated_session(
        root,
        baseline_package=baseline_package,
        storyline_package=storyline_package,
        world_package=world_package,
        environment_package=environment_package,
        input_gate=input_gate,
        runtime=contract_runtime,
        full_validation=False,
    )
    if session.get("plan_review_protocol") != T1_PLAN_REVIEW_PROTOCOL:
        _fail("T1_PLAN_REVIEW_INVALID", "session protocol mismatch")
    body = copy.deepcopy(dict(payload))
    if set(body) != set(PHASE_FIELDS["global-timeline"]):
        _fail("T1_PHASE_PAYLOAD_INVALID", "invalid P2 review candidate")
    if not (root / "generation-evidence" / "01-event-demand-scan.json").is_file() or (
        root / "generation-evidence" / "02-global-timeline.json"
    ).exists():
        _fail("T1_PHASE_ORDER_INVALID", "review requires sealed P1 and open P2")
    p1 = _sealed_phase_payload(root, sequence=1, phase="event-demand-scan")
    t1_contract_25.validate_p1_digests(
        p1,
        environment,
        source_path="sources/E1/environment-system.json",
        source_sha256=next(
            item["sha256"] for item in session["source_artifacts"]
            if item["path"] == "sources/E1/environment-system.json"
        ),
        canonical_sha256=rt.canonical_sha256,
    )
    try:
        t1_contract_25.validate_p2_plan(
            body,
            storyline,
            environment,
            rt.canonical_sha256,
            sealed_value=lambda origin: _sealed_initial_value_from_packages(
                origin,
                baseline_package=baseline_package,
                storyline_package=storyline_package,
                world_package=world_package,
                environment_package=environment_package,
            ),
        )
    except t1_contract_25.Contract25Error as error:
        _fail(error.code, str(error))
    candidate_sha256 = rt.canonical_sha256(body)
    candidate_path, request_path, _task_output_path, review_path, _validation_path, _manifest_path = (
        _plan_review_paths(root, candidate_sha256)
    )
    if candidate_path.exists() and _read(candidate_path, "T1_PLAN_REVIEW_INVALID") != body:
        _fail("T1_PLAN_REVIEW_INVALID", "stored candidate differs")
    if not candidate_path.exists():
        _write(candidate_path, body)
    request = _expected_plan_review_request(root, session=session, payload=body)
    if review_path.exists():
        _fail("T1_PLAN_REVIEW_EXISTS", str(review_path))
    if request_path.exists() and _read(request_path, "T1_PLAN_REVIEW_INVALID") != request:
        _fail("T1_PLAN_REVIEW_INVALID", "stored request differs")
    if not request_path.exists():
        _write(request_path, request)
    return copy.deepcopy(request)


def seal_t1_review_task_output(
    workspace: str | Path,
    *,
    candidate_sha256: str,
    task_id: str,
    verdict_payload: Mapping[str, Any],
) -> dict[str, Any]:
    """Seal the independent P2 reviewer task output before review submission."""

    root = Path(workspace).resolve()
    candidate_path, request_path, task_output_path, review_path, validation_path, manifest_path = (
        _plan_review_paths(root, candidate_sha256)
    )
    if any(path.exists() for path in (task_output_path, review_path, validation_path, manifest_path)):
        _fail("T1_REVIEW_TASK_OUTPUT_EXISTS", str(task_output_path))
    if (
        not isinstance(task_id, str)
        or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:/-]{2,127}", task_id.strip()) is None
    ):
        _fail("T1_REVIEW_TASK_OUTPUT_INVALID", "task id")
    request = _read(request_path, "T1_REVIEW_TASK_OUTPUT_INVALID")
    candidate = _read(candidate_path, "T1_REVIEW_TASK_OUTPUT_INVALID")
    reviewer_thread_id = os.environ.get("CODEX_THREAD_ID", "").strip()
    if (
        not reviewer_thread_id
        or reviewer_thread_id == request.get("producer_thread_id")
        or request.get("candidate_sha256") != candidate_sha256
        or rt.canonical_sha256(candidate) != candidate_sha256
        or request.get("review_kind") != "initial-event-plan-semantics"
        or request.get("review_protocol") != T1_PLAN_REVIEW_PROTOCOL
    ):
        _fail("T1_REVIEW_TASK_OUTPUT_INVALID", "review identity mismatch")
    if set(verdict_payload) != {"claim_verdicts", "findings"}:
        _fail("T1_REVIEW_TASK_OUTPUT_INVALID", "verdict payload differs")
    request_ref = rt.artifact_reference(request_path, root=root)
    candidate_ref = rt.artifact_reference(candidate_path, root=root)
    output = {
        "schema_version": "1.0",
        "stage": "T1",
        "review_kind": request["review_kind"],
        "review_protocol": request["review_protocol"],
        "task_id": task_id.strip(),
        "producer_thread_id": request["producer_thread_id"],
        "reviewer_thread_id": reviewer_thread_id,
        "candidate_sha256": candidate_sha256,
        "candidate": candidate_ref,
        "request": request_ref,
        "verdict_payload": copy.deepcopy(dict(verdict_payload)),
    }
    _write(task_output_path, output)
    output_ref = rt.artifact_reference(task_output_path, root=root)
    return {
        "task_id": output["task_id"],
        "producer_thread_id": output["producer_thread_id"],
        "reviewer_thread_id": output["reviewer_thread_id"],
        "output_artifact": output_ref,
        "output_sha256": rt.canonical_sha256(output),
        "candidate": candidate_ref,
        "candidate_sha256": candidate_sha256,
        "request": request_ref,
        "review_kind": output["review_kind"],
        "review_protocol": output["review_protocol"],
        "verdict_payload": copy.deepcopy(dict(verdict_payload)),
    }


def _validate_t1_reviewer_task_receipt(
    *,
    root: Path,
    request: Mapping[str, Any],
    reviewer_thread_id: str,
    receipt: Any,
    verdict_payload: Mapping[str, Any],
    candidate_reference: Mapping[str, str],
    request_reference: Mapping[str, str],
) -> None:
    required = {
        "task_id", "producer_thread_id", "reviewer_thread_id",
        "output_artifact", "output_sha256", "candidate", "candidate_sha256",
        "request", "review_kind", "review_protocol", "verdict_payload",
    }
    if not isinstance(receipt, Mapping) or set(receipt) != required:
        _fail("T1_REVIEW_TASK_RECEIPT_INVALID", "receipt fields differ")
    if (
        not isinstance(receipt["task_id"], str)
        or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:/-]{2,127}", receipt["task_id"]) is None
        or receipt["producer_thread_id"] != request["producer_thread_id"]
        or receipt["reviewer_thread_id"] != reviewer_thread_id
        or receipt["candidate"] != candidate_reference
        or receipt["candidate_sha256"] != request["candidate_sha256"]
        or receipt["request"] != request_reference
        or receipt["review_kind"] != request["review_kind"]
        or receipt["review_protocol"] != request["review_protocol"]
        or receipt["verdict_payload"] != verdict_payload
        or not isinstance(receipt["output_sha256"], str)
        or re.fullmatch(r"[a-f0-9]{64}", receipt["output_sha256"]) is None
        or receipt["output_sha256"] == "0" * 64
    ):
        _fail("T1_REVIEW_TASK_RECEIPT_INVALID", "receipt identity differs")
    try:
        candidate_path = rt.verify_artifact_reference(receipt["candidate"], root=root)
        request_path = rt.verify_artifact_reference(receipt["request"], root=root)
        output_path = rt.verify_artifact_reference(receipt["output_artifact"], root=root)
    except Exception as exc:
        _fail("T1_REVIEW_TASK_RECEIPT_INVALID", str(exc))
    expected_output_path = _plan_review_paths(
        root, request["candidate_sha256"]
    )[2]
    if (
        output_path != expected_output_path
        or receipt["output_artifact"]
        != rt.artifact_reference(expected_output_path, root=root)
    ):
        _fail("T1_REVIEW_TASK_RECEIPT_INVALID", "task output artifact differs")
    candidate = _read(candidate_path, "T1_REVIEW_TASK_RECEIPT_INVALID")
    if rt.canonical_sha256(candidate) != request["candidate_sha256"]:
        _fail("T1_REVIEW_TASK_RECEIPT_INVALID", "candidate differs")
    if _read(request_path, "T1_REVIEW_TASK_RECEIPT_INVALID") != request:
        _fail("T1_REVIEW_TASK_RECEIPT_INVALID", "request differs")
    expected_output = {
        "schema_version": "1.0",
        "stage": "T1",
        "review_kind": request["review_kind"],
        "review_protocol": request["review_protocol"],
        "task_id": receipt["task_id"],
        "producer_thread_id": request["producer_thread_id"],
        "reviewer_thread_id": reviewer_thread_id,
        "candidate_sha256": request["candidate_sha256"],
        "candidate": copy.deepcopy(dict(candidate_reference)),
        "request": copy.deepcopy(dict(request_reference)),
        "verdict_payload": copy.deepcopy(dict(verdict_payload)),
    }
    output = _read(output_path, "T1_REVIEW_TASK_RECEIPT_INVALID")
    if output != expected_output or receipt["output_sha256"] != rt.canonical_sha256(output):
        _fail("T1_REVIEW_TASK_RECEIPT_INVALID", "task output differs")


def _normalize_plan_review(
    *, root: Path, request: Mapping[str, Any], reviewer_thread_id: str,
    review: Mapping[str, Any], request_reference: Mapping[str, str],
    candidate_reference: Mapping[str, str],
) -> dict[str, Any]:
    if not reviewer_thread_id or reviewer_thread_id == request["producer_thread_id"]:
        _fail("T1_PLAN_REVIEW_THREAD_INVALID", reviewer_thread_id)
    if set(review) != {"claim_verdicts", "findings", "reviewer_task_receipt"}:
        _fail("T1_PLAN_REVIEW_INVALID", "review fields")
    verdicts = review["claim_verdicts"]
    findings = review["findings"]
    receipt = review["reviewer_task_receipt"]
    _validate_t1_reviewer_task_receipt(
        root=root,
        request=request,
        reviewer_thread_id=reviewer_thread_id,
        receipt=receipt,
        verdict_payload={"claim_verdicts": verdicts, "findings": findings},
        candidate_reference=candidate_reference,
        request_reference=request_reference,
    )
    if not isinstance(verdicts, list) or not isinstance(findings, list):
        _fail("T1_PLAN_REVIEW_INVALID", "review arrays")
    observed: list[str] = []
    for item in verdicts:
        if not isinstance(item, Mapping) or set(item) != {"claim_id", "verdict", "rationale"}:
            _fail("T1_PLAN_REVIEW_INVALID", "claim verdict")
        if item["verdict"] not in {"pass", "fail"} or not isinstance(item["rationale"], str) or not item["rationale"].strip():
            _fail("T1_PLAN_REVIEW_INVALID", str(item.get("claim_id")))
        observed.append(item["claim_id"])
    planned = request["planned_claim_ids"]
    if len(observed) != len(set(observed)) or set(observed) != set(planned):
        _fail("T1_PLAN_REVIEW_COVERAGE_MISMATCH", "claims")
    for item in findings:
        if not isinstance(item, Mapping) or set(item) != {"id", "severity", "claim_ids", "message"}:
            _fail("T1_PLAN_REVIEW_INVALID", "finding")
        if item["severity"] not in {"blocking", "advisory"} or not set(item["claim_ids"]).issubset(planned) or not str(item["message"]).strip():
            _fail("T1_PLAN_REVIEW_INVALID", str(item.get("id")))
    overall = "pass"
    if any(item["verdict"] != "pass" for item in verdicts) or any(item["severity"] == "blocking" for item in findings):
        overall = "fail"
    return {
        "schema_version": "1.0",
        "stage": "T1",
        "review_kind": request["review_kind"],
        "review_protocol": request["review_protocol"],
        "run_id": request["run_id"],
        "session_id": request["session_id"],
        "candidate_sha256": request["candidate_sha256"],
        "request": copy.deepcopy(dict(request_reference)),
        "reviewer_thread_id": reviewer_thread_id,
        "reviewer_task_receipt": copy.deepcopy(dict(receipt)),
        "planned_claim_ids": copy.deepcopy(planned),
        "covered_claim_ids": sorted(observed),
        "claim_verdicts": copy.deepcopy(verdicts),
        "findings": copy.deepcopy(findings),
        "verdict": overall,
    }


def submit_t1_plan_semantic_review(
    workspace: str | Path, *, candidate_sha256: str, review: Mapping[str, Any]
) -> dict[str, str]:
    root = Path(workspace).resolve()
    candidate_path, request_path, task_output_path, review_path, validation_path, manifest_path = (
        _plan_review_paths(root, candidate_sha256)
    )
    if review_path.exists() or validation_path.exists() or manifest_path.exists():
        _fail("T1_PLAN_REVIEW_EXISTS", str(review_path.parent))
    request = _read(request_path, "T1_PLAN_REVIEW_INVALID")
    candidate = _read(candidate_path, "T1_PLAN_REVIEW_INVALID")
    if (
        request.get("candidate_sha256") != candidate_sha256
        or rt.canonical_sha256(candidate) != candidate_sha256
    ):
        _fail("T1_PLAN_REVIEW_INVALID", "candidate hash")
    reviewer = os.environ.get("CODEX_THREAD_ID", "").strip()
    record = _normalize_plan_review(
        root=root,
        request=request,
        reviewer_thread_id=reviewer,
        review=review,
        request_reference=rt.artifact_reference(request_path, root=root),
        candidate_reference=rt.artifact_reference(candidate_path, root=root),
    )
    _write(review_path, record)
    validation = {
        "schema_version": "1.0",
        "stage": "T1",
        "review_kind": request["review_kind"],
        "review_protocol": T1_PLAN_REVIEW_PROTOCOL,
        "candidate_sha256": candidate_sha256,
        "verdict": record["verdict"],
        "candidate": rt.artifact_reference(candidate_path, root=root),
        "request": rt.artifact_reference(request_path, root=root),
        "review_task_output": rt.artifact_reference(task_output_path, root=root),
        "review": rt.artifact_reference(review_path, root=root),
        "planned_claim_ids": record["planned_claim_ids"],
        "covered_claim_ids": record["covered_claim_ids"],
    }
    _write(validation_path, validation)
    files = [
        rt.artifact_reference(path, root=review_path.parent)
        for path in (candidate_path, request_path, task_output_path, review_path, validation_path)
    ]
    manifest = {
        "schema_version": "1.0",
        "stage": "T1",
        "review_kind": request["review_kind"],
        "review_protocol": T1_PLAN_REVIEW_PROTOCOL,
        "candidate_sha256": candidate_sha256,
        "files": files,
        "validation": rt.artifact_reference(validation_path, root=review_path.parent),
        "verdict": record["verdict"],
    }
    _write(manifest_path, manifest)
    return rt.artifact_reference(manifest_path, root=root)


def _validated_plan_review(
    root: Path, *, session: Mapping[str, Any], payload: Mapping[str, Any]
) -> dict[str, str]:
    expected_request = _expected_plan_review_request(root, session=session, payload=payload)
    candidate_path, request_path, task_output_path, review_path, validation_path, manifest_path = (
        _plan_review_paths(root, expected_request["candidate_sha256"])
    )
    if (
        _read(candidate_path, "T1_PLAN_REVIEW_MISSING") != payload
        or rt.canonical_sha256(payload) != expected_request["candidate_sha256"]
    ):
        _fail("T1_PLAN_REVIEW_STALE", expected_request["candidate_sha256"])
    request = _read(request_path, "T1_PLAN_REVIEW_MISSING")
    if request != expected_request:
        _fail("T1_PLAN_REVIEW_STALE", expected_request["candidate_sha256"])
    record = _read(review_path, "T1_PLAN_REVIEW_MISSING")
    expected_record = _normalize_plan_review(
        root=root,
        request=request,
        reviewer_thread_id=record.get("reviewer_thread_id", ""),
        review={
            "claim_verdicts": record.get("claim_verdicts"),
            "findings": record.get("findings"),
            "reviewer_task_receipt": record.get("reviewer_task_receipt"),
        },
        request_reference=rt.artifact_reference(request_path, root=root),
        candidate_reference=rt.artifact_reference(candidate_path, root=root),
    )
    if record != expected_record or record["verdict"] != "pass":
        _fail("T1_PLAN_REVIEW_REJECTED", expected_request["candidate_sha256"])
    expected_validation = {
        "schema_version": "1.0", "stage": "T1",
        "review_kind": request["review_kind"],
        "review_protocol": T1_PLAN_REVIEW_PROTOCOL,
        "candidate_sha256": expected_request["candidate_sha256"], "verdict": "pass",
        "candidate": rt.artifact_reference(candidate_path, root=root),
        "request": rt.artifact_reference(request_path, root=root),
        "review_task_output": rt.artifact_reference(task_output_path, root=root),
        "review": rt.artifact_reference(review_path, root=root),
        "planned_claim_ids": record["planned_claim_ids"], "covered_claim_ids": record["covered_claim_ids"],
    }
    if _read(validation_path, "T1_PLAN_REVIEW_INVALID") != expected_validation:
        _fail("T1_PLAN_REVIEW_INVALID", "validation")
    expected_manifest = {
        "schema_version": "1.0", "stage": "T1",
        "review_kind": request["review_kind"],
        "review_protocol": T1_PLAN_REVIEW_PROTOCOL,
        "candidate_sha256": expected_request["candidate_sha256"],
        "files": [
            rt.artifact_reference(path, root=review_path.parent)
            for path in (candidate_path, request_path, task_output_path, review_path, validation_path)
        ],
        "validation": rt.artifact_reference(validation_path, root=review_path.parent), "verdict": "pass",
    }
    if _read(manifest_path, "T1_PLAN_REVIEW_INVALID") != expected_manifest:
        _fail("T1_PLAN_REVIEW_INVALID", "manifest")
    return rt.artifact_reference(manifest_path, root=root)


def submit_t1_phase(
    workspace: str | Path,
    *,
    baseline_package: str | Path,
    storyline_package: str | Path,
    world_package: str | Path,
    environment_package: str | Path,
    input_gate: Any,
    phase: str,
    payload: Mapping[str, Any],
    runtime: Any | None = None,
) -> dict[str, str]:
    root = Path(workspace).resolve()
    contract_runtime = runtime or rt.ContractRuntime()
    session, baseline, storyline, world, environment, controls = _validated_session(
        root,
        baseline_package=baseline_package,
        storyline_package=storyline_package,
        world_package=world_package,
        environment_package=environment_package,
        input_gate=input_gate,
        runtime=contract_runtime,
        full_validation=False,
    )
    completed: list[str] = []
    for index, item in enumerate(PHASES, 1):
        if (
            root / "generation-evidence" / f"{index:02d}-{item}.json"
        ).is_file():
            completed.append(item)
        else:
            break
    if len(completed) >= len(PHASES):
        _fail("T1_PHASE_ORDER_INVALID", "all phases already sealed")
    if phase not in PHASES or phase != PHASES[len(completed)]:
        _fail("T1_PHASE_ORDER_INVALID", f"next phase is {PHASES[len(completed)]}")
    body = copy.deepcopy(dict(payload))
    if set(body) != set(PHASE_FIELDS[phase]):
        _fail(
            "T1_PHASE_PAYLOAD_INVALID",
            f"{phase} must contain exactly {list(PHASE_FIELDS[phase])}",
        )
    semantic_review_reference = None
    if phase == "event-demand-scan":
        if body["event_demands"] != storyline["event_requirements"]:
            _fail("T1_DEMAND_PROJECTION_MISMATCH", "P1 event demands")
        try:
            t1_contract_25.validate_p1_digests(
                body,
                environment,
                source_path="sources/E1/environment-system.json",
                source_sha256=next(
                    item["sha256"] for item in session["source_artifacts"]
                    if item["path"] == "sources/E1/environment-system.json"
                ),
                canonical_sha256=rt.canonical_sha256,
            )
        except t1_contract_25.Contract25Error as error:
            _fail(error.code, str(error))
    if phase == "global-timeline":
        try:
            t1_contract_25.validate_p2_plan(
                body,
                storyline,
                environment,
                rt.canonical_sha256,
                sealed_value=lambda origin: _sealed_initial_value_from_packages(
                    origin,
                    baseline_package=baseline_package,
                    storyline_package=storyline_package,
                    world_package=world_package,
                    environment_package=environment_package,
                ),
            )
        except t1_contract_25.Contract25Error as error:
            _fail(error.code, str(error))
        semantic_review_reference = _validated_plan_review(
            root, session=session, payload=body
        )
    if phase == "event-and-causality-model":
        plan = _sealed_phase_payload(root, sequence=2, phase="global-timeline")
        provisional = {**copy.deepcopy(plan), **copy.deepcopy(body)}
        try:
            t1_contract_25.validate_p3_exact(plan, provisional)
        except t1_contract_25.Contract25Error as error:
            _fail(error.code, str(error))
    if phase == "cross-line-state-test":
        provisional_model = {
            "schema_version": CURRENT_MODEL_SCHEMA_VERSION,
            "skill": "novel-event-timeline-designer",
            "stage": "T1",
            "run_id": session["run_id"],
            "status": "ready",
            "input_gate": copy.deepcopy(session["input_gate"]),
            "source_artifacts": copy.deepcopy(session["source_artifacts"]),
            **copy.deepcopy(
                _sealed_phase_payload(
                    root, sequence=1, phase="event-demand-scan"
                )
            ),
            **copy.deepcopy(
                _sealed_phase_payload(root, sequence=2, phase="global-timeline")
            ),
            **copy.deepcopy(
                _sealed_phase_payload(
                    root, sequence=3, phase="event-and-causality-model"
                )
            ),
            **copy.deepcopy(body),
        }
        _validate_phase_chain(
            root / "generation-evidence",
            session=session,
            model=provisional_model,
            through=3,
        )
        _validate_model(
            provisional_model,
            baseline,
            storyline,
            world,
            environment,
            controls,
            contract_runtime,
            expected_gate=input_gate.reference,
            expected_sources=session["source_artifacts"],
            sealed_value=lambda origin: _sealed_initial_value_from_packages(
                origin,
                baseline_package=baseline_package,
                storyline_package=storyline_package,
                world_package=world_package,
                environment_package=environment_package,
            ),
        )
    if phase == "final-event-model":
        model = body.get("model")
        if not isinstance(model, Mapping):
            _fail("T1_PHASE_PAYLOAD_INVALID", "final model missing")
        _require_generation_schema(model)
        _validate_phase_chain(
            root / "generation-evidence",
            session=session,
            model=model,
            through=4,
        )
        _validate_model(
            model,
            baseline,
            storyline,
            world,
            environment,
            controls,
            contract_runtime,
            expected_gate=input_gate.reference,
            expected_sources=session["source_artifacts"],
            sealed_value=lambda origin: _sealed_initial_value_from_packages(
                origin,
                baseline_package=baseline_package,
                storyline_package=storyline_package,
                world_package=world_package,
                environment_package=environment_package,
            ),
        )
    previous = None
    if completed:
        previous = rt.sha256_file(
            root
            / "generation-evidence"
            / f"{len(completed):02d}-{completed[-1]}.json"
        )
    evidence = {
        "schema_version": "2.0",
        **{
            key: copy.deepcopy(session[key])
            for key in (
                "run_id",
                "session_id",
                "thread_id",
                "input_gate",
                "state_before",
                "baseline_completion",
                "upstream_completions",
                "source_artifacts",
                "upstream_package_bindings",
                "e1_semantic_review_bindings",
                "control_bindings",
                "storyline_bindings",
                "event_requirement_bindings",
                "storyline_connection_bindings",
                "storyline_state_bindings",
                "world_rule_bindings",
                "environment_bindings",
                "affordance_bindings",
                "implementation_bindings",
                "plan_review_protocol",
            )
        },
        "stage": "T1",
        "phase": phase,
        "sequence": len(completed) + 1,
        "previous_evidence_sha256": previous,
        "payload": body,
        "payload_sha256": rt.canonical_sha256(body),
    }
    if semantic_review_reference is not None:
        evidence["semantic_review"] = semantic_review_reference
    path = (
        root
        / "generation-evidence"
        / f"{len(completed)+1:02d}-{phase}.json"
    )
    _write(path, evidence)
    return rt.artifact_reference(path, root=root)


def _validate_phase_chain(
    evidence_root: Path,
    *,
    session: Mapping[str, Any],
    model: Mapping[str, Any],
    phase_fields: Mapping[str, Sequence[str]] = PHASE_FIELDS,
    through: int | None = None,
) -> list[Path]:
    paths: list[Path] = []
    previous = None
    shared = [
        "run_id",
        "session_id",
        "thread_id",
        "input_gate",
        "state_before",
        "baseline_completion",
        "upstream_completions",
        "source_artifacts",
        "control_bindings",
        "storyline_bindings",
        "event_requirement_bindings",
        "storyline_connection_bindings",
        "storyline_state_bindings",
        "world_rule_bindings",
        "environment_bindings",
        "affordance_bindings",
    ]
    for current_only in (
        "upstream_package_bindings",
        "e1_semantic_review_bindings",
        "implementation_bindings",
        "plan_review_protocol",
    ):
        if current_only in session:
            shared.append(current_only)
    phase_sequence = PHASES if through is None else PHASES[:through]
    for index, phase in enumerate(phase_sequence, 1):
        path = evidence_root / f"{index:02d}-{phase}.json"
        evidence = _read(path, "T1_EVIDENCE_MISSING")
        payload = evidence.get("payload")
        if not isinstance(payload, Mapping):
            _fail("T1_EVIDENCE_INVALID", phase)
        expected = {
            "schema_version": "2.0",
            **{key: copy.deepcopy(session[key]) for key in shared},
            "stage": "T1",
            "phase": phase,
            "sequence": index,
            "previous_evidence_sha256": previous,
            "payload": dict(payload),
            "payload_sha256": rt.canonical_sha256(payload),
        }
        if phase == "global-timeline" and model.get("schema_version") == CURRENT_MODEL_SCHEMA_VERSION:
            expected["semantic_review"] = _validated_plan_review(
                evidence_root.parent, session=session, payload=payload
            )
        if evidence != expected or set(payload) != set(phase_fields[phase]):
            _fail("T1_EVIDENCE_INVALID", phase)
        if phase == "final-event-model":
            if payload["model"] != model:
                _fail("T1_EVIDENCE_MODEL_MISMATCH", phase)
        else:
            for field in phase_fields[phase]:
                if payload[field] != model[field]:
                    _fail("T1_EVIDENCE_MODEL_MISMATCH", f"{phase}.{field}")
        previous = rt.sha256_file(path)
        paths.append(path)
    return paths


def _validation(run_id: str) -> dict[str, Any]:
    return {
        "schema_version": "2.0",
        "run_id": run_id,
        "stage": "T1",
        "verdict": "ready",
        "checks": [
            "schema",
            "B0/S1/W1/E1/gate-lineage",
            "E1-universe-capability-occurrence-digests",
            "event-demand-exact-projection",
            "initial-anchor-option-and-plan-review-closure",
            "planned-event-transition-milestone-connection-obligation-closure",
            "capability-occurrence-and-authority-instance-closure",
            "typed-lifecycle-effective-time-and-single-use-consumption-closure",
            "P2-to-P3-exact-realization",
            "storyline-chain-and-state-closure",
            "causal-DAG-and-world-time-closure",
            "connection-and-timing-closure",
            "environment-affordance-closure",
            "state-resource-authority-information-disclosure-ledgers",
            "downstream-boundary",
            "completion-binding",
        ],
        "errors": [],
    }


def _historical_validation_2_0(run_id: str) -> dict[str, Any]:
    """Exact validation receipt shape emitted by the trusted 2.0 release."""

    return {
        "schema_version": "2.0",
        "run_id": run_id,
        "stage": "T1",
        "verdict": "ready",
        "checks": [
            "schema",
            "B0/S1/W1/E1/gate-lineage",
            "event-demand-exact-projection",
            "storyline-chain-and-state-closure",
            "causal-DAG-and-world-time-closure",
            "connection-and-timing-closure",
            "environment-affordance-closure",
            "state-resource-authority-information-ledgers",
            "downstream-boundary",
            "completion-binding",
        ],
        "errors": [],
    }


def _check_package_boundary(root: Path) -> None:
    allowed_evidence = {
        f"generation-evidence/{index:02d}-{phase}.json"
        for index, phase in enumerate(PHASES, 1)
    }
    execution = _read(root / "execution-record.json", "T1_EXECUTION_INVALID")
    allowed_implementation = {
        f"implementation/{item['identity']}"
        for item in execution.get("implementation_catalog", [])
        if isinstance(item, Mapping) and isinstance(item.get("identity"), str)
    }
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        if relative in _ALLOWED_ROOT_FILES:
            continue
        if relative in allowed_evidence or relative in allowed_implementation:
            continue
        if relative.startswith("semantic-reviews/"):
            parts = PurePosixPath(relative).parts
            if (
                len(parts) == 4
                and parts[1] == T1_PLAN_REVIEW_PROTOCOL
                and _HEX64.fullmatch(parts[2]) is not None
                and parts[3]
                in {"candidate.json", "request.json", "review-task-output.json", "review.json", "validation.json", "package-manifest.json"}
            ):
                continue
            _fail("T1_BOUNDARY_VIOLATION", relative)
        if any(relative.startswith(prefix) for prefix in _ALLOWED_SOURCE_PREFIXES):
            continue
        _fail("T1_BOUNDARY_VIOLATION", relative)


def validate_t1_package(
    package_root: str | Path,
    *,
    runtime: Any | None = None,
    require_completion: bool = True,
) -> dict[str, Any]:
    root = Path(package_root).resolve()
    contract_runtime = runtime or rt.ContractRuntime()
    _check_package_boundary(root)
    model = _read(root / "event-timeline.json", "T1_MODEL_MISSING")
    current_model = _is_current_model(model)
    manifest = _read(root / "package-manifest.json", "T1_MANIFEST_INVALID")
    stored = _read(root / "validation.json", "T1_VALIDATION_MISSING")
    try:
        contract_runtime.validate(manifest, "package-manifest.schema.json")
        rt.verify_manifest_integrity(manifest, root=root)
    except Exception as error:
        _fail("T1_MANIFEST_INVALID", str(error))
    execution = _read(root / "execution-record.json", "T1_EXECUTION_INVALID")
    catalog = {
        item["identity"]: item["artifact"]
        for item in execution.get("implementation_catalog", [])
    }
    identity_mode = "pre-versioned-model"
    if current_model:
        try:
            identity_mode, catalog = stage_identity.validate_stage_catalog(
                stage="T1",
                records=execution.get("implementation_catalog"),
                package_root=root,
                current_paths=_implementation_paths(),
                verify_artifact_reference=rt.verify_artifact_reference,
                sha256_file=rt.sha256_file,
            )
        except stage_identity.StageImplementationIdentityError as error:
            _fail("T1_IMPLEMENTATION_STALE", str(error))
    if not current_model:
        _validate_trusted_legacy_model_schema(root, model, catalog)
    b0 = root / "sources" / "B0"
    s1 = root / "sources" / "S1"
    w1 = root / "sources" / "W1"
    e1 = root / "sources" / "E1"
    if current_model:
        try:
            rt.validate_baseline_package(b0, runtime=contract_runtime)
            s1_runtime.validate_s1_package(s1, runtime=contract_runtime)
            w1_runtime.validate_w1_package(w1, runtime=contract_runtime)
            e1_runtime.validate_e1_package(e1, runtime=contract_runtime)
        except Exception as error:
            _fail("T1_UPSTREAM_INVALID", str(error))
    else:
        for stage, canonical_name in (
            ("B0", "author-control-baseline.json"),
            ("S1", "storyline-architecture.json"),
            ("W1", "world-model.json"),
            ("E1", "environment-system.json"),
        ):
            _validate_legacy_upstream_snapshot(
                root / "sources" / stage,
                stage=stage,
                canonical_name=canonical_name,
                runtime=contract_runtime,
            )
    baseline = _read(b0 / "author-control-baseline.json", "T1_B0_INVALID")
    storyline = _read(s1 / "storyline-architecture.json", "T1_S1_INVALID")
    world = _read(w1 / "world-model.json", "T1_W1_INVALID")
    environment = _read(e1 / "environment-system.json", "T1_E1_INVALID")
    controls = _controls(b0, baseline)
    gate = _read(root / "input-gate.json", "T1_GATE_MISSING")
    try:
        contract_runtime.validate(gate, "input-gate.schema.json")
    except Exception as error:
        _fail("T1_GATE_INVALID", str(error))
    if rt.canonical_sha256(gate) != rt.sha256_file(root / "input-gate.json"):
        _fail("T1_GATE_INVALID", "stored gate is not canonical")
    gate_ref = {
        "path": model["input_gate"]["path"],
        "sha256": rt.sha256_file(root / "input-gate.json"),
    }
    if not gate_ref["path"].endswith("/input-gate.json"):
        _fail("T1_GATE_REFERENCE_MISMATCH", "gate path not package-qualified")
    if current_model:
        sealed_b0 = gate.get("baseline_completion")
        sealed_upstreams = gate.get("upstream_completions")
        if (
            not isinstance(sealed_b0, Mapping)
            or not isinstance(sealed_upstreams, list)
            or len(sealed_upstreams) != 3
            or any(not isinstance(item, Mapping) for item in sealed_upstreams)
        ):
            _fail(
                "T1_GATE_INVALID",
                "gate does not select exactly B0, S1, W1, and E1",
            )
        b0_ref = _sealed_upstream_reference(
            b0,
            sealed_b0,
            stage="B0",
            run_id=model["run_id"],
            previous_stage_completions=[],
            runtime=contract_runtime,
        )
        s1_ref = _sealed_upstream_reference(
            s1,
            sealed_upstreams[0],
            stage="S1",
            run_id=model["run_id"],
            previous_stage_completions=[],
            runtime=contract_runtime,
        )
        w1_ref = _sealed_upstream_reference(
            w1,
            sealed_upstreams[1],
            stage="W1",
            run_id=model["run_id"],
            previous_stage_completions=[s1_ref],
            runtime=contract_runtime,
        )
        e1_ref = _sealed_upstream_reference(
            e1,
            sealed_upstreams[2],
            stage="E1",
            run_id=model["run_id"],
            previous_stage_completions=[s1_ref, w1_ref],
            runtime=contract_runtime,
        )
        for path, expected in (
            (s1 / "sources" / "B0" / "stage-completion.json", b0_ref),
            (w1 / "sources" / "B0" / "stage-completion.json", b0_ref),
            (w1 / "sources" / "S1" / "stage-completion.json", s1_ref),
            (e1 / "sources" / "B0" / "stage-completion.json", b0_ref),
            (e1 / "sources" / "S1" / "stage-completion.json", s1_ref),
            (e1 / "sources" / "W1" / "stage-completion.json", w1_ref),
        ):
            _require_embedded_completion(
                path, expected, code="T1_UPSTREAM_LINEAGE_MISMATCH"
            )
    else:
        b0_ref = _stage_reference(b0, "B0")
        s1_ref = _stage_reference(s1, "S1")
        w1_ref = _stage_reference(w1, "W1")
        e1_ref = _stage_reference(e1, "E1")
    if (
        gate.get("target_stage") != "T1"
        or gate.get("run_id") != model["run_id"]
        or gate.get("baseline_completion") != b0_ref
        or gate.get("upstream_completions") != [s1_ref, w1_ref, e1_ref]
    ):
        _fail("T1_GATE_INVALID", "stored T1 topology is invalid")
    expected_sources = _source_artifacts(b0, s1, w1, e1)
    if current_model:
        _validate_model(
            model,
            baseline,
            storyline,
            world,
            environment,
            controls,
            contract_runtime,
            expected_gate=gate_ref,
            expected_sources=expected_sources,
            sealed_value=lambda origin: _sealed_initial_value(root, origin),
        )
    elif (
        model.get("stage") != "T1"
        or model.get("status") != "ready"
        or model.get("input_gate") != gate_ref
        or model.get("source_artifacts") != expected_sources
    ):
        _fail(
            "T1_LEGACY_MODEL_BINDING_INVALID",
            "trusted legacy canonical is not bound to its gate and source snapshot",
        )
    if manifest["artifact_roles"]["canonical"] != rt.artifact_reference(
        root / "event-timeline.json", root=root
    ):
        _fail("T1_MANIFEST_INVALID", "canonical role is stale")
    if (
        execution.get("input_gate") != gate_ref
        or execution.get("baseline_completion") != b0_ref
        or execution.get("upstream_completions") != [s1_ref, w1_ref, e1_ref]
        or execution.get("output_sha256") != rt.canonical_sha256(model)
    ):
        _fail("T1_EXECUTION_INVALID", "execution lineage is stale")
    session = _read(root / "generation-session.json", "T1_SESSION_INVALID")
    thread = session.get("thread_id")
    if not isinstance(thread, str) or not thread.strip():
        _fail("T1_SESSION_INVALID", "thread is missing")
    expected_session = {
        "schema_version": "2.0",
        "run_id": model["run_id"],
        "stage": "T1",
        "session_id": _session_id(
            thread, gate_ref, b0_ref, s1_ref, w1_ref, e1_ref
        ),
        "thread_id": thread,
        "input_gate": gate_ref,
        "state_before": gate.get("run_state"),
        "baseline_completion": b0_ref,
        "upstream_completions": [s1_ref, w1_ref, e1_ref],
        "source_artifacts": expected_sources,
        "control_bindings": _control_bindings(controls),
        "storyline_bindings": _object_bindings(
            storyline["storylines"], extra="type"
        ),
        "event_requirement_bindings": _object_bindings(
            storyline["event_requirements"], extra="target_stage"
        ),
        "storyline_connection_bindings": _object_bindings(
            storyline["connections"], extra="type"
        ),
        "storyline_state_bindings": [
            {
                "id": item["id"],
                "value_sha256": rt.canonical_sha256(
                    [
                        item["start_state"],
                        *item["state_changes"],
                        item["end_state"],
                    ]
                ),
            }
            for item in storyline["storylines"]
        ],
        "world_rule_bindings": _object_bindings(
            [
                *world["world_facts"],
                *world["systems"],
                *world["institutions"],
                *world["resource_flows"],
                *world["authority_flows"],
            ]
        ),
        "environment_bindings": _object_bindings(
            environment["environments"]
        ),
        "affordance_bindings": _object_bindings(
            environment["event_affordance_catalog"]
        ),
        "phases": list(PHASES),
    }
    if current_model:
        expected_session["implementation_bindings"] = (
            _implementation_bindings()
            if identity_mode
            == stage_identity.STAGE_IMPLEMENTATION_IDENTITY_CONTRACT_VERSION
            else [
                {"identity": identity, "sha256": reference["sha256"]}
                for identity, reference in sorted(catalog.items())
            ]
        )
        expected_session["plan_review_protocol"] = T1_PLAN_REVIEW_PROTOCOL
        expected_session["upstream_package_bindings"] = _upstream_package_bindings(
            b0, s1, w1, e1
        )
        expected_session["e1_semantic_review_bindings"] = _e1_semantic_review_bindings(e1)
    if session != expected_session:
        _fail("T1_SESSION_INVALID", "session differs from current inputs")
    if execution.get("session_id") != session["session_id"]:
        _fail("T1_SESSION_INVALID", "execution session differs")
    evidence_paths = _validate_phase_chain(
        root / "generation-evidence",
        session=session,
        model=model,
        phase_fields=(
            PHASE_FIELDS
            if current_model
            else _LEGACY_PHASE_FIELDS_2_1
            if model.get("schema_version") == "2.1"
            else _LEGACY_PHASE_FIELDS_2_0
        ),
    )
    evidence_index = _read(
        root / "generation-evidence-index.json", "T1_EVIDENCE_INVALID"
    )
    if evidence_index != {
        "schema_version": "2.0",
        "run_id": model["run_id"],
        "stage": "T1",
        "session_id": session["session_id"],
        "phases": list(PHASES),
        "evidence": [
            rt.artifact_reference(path, root=root) for path in evidence_paths
        ],
    }:
        _fail("T1_EVIDENCE_INVALID", "evidence index is stale")
    implementation_identities = set(catalog)
    expected_implementation_refs = {
        rt.canonical_json(
            rt.artifact_reference(
                root / "implementation" / identity,
                root=root,
            )
        )
        for identity in implementation_identities
    }
    if (
        set(catalog) != implementation_identities
        or {
            rt.canonical_json(item)
            for item in execution.get("implementation", [])
        }
        != expected_implementation_refs
        or {
            rt.canonical_json(item) for item in manifest.get("implementation", [])
        }
        != expected_implementation_refs
        or {
            rt.canonical_json(item) for item in catalog.values()
        }
        != expected_implementation_refs
    ):
        _fail(
            "T1_IMPLEMENTATION_STALE",
            "implementation files, catalog, execution, and manifest differ",
        )
    if require_completion:
        completion = _read(
            root / "stage-completion.json", "T1_COMPLETION_MISSING"
        )
        try:
            contract_runtime.validate(completion, "stage-completion.schema.json")
        except Exception as error:
            _fail("T1_COMPLETION_INVALID", str(error))
        manifest_ref = completion.get("manifest")
        manifest_path = (
            manifest_ref.get("path") if isinstance(manifest_ref, Mapping) else ""
        )
        prefix = PurePosixPath(manifest_path).parent.as_posix()
        if (
            not (prefix == "T1" or prefix.startswith("T1/"))
            or completion.get("run_id") != model["run_id"]
            or completion.get("stage") != "T1"
            or completion.get("status") != "ready"
            or completion.get("session_id") != session["session_id"]
            or completion.get("manifest")
            != {
                "path": _logical(prefix, "package-manifest.json"),
                "sha256": rt.sha256_file(root / "package-manifest.json"),
            }
            or completion.get("validation")
            != {
                "path": _logical(prefix, "validation.json"),
                "sha256": rt.sha256_file(root / "validation.json"),
            }
            or completion.get("input_gate") != gate_ref
            or completion.get("state_before") != gate.get("run_state")
            or completion.get("previous_stage_completions")
            != [s1_ref, w1_ref, e1_ref]
            or completion.get("return_binding") != gate.get("return_binding")
        ):
            _fail("T1_COMPLETION_BINDING_MISMATCH", "completion lineage is stale")
    expected_validation = (
        _validation(model["run_id"])
        if current_model
        else _historical_validation_2_0(model["run_id"])
        if model.get("schema_version") == "2.0"
        else stored
    )
    if stored != expected_validation:
        _fail("T1_VALIDATION_STALE", "stored validation differs")
    return expected_validation


def run_t1(
    package_root: str | Path,
    *,
    baseline_package: str | Path,
    storyline_package: str | Path,
    world_package: str | Path,
    environment_package: str | Path,
    coordinator: Any,
    input_gate: Any,
    controlled_workspace: str | Path,
    logical_package_path: str = "T1",
    next_state_path: str,
    active_return_request: Any | None = None,
    runtime: Any | None = None,
) -> T1RunReceipt:
    destination = Path(package_root).resolve()
    if destination.exists():
        _fail("T1_OUTPUT_EXISTS", str(destination))
    if not os.environ.get("CODEX_THREAD_ID", "").strip():
        _fail("T1_THREAD_REQUIRED", "CODEX_THREAD_ID is required")
    contract_runtime = runtime or rt.ContractRuntime()
    workspace = Path(controlled_workspace).resolve()
    session, baseline, storyline, world, environment, controls = _validated_session(
        workspace,
        baseline_package=baseline_package,
        storyline_package=storyline_package,
        world_package=world_package,
        environment_package=environment_package,
        input_gate=input_gate,
        runtime=contract_runtime,
    )
    final = _read(
        workspace
        / "generation-evidence"
        / f"{len(PHASES):02d}-{PHASES[-1]}.json",
        "T1_EVIDENCE_MISSING",
    )
    payload = final.get("payload")
    if not isinstance(payload, Mapping) or not isinstance(
        payload.get("model"), Mapping
    ):
        _fail("T1_EVIDENCE_INVALID", "final model missing")
    model = copy.deepcopy(dict(payload["model"]))
    _require_generation_schema(model)
    _validate_phase_chain(
        workspace / "generation-evidence", session=session, model=model
    )
    _validate_model(
        model,
        baseline,
        storyline,
        world,
        environment,
        controls,
        contract_runtime,
        expected_gate=input_gate.reference,
        expected_sources=session["source_artifacts"],
        sealed_value=lambda origin: _sealed_initial_value_from_packages(
            origin,
            baseline_package=baseline_package,
            storyline_package=storyline_package,
            world_package=world_package,
            environment_package=environment_package,
        ),
    )

    destination.parent.mkdir(parents=True, exist_ok=True)
    temp_parent = Path(
        tempfile.mkdtemp(prefix=f".{destination.name}.", dir=destination.parent)
    )
    staging = temp_parent / "package"
    staging.mkdir()
    try:
        for stage, source in (
            ("B0", Path(baseline_package).resolve()),
            ("S1", Path(storyline_package).resolve()),
            ("W1", Path(world_package).resolve()),
            ("E1", Path(environment_package).resolve()),
        ):
            shutil.copytree(source, staging / "sources" / stage)
        _write(staging / "input-gate.json", input_gate.data)
        if _source_artifacts(
            staging / "sources" / "B0",
            staging / "sources" / "S1",
            staging / "sources" / "W1",
            staging / "sources" / "E1",
        ) != session["source_artifacts"]:
            _fail("T1_SOURCE_ARTIFACT_MISMATCH", "staged inputs changed")
        _write(staging / "event-timeline.json", model)
        evidence_refs = []
        for index, phase in enumerate(PHASES, 1):
            source = (
                workspace / "generation-evidence" / f"{index:02d}-{phase}.json"
            )
            target = staging / "generation-evidence" / source.name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            evidence_refs.append(rt.artifact_reference(target, root=staging))
        _write(
            staging / "generation-evidence-index.json",
            {
                "schema_version": "2.0",
                "run_id": baseline["run_id"],
                "stage": "T1",
                "session_id": session["session_id"],
                "phases": list(PHASES),
                "evidence": evidence_refs,
            },
        )
        _write(staging / "generation-session.json", session)
        p2_payload = _sealed_phase_payload(
            workspace, sequence=2, phase="global-timeline"
        )
        selected_review = _validated_plan_review(
            workspace, session=session, payload=p2_payload
        )
        selected_review_path = workspace / Path(
            *PurePosixPath(selected_review["path"]).parts
        )
        selected_review_root = selected_review_path.parent
        target_review_root = staging / selected_review_root.relative_to(workspace)
        target_review_root.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(selected_review_root, target_review_root)
        implementation_refs = []
        implementation_catalog = []
        for identity, source in sorted(_implementation_paths().items()):
            target = staging / "implementation" / identity
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            reference = rt.artifact_reference(target, root=staging)
            implementation_refs.append(reference)
            implementation_catalog.append(
                {"identity": identity, "artifact": reference}
            )
        execution = {
            "schema_version": "2.0",
            "run_id": baseline["run_id"],
            "stage": "T1",
            "operation": "controlled-event-timeline-generation",
            "session_id": session["session_id"],
            "input_gate": copy.deepcopy(input_gate.reference),
            "baseline_completion": session["baseline_completion"],
            "upstream_completions": session["upstream_completions"],
            "implementation": implementation_refs,
            "implementation_catalog": implementation_catalog,
            "output_sha256": rt.canonical_sha256(model),
        }
        _write(staging / "execution-record.json", execution)
        (staging / "event-preview.md").write_text(
            "# Event timeline\n\n"
            + "\n".join(
                f"- **{item['id']}** {item['world_time']}: "
                f"{item['responsibility']}"
                for item in model["major_events"]
            )
            + "\n",
            encoding="utf-8",
            newline="",
        )
        validation = _validation(baseline["run_id"])
        _write(staging / "validation.json", validation)
        files = [
            rt.artifact_reference(path, root=staging)
            for path in sorted(staging.rglob("*"), key=lambda item: item.as_posix())
            if path.is_file()
        ]
        by_path = {item["path"]: item for item in files}
        manifest = {
            "schema_version": "2.0",
            "run_id": baseline["run_id"],
            "stage": "T1",
            "package_profile": "generated-model",
            "verdict": "ready",
            "files": files,
            "artifact_roles": {
                "canonical": by_path["event-timeline.json"],
                "generation_session": by_path["generation-session.json"],
                "generation_evidence_index": by_path[
                    "generation-evidence-index.json"
                ],
                "execution_record": by_path["execution-record.json"],
                "preview": by_path["event-preview.md"],
            },
            "validation": by_path["validation.json"],
            "implementation": implementation_refs,
        }
        contract_runtime.validate(manifest, "package-manifest.schema.json")
        rt.verify_manifest_integrity(manifest, root=staging)
        _write(staging / "package-manifest.json", manifest)
        validate_t1_package(
            staging, runtime=contract_runtime, require_completion=False
        )
        completion_data = {
            "schema_version": "2.0",
            "run_id": baseline["run_id"],
            "stage": "T1",
            "status": "ready",
            "session_id": session["session_id"],
            "manifest": {
                "path": _logical(logical_package_path, "package-manifest.json"),
                "sha256": rt.sha256_file(staging / "package-manifest.json"),
            },
            "validation": {
                "path": _logical(logical_package_path, "validation.json"),
                "sha256": rt.sha256_file(staging / "validation.json"),
            },
            "input_gate": copy.deepcopy(input_gate.reference),
            "state_before": copy.deepcopy(input_gate.data["run_state"]),
            "previous_stage_completions": copy.deepcopy(
                input_gate.data["upstream_completions"]
            ),
            "return_binding": copy.deepcopy(input_gate.data["return_binding"]),
        }
        contract_runtime.validate(
            completion_data, "stage-completion.schema.json"
        )
        sealed = rt.seal_stage_document(
            completion_data,
            "T1",
            _logical(logical_package_path, "stage-completion.json"),
        )
        _write(staging / "stage-completion.json", sealed.data)
        validate_t1_package(staging, runtime=contract_runtime)
        transition = coordinator.accept_stage_completion(
            gate=input_gate,
            completion=sealed,
            next_state_path=next_state_path,
            active_return_request=active_return_request,
        )
        staging.replace(destination)
    except Exception:
        shutil.rmtree(temp_parent, ignore_errors=True)
        raise
    shutil.rmtree(temp_parent, ignore_errors=True)
    return T1RunReceipt(
        package_root=destination,
        model=copy.deepcopy(model),
        manifest=copy.deepcopy(manifest),
        completion=sealed,
        transition=transition,
    )


__all__ = [
    "PHASES",
    "PHASE_FIELDS",
    "CURRENT_MODEL_SCHEMA_VERSION",
    "LEGACY_MODEL_SCHEMA_VERSIONS",
    "T1_PLAN_REVIEW_PROTOCOL",
    "T1Error",
    "T1RunReceipt",
    "run_t1",
    "start_t1_session",
    "start_t1_plan_semantic_review",
    "seal_t1_review_task_output",
    "submit_t1_phase",
    "submit_t1_plan_semantic_review",
    "validate_t1_package",
]
