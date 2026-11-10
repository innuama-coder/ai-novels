# Methodology

## Design thesis

HP1 is a deterministic compilation/linking boundary between accepted HLD and LLD. A good result is not a better story; it is proof that the same reviewed story controls were transferred completely, exactly and reproducibly.

## Applied methods

### 1. Content-addressed admission

Every trusted input has role, normalized workspace path and SHA-256. The upstream main artifact, manifest and completion triple must match the work-order. The public profile is checked from actual directory membership; the manifest is schema-valid and closes over every content file; completion binds the manifest, validation and canonical artifact.

### 2. Lossless canonical preservation

HA1–HK1 models and HQ1 review are copied byte-for-byte. Machine convenience views point to canonical values with JSON locators and hashes. No prose regeneration substitutes for a model.

### 3. Authority-preserving index

HB0 control/source IDs are indexed as `source_control` owned by HB0. HLD object IDs remain owned by their producing design stage. The assembler owns only the index entry and LWK projection.

### 4. Explicit trace, not prefix inference

Trace sources come only from explicit `source_refs`; decisions come from explicit `design_decision_ids`. For the current HK1 contract, which seals decisions at stage level rather than repeating them on each HKF, HP1 may project the single HK1 decision only when exactly one derivation claim binds `/lld_work_requirements` to the exact canonical list hash and exactly one HK1 design decision exists. Multiple claims or decisions fail closed. Other IDs in a work requirement are targets/constraints, not automatically source provenance.

### 5. Mechanical unresolved aggregation

HP1 checks expected HDD owners against HB0 routing and HQ1 coverage, then applies one closed decision table: surviving `required_now` blocks; all not-needed becomes `not_needed_for_current_hld`; a permitted conditional mix becomes `conditionally_preserved`; unanimous single-ref external resolution becomes `resolved`. No other combination is accepted.

### 6. Bijective handoff

HK1 requirements are `LWR-*`; HP1 creates `LWK-*` with the same suffix and exact copied fields. Source value hash exposes any drift. Both duplicate source IDs and projected collisions block.

### 7. Acyclic package sealing

The manifest closes over package content except itself and `stage-completion.json`. Completion then binds the finished manifest, validation and canonical artifacts. The result lives outside the package. This avoids impossible self-hash cycles.

### 8. Independent reproducibility

Validation hides the delivered result, reloads sealed inputs, regenerates an expected package, compares every byte, rechecks completion bindings and compares fixed result identity fields. Ambient time, randomness and filesystem metadata are forbidden.

## Boundary

HP1 can detect a semantic-contract inconsistency but cannot fix it. A defect is routed to its producing stage through a durable blocked result; local best-effort repair would violate provenance and review authority.
