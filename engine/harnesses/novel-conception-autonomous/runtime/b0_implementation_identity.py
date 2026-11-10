"""Frozen B0 implementation-identity migration contract.

This module is part of every newly generated B0 implementation catalog.  A
historical package predating it may replay only through the exact catalog and
old-to-current validator hash pair registered here.
"""

from __future__ import annotations


B0_IMPLEMENTATION_IDENTITY_CONTRACT_VERSION = "1.0"
TRUSTED_LEGACY_IMPLEMENTATION_CATALOG_SHA256 = frozenset(
    {"98a67b0b3e2037f8729066bf31fc3421a1fe98e3d5ff76322f07593446799488"}
)
TRUSTED_LEGACY_MISSING_CURRENT_IDENTITIES = frozenset(
    {"runtime/b0_implementation_identity.py"}
)
TRUSTED_LEGACY_MISMATCH_BINDINGS = {
    "runtime/baseline.py": {
        "stored_sha256": "e9eb8603f16b374288a0f7b04aaa43c8a4d51dbfac97f7c064c1a39b37a6bf34",
        # This lives outside baseline.py to avoid self-hash recursion while
        # remaining catalog-bound for every new package.
        "approved_current_sha256": "51160603f780f7edf0014a04c3a0ca6ac11807a1a86e663624ce2feb1a194c0c",
    }
}


__all__ = [
    "B0_IMPLEMENTATION_IDENTITY_CONTRACT_VERSION",
    "TRUSTED_LEGACY_IMPLEMENTATION_CATALOG_SHA256",
    "TRUSTED_LEGACY_MISSING_CURRENT_IDENTITIES",
    "TRUSTED_LEGACY_MISMATCH_BINDINGS",
]
