"""Versioned implementation-identity boundary for conception stages.

An implementation catalog identifies the code, schemas, and review contracts
owned by the stage that produced it.  Upstream package validators authenticate
their own implementation when they are called; copying their source files into
every downstream catalog would make an unrelated upstream maintenance change
invalidate the entire chain.

Version 1 narrows that boundary.  The only pre-versioned catalogs accepted are
the exact, frozen run19 catalogs below.  Every stored artifact is still
verified, every retained identity must still equal the current implementation,
and the only shape change allowed is the explicit removed/missing mapping.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence


STAGE_IMPLEMENTATION_IDENTITY_CONTRACT_VERSION = "1.0"
IDENTITY_MODULE = "runtime/stage_implementation_identity.py"

TRUSTED_LEGACY_CATALOGS: dict[str, dict[str, Any]] = {
    "S1": {
        "canonical_digest": "1df651e9a8b8f551fe667e5ca505224eb8a1d6701e8c634b90760388f59615ac",
        "removed_identities": frozenset({"runtime/baseline.py"}),
        "approved_mismatches": {"skill/run_v2.py": ("9894a35e664a142e65ac440e8c37a6cf81ce46d1a78fdb55c1c77c6c8f4e4151", "b77818b31b87383fe74d1a3eb74a5c5ecc2bfacfdd6625b5e6ade845708645f4")},
    },
    "W1": {
        "canonical_digest": "31e449b2c1ba5aebb697739fd8dec8c7be01933b21eeee0f2b9a16ec955476c5",
        "removed_identities": frozenset(
            {
                "runtime/baseline.py",
                "schemas/author-control-baseline.schema.json",
                "schemas/storyline-architecture.schema.json",
                "upstream/S1-SKILL.md",
                "upstream/S1-run_v2.py",
                "upstream/S1-runtime-contract.md",
            }
        ),
        "approved_mismatches": {"skill/run_v2.py": ("f36b712eb8617745acf60487281cb2faa7566162f71e8cb788308cec641619f4", "11212c41ca68cb9f73b1a4e58433596a7273ee7dc406ea02c3c85c0ebe4d8963")},
    },
    "E1": {
        "canonical_digest": "827f050d9c13af99b4e95aa1402bc385c18df5541a6f4eb3e4433558992172ea",
        "removed_identities": frozenset(
            {
                "runtime/b0_completion.py",
                "runtime/baseline.py",
                "schemas/author-control-baseline.schema.json",
                "schemas/storyline-architecture.schema.json",
                "schemas/world-model.schema.json",
                "upstream/S1-run_v2.py",
                "upstream/S1-runtime-contract.md",
                "upstream/W1-run_v2.py",
                "upstream/W1-runtime-contract.md",
            }
        ),
        "approved_mismatches": {
            "skill/run_v2.py": ("b71ef6e750fab14cd552a288397a8e074e6cf27c598e7dbdfba55e20023c7c57", "ffb724de42314edd3e70bf2ca7133677b3374076024471b8c18b8949275ecf5f"),
            "skill/runtime-contract.md": ("d4027156b940dbc31392b681fd8ec9afb97c0e26fe9aeaad76e063735c5d3acc", "58eb7b036b1f87506d28d2fc29f8edf424c59189b3221396fe524f707ee1c9b4"),
        },
    },
    "T1": {
        "canonical_digest": "82c4340717606a0f3c18ec1febbcc23476c729a62d3ad76772fa4cd21ad50e03",
        "removed_identities": frozenset(
            {
                "runtime/b0_completion.py",
                "runtime/baseline.py",
                "schemas/author-control-baseline.schema.json",
                "schemas/environment-system.schema.json",
                "schemas/storyline-architecture.schema.json",
                "schemas/world-model.schema.json",
                "upstream/E1-run_v2.py",
                "upstream/E1-runtime-contract.md",
                "upstream/S1-run_v2.py",
                "upstream/S1-runtime-contract.md",
                "upstream/W1-run_v2.py",
                "upstream/W1-runtime-contract.md",
            }
        ),
        "approved_mismatches": {"skill/run_v2.py": ("ced8c8392848be03aad780cd71751db61073464b365f0a9fcde94dc1173535d6", "016effdd1110d8e64a9333f17ed014d1b418a148d70c0df212d94ac1fd784b9c")},
    },
    "C1": {
        "canonical_digest": "54f2fcc20863a7a85f7cb70278e9b1f77374cb9d529b7a0e40d2f1cbe5b579dc",
        "removed_identities": frozenset(
            {
                "runtime/b0_completion.py",
                "runtime/baseline.py",
                "schemas/author-control-baseline.schema.json",
                "schemas/environment-system.schema.json",
                "schemas/event-timeline.schema.json",
                "schemas/storyline-architecture.schema.json",
                "schemas/world-model.schema.json",
                "upstream/E1-run_v2.py",
                "upstream/E1-runtime-contract.md",
                "upstream/S1-run_v2.py",
                "upstream/S1-runtime-contract.md",
                "upstream/T1-run_v2.py",
                "upstream/T1-runtime-contract.md",
                "upstream/W1-run_v2.py",
                "upstream/W1-runtime-contract.md",
            }
        ),
        "approved_mismatches": {"skill/run_v2.py": ("57dbf857c81d73ed817f8dc7c55cedb7780877ae309b8a80c06a62ac2e0d4782", "34199c04abc04583f75ab991dd36597d92b3b3a33018f4df9981ab933f63c60c")},
    },
    "Q1": {
        "canonical_digest": "2b3b5c39b59076b25f49807b54486e0a083d81309fb39d8a5e205b4c6eac3227",
        "removed_identities": frozenset(
            {"workflow/conception-autonomous-workflow-v2.md"}
        ),
        "approved_mismatches": {"skill/run_v2.py": ("5c536d10037f5fd095c8094ac109e4dda4ae7bb450dd69f61752f0c731688dbb", "b04ceca7c955e9e06baa8e3612b625423653213ac567654db1508ff43b71c5ba")},
    },
    "P1": {
        "canonical_digest": "fa0126d9bf8fde833cfacc3020b2e912f587c9b0211cba104dbb60530b20f95f",
        "removed_identities": frozenset(),
        "approved_mismatches": {"skill/run_v2.py": ("e350bc3c9c47a64f27a38f78fe81f9ca91a08ce3a430ffab94b7821e420ea62a", "0e3f0cd729ca309309876bc7165f958d2ff71c6107d24b11bf9a43e22818084d")},
    },
}


class StageImplementationIdentityError(ValueError):
    """Raised when a package does not satisfy its stage identity boundary."""


def canonical_catalog_digest(records: Sequence[Mapping[str, Any]]) -> str:
    payload = json.dumps(
        records,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def migration_registry_digest() -> str:
    """Return one stable digest for the complete frozen migration registry."""

    normalized = {
        stage: {
            "canonical_digest": contract["canonical_digest"],
            "removed_identities": sorted(contract["removed_identities"]),
            "approved_mismatches": {
                name: {
                    "stored_sha256": pair[0],
                    "approved_current_sha256": pair[1],
                }
                for name, pair in sorted(
                    contract.get("approved_mismatches", {}).items()
                )
            },
        }
        for stage, contract in sorted(TRUSTED_LEGACY_CATALOGS.items())
    }
    return canonical_catalog_digest([normalized])


def validate_stage_catalog(
    *,
    stage: str,
    records: Any,
    package_root: Path,
    current_paths: Mapping[str, Path],
    verify_artifact_reference: Callable[..., Path],
    sha256_file: Callable[[Path], str],
) -> tuple[str, dict[str, Mapping[str, Any]]]:
    """Validate a current V1 catalog or one exact pre-versioned migration.

    The returned mode is either ``"1.0"`` or ``"legacy-run19"``.  Callers use
    the returned catalog identities when checking any mirrored manifest fields.
    """

    if not isinstance(records, list):
        raise StageImplementationIdentityError("catalog is not a list")
    catalog: dict[str, Mapping[str, Any]] = {}
    for item in records:
        if (
            not isinstance(item, Mapping)
            or set(item) != {"identity", "artifact"}
            or not isinstance(item.get("identity"), str)
            or not isinstance(item.get("artifact"), Mapping)
            or item["identity"] in catalog
        ):
            raise StageImplementationIdentityError("catalog shape is not exact")
        catalog[item["identity"]] = item["artifact"]

    current_identities = set(current_paths)
    if IDENTITY_MODULE not in current_identities:
        raise StageImplementationIdentityError("identity authority is unbound")

    mode = STAGE_IMPLEMENTATION_IDENTITY_CONTRACT_VERSION
    if set(catalog) != current_identities:
        legacy = TRUSTED_LEGACY_CATALOGS.get(stage)
        if (
            legacy is None
            or canonical_catalog_digest(records) != legacy["canonical_digest"]
            or set(catalog)
            != (current_identities - {IDENTITY_MODULE})
            | set(legacy["removed_identities"])
        ):
            raise StageImplementationIdentityError("catalog identity set differs")
        mode = "legacy-run19"

    for identity, reference in catalog.items():
        try:
            verify_artifact_reference(reference, root=package_root)
        except Exception as error:
            raise StageImplementationIdentityError(str(error)) from error

        current = current_paths.get(identity)
        if current is not None:
            stored_sha256 = reference.get("sha256")
            current_sha256 = sha256_file(current)
            if stored_sha256 != current_sha256:
                legacy = TRUSTED_LEGACY_CATALOGS.get(stage, {})
                approved = legacy.get("approved_mismatches", {}).get(identity)
                if mode != "legacy-run19" or approved != (
                    stored_sha256,
                    current_sha256,
                ):
                    raise StageImplementationIdentityError(
                        f"current implementation differs: {identity}"
                    )

    return mode, catalog


__all__ = [
    "IDENTITY_MODULE",
    "STAGE_IMPLEMENTATION_IDENTITY_CONTRACT_VERSION",
    "StageImplementationIdentityError",
    "TRUSTED_LEGACY_CATALOGS",
    "canonical_catalog_digest",
    "migration_registry_digest",
    "validate_stage_catalog",
]
