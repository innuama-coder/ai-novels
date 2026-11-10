# Autonomous conception evaluation inputs

This directory contains evaluation inputs and test-Agent proposal adapters.  It
does not contain author authority and must not publish production stage
packages.

## Storyline plan boundary

An S1 evaluation plan is an `eval_owned_autonomous_proposal`.  It simulates the
semantic proposal that a real Agent would submit through the five controlled
S1 phases.  It is not:

- an interview artifact or B0 author control;
- an author approval, correction, or decision;
- `storyline-architecture.json`;
- a generation session, evidence record, manifest, validation, completion, or
  downstream answer.

The plan must declare `author_authority: false` and
`usage: S1_phase_payload_only`.  The production S1 runtime remains solely
responsible for accepting phase submissions, validating the canonical model,
sealing evidence, and publishing a completion.

## Explicit case loading

`storyline_quality.load_ready_eval_case()` is the formal S1 admission entry.
It accepts one explicit case-manifest path.  There is no sibling-file lookup
and no fixture-name convention.  A formal manifest binds exactly:

1. the unchanged interview fixture;
2. one versioned storyline plan;
3. the authoritative versioned storyline-plan schema.
4. one independently reviewed storyline quality gate;
5. the authoritative versioned quality-gate schema.

All five references use paths relative to this `evals` directory and exact
SHA-256 hashes.  Paths must use `/`, stay below both the evaluation and
repository roots, and contain no absolute prefix, backslash, `.` or `..`
component.  The fixed manifest, plan, and quality schemas are trusted evaluator
code: their byte hashes are pinned by the corresponding loaders, and the
manifest must repeat both pinned schema hashes.  Symbolic links and duplicate
JSON keys are rejected.  A hash mismatch or undeclared file fails closed.
Every JSON artifact is read exactly once; hashing, duplicate-key parsing and
schema/relation validation operate on that same immutable byte snapshot.

`storyline_plan.load_eval_case()` remains the structural loader.  The
two-argument `storyline_quality.load_storyline_quality_gate()` entry is a
compatibility surface for evaluator unit tests; it is not formal evidence.
Its explicit gate path must resolve to the manifest-declared gate path; an
identical-hash sibling is rejected.  Formal and compatibility loaders return
different result types.
Formal proposal authoring requires the manifest-only ready case and
`DeclarativeProposalAdapter.from_manifest(manifest_path)`.  The adapter invokes
the formal loader internally and projects only a defensive copy of that
admission snapshot.  It never accepts an externally loaded case.  Direct
fixture construction is legacy/test-only and cannot contribute formal S1
evidence.

The published generic and Duanxian manifests are the current formal S1
evaluation cases.  Adding or correcting a case requires new immutable
versioned artifacts and independent semantic review.

## Versioning

The current contracts are:

- `schemas/eval-case-manifest.v1.schema.json`
- `schemas/storyline-plan.v1.schema.json`
- `schemas/storyline-proposal-quality-gate.v1.schema.json`

Published plans and manifests are immutable.  Corrections create a new
versioned filename and a new manifest.  The existing fixture remains unchanged;
the new plan binds its exact bytes.

`not_applicable` is reserved by the plan vocabulary but deliberately rejected
by the v1 relation validator with
`STORYLINE_PLAN_NOT_APPLICABLE_UNSUPPORTED`.  Production S1 currently requires
every demand to have a non-empty realization.  Supporting genuine
non-realization requires a separately reviewed canonical S1 contract revision;
it must not be silently reinterpreted by an evaluation adapter.

See [storyline-plan-contract.md](storyline-plan-contract.md) for the complete
relation and authority contract.
