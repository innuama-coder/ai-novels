# Storyline proposal quality gate v1

## Boundary

This gate is evaluation-only evidence about one autonomous storyline proposal.
It is owned by `eval_harness`, has
`authority=non_authoritative_quality_evidence`, and has
`artifact_role=not_completion`.  It is not author approval, a production S1
artifact, a stage completion, or a substitute for Q1.

The formal loader `load_ready_eval_case()` receives only an explicit
case-manifest path.  It first calls the official
`storyline_plan.load_eval_case()` structural loader, then resolves the gate and
quality schema only through the manifest's hash-bound references.  A fixture,
plan, plan-schema, graph, coverage, authority, gate-schema, or gate-reference
failure therefore stops evaluation before admission.

The two-argument `load_storyline_quality_gate()` entry is retained only for
compatibility tests of gate semantics.  Its caller-supplied gate path must
resolve exactly to the manifest-declared path; an identical-hash sibling is
rejected.  It returns a mechanically distinct compatibility result type that
is not admissible as formal S1 evidence.

The proposal adapter accepts only a manifest path.  It calls the formal loader
itself and defensively copies that exact validated snapshot; neither a formal
result object, a compatibility result object, nor a mutated structural case can
be supplied to `from_manifest`.

The gate then binds the manifest's exact fixture, storyline-plan, and
storyline-plan-schema paths and SHA-256 values, plus the fixture, run, plan,
and structural-validation identities.  The quality-gate schema has a fixed
repository path and a code-pinned SHA-256.  No sibling discovery is used.
Both the loader and the public `validate_storyline_quality_gate()` entry point
apply that complete pinned schema; direct callers cannot bypass role,
authority, required-field, enum, or `additionalProperties` checks.

The public validator also requires `structural_case.validation` to be a
mapping with `status=ready`.  Its plan, fixture, and run identities must equal
the structurally validated case even when a caller recomputes the subject hash
after tampering.  A hash match is therefore binding evidence, not a substitute
for structural admission.

## Independence and admission

The proposal producer and quality reviewer each declare a task ID and thread
ID.  Both the task IDs and thread IDs must differ.  This is accountable local
identity separation, not a cryptographic signature.

Exactly these eight checks are required:

1. `authority_preservation`
2. `main_arc_completeness`
3. `causal_topology`
4. `role_clustering`
5. `open_preservation`
6. `optional_non_load_bearing`
7. `non_placeholder_evidence`
8. `downstream_usefulness`

Every check must be `pass`, cite a non-empty exact target set, and supply
distinct evidence and a distinct failure condition that each name at least one
of those targets.  Target IDs resolve only through the structurally validated
fixture and plan object registry.
After schema validation, the relation validator independently requires every
check status to remain `pass`; final admission independently requires
`verdict=ready` and `findings=[]`.

Coverage is deterministic:

- authority covers every control and semantic anchor, including the exact
  derived-anchor subset and its source controls;
- main arc covers the architecture and unique main line;
- causal topology covers the architecture, every line, and every connection;
- role clustering covers every line and every C1 requirement;
- open preservation covers exactly author-open controls and anchors;
- optional non-load-bearing covers exactly optional-melody lines and their
  incident connections;
- non-placeholder evidence covers the complete case object registry;
- downstream usefulness covers every W1/E1/T1/C1 requirement.

If a valid plan has no author-open or optional-melody object, the corresponding
check targets the plan ID as an explicit not-applicable witness.  The loader
also rejects common placeholder tokens in the fixture, plan, check evidence,
or failure conditions.  `unresolved` and a concrete author-open question are
not placeholders.

Admission requires `verdict=ready` and `findings=[]`.  A missing or duplicate
check, unknown or stale target, incomplete category coverage, reused template
evidence, subject/hash drift, identical producer/reviewer identity, untrusted
schema, non-empty finding, or false authority/completion role fails closed.

## Assurance limit

The gate makes the reviewer and reviewed objects inspectable and detects known
structural shortcuts.  It does not mathematically prove literary quality or
the truth of free-text judgments.  Q1 remains responsible for independent
review of the complete S1-W1-E1-T1-C1 conception chain.

The versioned generic and Duanxian gates referenced by their manifests are the
published formal evaluation cases for the S1 integration probe.  Their
`ready` verdict is non-authoritative quality evidence and does not weaken the
assurance limit above.
