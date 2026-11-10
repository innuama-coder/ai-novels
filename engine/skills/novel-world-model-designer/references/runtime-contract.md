# W1 V2 runtime contract

`scripts/run_v2.py` is the sole production runtime for W1. Python controls
lineage, stage order, validation, sealing, and publication. The Agent authors
all world semantics; the runtime never templates rules, institutions, history,
systems, flows, or downstream demands.

## Controlled generation protocol

1. Call `start_w1_session()` with the current B0 package, current ready S1
   package, and coordinator-issued W1 gate. `CODEX_THREAD_ID` is mandatory.
2. The session freezes the exact B0 and S1 completions, gate, pre-stage state,
   source artifact hashes, B0 controls and fact dependencies, S1 storylines, and
   complete S1 world-requirement objects.
3. Let the Agent submit exactly five phases in order:
   `requirement-projection`, `world-rules-and-history`, `systems-and-flows`,
   `cross-line-world-test`, and `final-world-model`.
4. Every evidence record binds the frozen inputs, thread, payload hash, and
   previous evidence hash. P1-P3 validate cumulatively before evidence is
   written. P4 is assembled from the sealed P1-P3 projections plus its candidate
   fields and receives full-model validation before sealing. P5 must equal the
   exact sealed P1-P4 projections and passes full validation again.
5. Call `run_w1()` to validate and package the fifth submission. It writes the
   completion and asks the coordinator to accept it before publishing W1.

One-shot candidate models and evidence backfilling are not production inputs.
Changing B0 or S1 requires a new session and new Agent-authored phase payloads.

## Ready guarantees

New canonical models carry `schema_version: 2.1` and
`contract_revision: 2026-08-11`. Version 2.0 is legacy-only. Ready legacy
packages must also have a revision-free session and five-phase evidence chain,
plus package-bound W1 runtime/world-schema digests matching a reviewed legacy
allowlist. A standalone 2.0 model check is migration assistance, not proof that
a package is ready. An unknown explicit revision is rejected.

- `storyline_requirements` is byte-semantic equality with S1
  `world_requirements`, and every storyline is covered;
- each requirement is carried by at least one rule and one operating system;
- every rule binds at least one valid S1 world-requirement ID; every system and
  institution declares valid `source_requirement_ids`;
- each institution declares its world position, interests, dependencies,
  conflicts, and intervention scope. Dependencies or conflicts may be empty
  individually, but at least one of the two relationship sets is nonempty;
- every one of the eight world facets contains structured claims with valid
  requirement and rule IDs, so a nonempty placeholder is not evidence;
- every rule states scope, exception, cost, and constraint;
- every system has at least one valid S1 actor slot and closes inputs,
  resources, authorities,
  transformation rules, observable outputs, costs, limits, failures, state
  changes, and resource/authority/information flows;
- history, systems, and conflict tests cover every storyline; institution
  participation is requirement-specific and optional;
- each support record has exact `claim_coverage` for the requirement's required
  capability, constraints, acceptance checks, and downstream freedom. Every
  entry binds the source pointer and value hash to an owned realization ID and
  pointer, disposition, and rationale. Disposition is fixed by pointer class:
  capability/`realized`, constraint/`constrained`, acceptance check/`tested`,
  and downstream freedom/`deferred_to_downstream`;
- support ledger and E1 environment demands cover each S1 requirement exactly
  once. Every E1 demand supplies nonempty macro geography, institution/facility,
  spatial-relation, and plot-carrier dimensions;
- the four environment dimensions are defined by the current W1 schema only.
  The shared canonical handoff schema remains unchanged, and legacy W1 demands
  continue to validate against that historical shared shape;
- governed entity and flow IDs are globally unique; duplicate flow edges are
  rejected. Resource flows may converge on one target, while authority targets
  have exactly one owner;
- derivation claims cover rules, systems, and support records; an
  `author_open` ID may never appear in an implementation-bearing world-fact
  source, decision impact/projection, support source/realization, or derivation
  source/projection. It remains legal in the authority partition and open item;
- Phase 2 rejects duplicate fact-dependency dispositions before evidence is
  written and preserves earlier evidence hashes;
- fact-dependency handling is exactly closed against B0; author-open controls
  remain open;
- the four local authority classes are pairwise-disjoint; locked/open equal
  B0, autonomous-owned equals W1 decisions and governed world entities, and
  downstream-freedom equals the W1 environment-demand IDs exactly;
- gate, B0, S1, session, evidence, implementation, manifest, validation,
  completion, and coordinator transition share one immutable lineage.

Implementation freshness uses W1's deterministic dependency registry. It
includes the W1 runner, world schema, shared schemas, and upstream validators
executed by W1, while excluding E1 and later-stage-only schemas. The complete
schema catalog is still meta-validated; catalog membership alone does not make
an unrelated schema a W1 package dependency.

`validate_w1_package()` is read-only and recomputes these guarantees. Resealing
hash declarations cannot replace semantic coverage, source-value
participation, boundary, or completion checks. A package without a valid
`stage-completion.json` is not ready.

## Boundary

W1 defines world scope, rules, history pressure, institutions, systems,
resources, authority, information mechanisms, and requirements for E1. It does
not enumerate concrete environments or functional zones, build an event
timeline, create events, or create character profiles. Such artifacts are a
hard `W1_BOUNDARY_VIOLATION`.
