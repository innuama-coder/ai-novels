# Input Contract

## New production run

### Approved authority-revision fork

When a later author directive requires correcting an already completed
conception authority, the only bootstrap API is
`initialize_conception_revision_run`. It binds the completed parent run and
the external HLD question/answer/resolution chain, preserves the author's
exact words with `author_approved_bytes=false`, applies only the seven
explicitly allowed control edits, and requires a producer-independent semantic
review. The parent run is read-only. Migration finalization and authority
revision finalization are mutually exclusive.

The producer first calls `build_authority_revision_review_material`, which is
pure and writes no run files. A separate reviewer task reads that exact
material and seals a canonical `authority-revision-semantic-review` artifact.
Initialization accepts the review root and its `{path, sha256}` reference; it
never accepts reviewer identity strings as a substitute and never manufactures
a `pass` verdict. Before creating a lock, target, or staging directory it
checks the raw and canonical hash, candidate digest, exact seven-item coverage,
per-item pass with no findings, three-field producer/reviewer separation, and
`reviewer_produced_patch=false`.

B0 has exactly three mutually exclusive admissible input modes:

1. **Native interview contract 2.0.** I0-I5 completions expose hash-bound
   `control_projection` artifacts, V1 exposes the hash-bound
   `fact_dependency_register`, and the current V2 has an explicit approval.
2. **Finalized legacy migration.** `migration-finalization.json` comes from a
   fresh, exhaustive author decision over every proposed control and fact. The
   autonomous runtime must call `validate_finalized_migration_handoff` and then
   `build_baseline_from_handoff`; a `waiting_author` candidate, an old V2
   approval alone, or caller-supplied path mapping is never admissible.
3. **Finalized authority revision.** The new revision-000 state, effective
   I3-I5 artifacts, deterministic patch material and copied external semantic
   review all revalidate through the authority-revision finalization chain.
   Its base ancestry is independently declared as either `native` or
   `compatibility_migration`. A migration-based revision consumes the accepted
   parent B0 baseline, completion and manifest plus its finalized migration;
   it does not require nonexistent legacy I0-I5 `control_projection` fields
   and must not submit native source arguments alongside that parent package.
   The initial B0 input gate must bind the fork's exact
   `state/revision-000.json`. After an explicit routed return to B0, a refresh
   gate binds the exact current descendant and supplies its complete canonical
   chain back to revision-000; every state must preserve the authority source
   and finalization identity. The bootstrap state's `source_interview_state`
   must equal the authority finalization's `parent_run` reference. The accepted
   migration B0's older run state is ancestry only and cannot be reused as the
   current run state.

The autonomous `production_run_id` and immutable interview `source_run_id` are
separate identities. Native mode normally uses the same value. Migration mode
may use a new production id, while all legacy snapshots, projections, facts,
candidate manifest and the new migration author decision remain hash-bound to
the original source id. Downstream stages use only `production_run_id`.

The public input is one approved interview source chain, not a prebuilt P1 or
H1 package. Before `initialize_production_run`, the caller must possess:

- an immutable source root and sealed current interview-state reference;
- the exact I0–I5 design completion set referenced by that state;
- current V1 completion, V2 completion and explicit V2 author approval;
- the fact-dependency register required by B0;
- a unique non-empty production run id and an absent production run root.

The B0 owner receives native paths through its work order and calls
`build_baseline_package`, or receives exactly one finalized migration path and
calls `build_baseline_from_handoff`; both routes then call `complete_b0`. The
scheduler never extracts interview facts itself. All migration protocol, hash,
coverage, status or author-binding failures fail closed before a B0 directory
is committed.

Each later owner receives only the current work order, sealed input gate,
persisted state reference, exact upstream package paths and any active return
body. All values are immutable. H1 internal actions additionally bind the
current persisted workspace. `dependency-spec.json` fixes the only legal owner
and runtime API for every action. Stage execution and package-orphan recovery
must submit that exact actor id; a mismatch is rejected before semantic code is
called and leaves the current work order pending.

After the current P1 is admitted, `initialize_h1_workspace` creates the sole H1
session workspace. Retrying the same session id is idempotent. Replacing an
active same-P1 workspace with a different session is invalid; a new session is
allowed only for a changed P1 binding or a sealed return whose resume stage is
H1.

An existing run accepts only its run-root path through
`resume_production_run`. Supplying reconstructed state, an alternate owner,
another pending work order or direct completion JSON is invalid.

A pre-assembly H1-A plan correction accepts only the public
`apply_internal_h1_plan_return` transaction. Its inputs are the current
production context, independently persisted sealed candidate report, a
pre-existing sealed independent
`presentation-fidelity-review` with `verdict=revise`, the exact router-produced
H1-A-plan request, and the `production-orchestrator` actor. The API derives the
current workspace, manifests, producer identities, pending assemble order and
P1 package itself; callers cannot supply or override those identities.
The transaction does not persist reviewer evidence for the caller.
The scheduler must first call `assign_internal_h1_plan_fidelity_review` with
the actual independent task/thread. That reviewer then calls
`record_internal_h1_plan_fidelity_failure` under the dedicated reviewer actor;
the resulting protected completion is a required return input. Generic
document persistence cannot mint any of these three authority artifacts.
The same protected chain is also the sole input path when a fresh independent
plan review, performed while an H1-B return is active, proves that the defect
belongs to H1-A planning.  In that case the assignment and completion bind the
current active H1-B return, its qualification, planned workspace and H1-B
order, plus the exact earlier fragments-ready workspace and manifests.  No
generic escalation input, caller-selected ancestry, or already-used H1-B
reviewer identity is accepted.

Every admitted successor requires a pre-existing immutable commit intent that
binds the current work order and its exact successor hash. A state or H1
workspace written without that journal is never auto-admitted during recovery.
The journal may be prepared only after the formal owner evidence reproduces the
entire successor through a fresh coordinator; schema validity or a partial
field comparison is insufficient.

## Author input

The author decision is a separately created, sealed event that binds the
current P1, formal H1 and HTML package. It is accepted only after the persisted
state is `waiting_author`. The scheduler may forward but never create or edit it.

## Terminal compatibility input

`run_from_rendered_h1` retains its historical seventeen-argument contract for
already rendered H1 callers. It is not valid for starting a new conception
run. Its output-root recovery restriction remains:

<!-- OUTPUT-ROOT-CONTRACT:BEGIN -->
{
  "schema_version": "2.0",
  "fresh": ["absent", "empty-real-directory"],
  "retry": {
    "allowed_shape": "H1/stage",
    "scope": "h1-publication-orphan-only",
    "content_validator": "formal-h1-publisher"
  },
  "root_entry": {
    "symlink": false,
    "reparse_alias": false,
    "parent_resolution": "platform-normal"
  },
  "forbidden_residue": [
    "D1",
    "R1",
    "author-decision",
    "completion",
    "final",
    "terminal",
    "sibling",
    "extra"
  ],
  "later_transaction_recovery": false,
  "author_decision_basename_enforced": false
}
<!-- OUTPUT-ROOT-CONTRACT:END -->
# Gate-authoritative package binding

Every S1-through-P1 package input is derived from the sealed input gate and the
current stage-completion reference. The completion, manifest, and validation
must be unique hash-bound siblings under one logical and physical package root.
Attempt-qualified Windows extended roots and unique legacy flat roots are
supported. Caller-selected overrides, missing or ambiguous roots, foreign or
escaped references, and tampered siblings are rejected before work publication.
Windows extended and ordinary spellings of the same resolved root are treated
as one physical identity; the namespace prefix is never accepted as a logical
reference. Resolution still rejects traversal, drive-qualified logical paths,
backslashes, cross-root targets and symlinks escaping the run root.
The executor receives the sealed order inputs and cannot replace them through a
closure; stage-return replacement orders recompute the same bindings.
