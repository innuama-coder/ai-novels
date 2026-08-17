# Compatibility migration contract

## Scope

Bridge one already approved legacy I0-I5/V1/V2 interview chain to the newer B0 input
contract. Preserve source bytes and meaning. Do not create an approval, B0 handoff, B0
baseline, or revised interview artifact.

## Projection plan

Use `projection-plan.schema.json`. Supply exactly these input paths: I0-I5, V1, V2, and
the existing V2 approval. Paths may be absolute, relative to the plan, or relative to the
invocation working directory; ambiguous resolution is rejected.

Supply one `stage_projections` item for each I0-I5. Each selected section has a stage-
prefixed `control_id`, one contracted `hardness`, and the exact H2/H3 `heading` without
Markdown markers. Extraction starts at the heading and ends before the next equal-or-
higher-level heading. The value is the unchanged body. Missing, duplicate, empty,
overlapping, metadata, H1, and H4-H6 selections are invalid.

Every fact candidate has `id`, `proposed_status`, and `claim`. `not_applicable` also has
`rationale`; `open` has `blocking:false`, `allowed_handling:"preserve_open"`, and
`rationale`; `adopted` has source paths `research_package` and `adoption_record`, plus
`allowed_use` and `fiction_boundary`. Adopted evidence is snapshotted. Use one explicit
`not_applicable` fact rather than an empty list.

## Candidate

The builder proves that all completions are ready and share `run_id`; design hashes match;
V1 binds exactly the selected I0-I5; V2 binds V1; and the old V2 approval binds the brief.
It snapshots the chain, state, plan, designs, and adopted evidence.

The manifest, six projections, and fact register all say `waiting_author`, so they are not
B0-ready. JSON and HTML reviews present the exact candidates. `source_run_id` means the
original interview run; `migration_id` means only this compatibility operation.

## Compatibility decision and finalization

Use exactly one fresh, manifest-bound route:

- `author-decision.schema.json`: the author reviews the migration itself and accepts every
  control and fact ID exactly once.
- `author-process-decision.schema.json`: the author explicitly delegates compatibility
  conversion as internal work and reserves human review for the final H1 sections
  `world`, `story`, `characters`, and `fragments`. This is not content approval; the
  converter and Q1 own migration correctness.

An old approval, silence, agent-authored delegation, partial list, extra ID, duplicate ID,
or stale hash is invalid.

The finalizer copies that decision and the intact candidate, then emits canonical ready
projections, a canonical ready fact register, validation, and
`migration-finalization.json`. Its `finalized` status proves that the selected conversion
route is authorized; it is not conception approval or a B0 handoff. Final validation
replays the candidate hash and either exact item coverage or the exact four-part review
delegation rather than trusting status.
