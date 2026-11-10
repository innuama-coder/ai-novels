# Portable core contract

This directory is the runtime-independent source of HLD orchestration meaning. Runtime adapters may translate task creation, filesystem access and external author events, but may not change stage order, input topology, result algebra, source-access policy, package profiles, pass bars or unsupported-runtime claims.

The executable core is split into:

- `runtime/contracts.py`: frozen stage, owner, source-access and package-profile tables;
- `runtime/canonical.py`: canonical JSON, SHA-256, safe paths and artifact references;
- `runtime/state.py`: immutable initial/successor state construction;
- `runtime/hdd.py`: deterministic unresolved projections and coverage aggregation;
- `runtime/revision.py`: immutable revision plans, append-only plan states and fingerprints;
- `runtime/author_gate.py`: source-resolution and retarget transactions;
- `runtime/package_envelope.py`: exact content-package and result-envelope validation;
- `runtime/router.py`: the sole result consumer and transition decision owner.

These modules deliberately do not generate story content. They accept and return mappings so runtime adapters can store artifacts in an append-only run directory.
