# Output Contract

The production scheduler returns a `ProductionContext` after every committed
transaction. Its state reference is the only current orchestration authority;
receipts do not replace stage packages or completion records.

The run root contains:

- for an authority-revision fork, an immutable `authority-revision/` evidence
  chain containing the bootstrap intent, copied parent/HLD evidence, author
  directive binding, exact patch plan, independent semantic review,
  finalization, validation and completion;

  The semantic review is copied byte-for-byte from an external canonical,
  hash-bound artifact. Its candidate digest is reproduced from the final
  directive, evidence bindings and exact seven edits. No bootstrap component
  is permitted to author or upgrade the review verdict.

  `source_kind` remains uniquely `authority_revision`. If the read-only base
  was an accepted compatibility migration, `base_source_kind`, the base
  migration finalization and the parent B0 baseline/completion/manifest are
  propagated through the new baseline, package manifest and B0 completion.
  I0-I2 and every non-target control remain the parent's exact semantic
  projection; only the seven reviewed I3-I5 values may differ.

  The new B0 `run_state` is the authority finalization's `parent_run`, exactly
  matching the fork revision-000 `source_interview_state`. A migration base's
  old run state remains reachable only through the copied parent B0 baseline;
  it is never promoted as the current authority-revision run state. B0
  completion compares the complete reference, not only its SHA-256.

  A refreshed authority B0 keeps the old package and completion immutable. Its
  stored input gate references the current post-return state, and the package
  carries the complete hash-linked state chain back to revision-000. The old
  completion is superseded, the old work order receives a rejection receipt,
  and the replacement B0 completion and subsequent S1 gate/order are appended.

- append-only canonical `state/revision-NNN.json` snapshots;
- immutable gates and one-shot work orders with consumed receipts;
- the current H1 workspace chain;
- formal B0, S1, W1, E1, T1, C1, Q1 and P1 packages;
- H1-A plan, H1-B fragments, H1-A assembly, H1-C HTML and formal H1 package;
- the external author event and, for revise, its deterministic return body;
- final conception completion only on the current approved branch.

A B0 execution record binds the exact behavioral runtime, validator and schema
files used by B0. It deliberately excludes the package-level
`runtime/__init__.py` export aggregator, whose later-stage public exports do not
change baseline semantics. Public validation accepts a historical execution
catalog that still contains this file only when its complete identity-to-hash
map equals the frozen digest registered by the harness; every copied reference
is then revalidated read-only. Only the registered old-to-approved-current
`runtime/baseline.py` hash pair may differ; the separate migration-authority
module is mandatory in every new catalog and is the sole identity an exact
historical package may lack. Every other required runtime, schema and validator
must remain current-exact. It never lets an extra replace a required identity:
all required identities must remain present and manifest-bound, and new
packages must equal the current B0 files. Missing, tampered, partially resealed,
future-validator or unregistered historical profiles fail closed.

S1 through P1 use the shared versioned stage-implementation identity contract.
Each catalog contains only the producing stage's runner, stage-owned runtime
helpers, authoritative schemas, and review contracts. An upstream validator is
called through its public API and authenticates its own package and identity;
its source tree is not copied into every downstream identity. Thus approved
maintenance to B0 or S1 does not make an otherwise unchanged E1/P1 package
stale. Current catalogs are exact and include
`runtime/stage_implementation_identity.py`. Pre-versioned packages replay only
when the complete stored catalog digest equals the frozen stage entry, every
stored artifact still verifies, the removed/missing identity set is exact, and
every changed retained file matches an explicit old-to-approved-current pair.
Missing or tampered stage-owned runtime/schema/review files, arbitrary extras,
resealed legacy catalogs, and any later unapproved current drift fail closed.

The formal H1 package preserves the original H1-A input gate as immutable
provenance while binding its stage completion to the current `H1-publish`
work-order gate. After an internal H1 return, the current gate may carry a new
run-state and return binding, but its run, target, baseline, and upstream
completion topology must remain byte-for-value equal to the sealed plan gate.
The active return must match the current gate exactly and is resolved only by
the accepted H1 completion.

The rendered workspace is authoritative for all four accepted H1 manifest
paths. Legacy or attempt-qualified plan, assembly, and HTML roots, plus legacy,
attempt-qualified, or nested fragment roots, are valid only when each exact
logical reference maps to the supplied physical package root and manifest SHA.
The publisher never scans sibling directories. It forwards the accepted plan,
fragment, and assembly logical roots explicitly through H1-C into H1-A
validation, so a qualified package can never silently fall back to a legacy
lineage.

If an unresolved H1 revision reaches assembly with a sealed H1-A implementation
that is no longer current, production must use the internal H1 implementation
refresh transaction described in
[`internal-h1-implementation-refresh.md`](internal-h1-implementation-refresh.md).
That transaction preserves B0-P1, supersedes the stale H1 suffix, and restarts
at a fresh H1-A plan workspace. It cannot promote the stale plan, fragments, or
assembly candidate and cannot manufacture an author decision.

When only the sealed production-qualification digest predates a versioned,
migration-approved stage implementation catalog, a current active H1 return may
use the compatible qualification refresh. The receipt records the frozen
migration-registry digest, every exact approved implementation pair, and the
successful B0-P1 public replay set. The successor preserves all content and H1
workspace references byte-for-value; only revision/previous-state, the current
qualification pointer, and a newly bound copy of the pending H1 gate/order
change. This evidence cannot authorize a package, schema, review protocol,
owner version, runtime-contract semantic, or unregistered implementation
change.

The refresh does not reseal a consumed H1-B order. Its old state binding remains
admissible to protected fragment-fidelity handling only through the current,
trusted compatible-refresh receipt, whose predecessor is that exact state and
whose successor is the current state. The workspace and old/new pending action
bindings must be byte-for-value identical and the state snapshots may differ
only in revision lineage; this exception cannot cross another state revision.

A failed independent prepublication HTML readability review uses the
production-only `apply_internal_h1_html_readability_return` transaction. Its
successor retains the accepted plan, fragment, and assembly manifest
references, replaces the active H1 return with an exact `H1-C` return, restores
the current workspace pointer to the immutable assembled predecessor, and
publishes one pending H1-C order. Only `html` and `completion` are superseded;
the rejected rendered workspace, HTML manifest, failure review, and prior
return remain append-only evidence. A completed H1-C retry that fails a new
independent review may refresh an older H1-C return with a distinct immutable
failure and request; other same-action refreshes remain forbidden. A later render must use a fresh logical
package path and must pass a new independent readability review before H1 can
be published.

The first formal H1 completion is published at `H1/stage`. If that completion
has been superseded, the replacement is append-only at
`H1/stage-attempt-N`; the legacy package is never overwritten or recovered as
the new result. The current run-state H1 completion reference is authoritative
for the human-review completion and manifest paths. Its sealed execution record
is authoritative for the matching `H1/html` or `H1/html-attempt-N` root used by
an author-decision event. Mixed old/new paths fail closed.

Same-session retries never overwrite an accepted workspace. Production names
new `fragments_ready` and `rendered` workspace references with the accepted
fragment or HTML manifest SHA prefix. Historical prepared H1-B/H1-C intents
that bind a now-occupied flat workspace path are recoverable only when the
supersession marker, predecessor, package manifest, successor body, collision,
and active return all replay exactly. Recovery writes a qualified successor
and an immutable relocation receipt; the old path and old intent remain
unchanged.

The machine conception deliverable is the current P1 package. The human
deliverable is the H1 report, fragments and offline HTML, all bound to that P1.
The H1 assembly also contains an independent element-level semantic fidelity
review. Its pass is required evidence that human-language compression did not
materially contradict, omit, overstate or promote P1 content.
If that review returns `revise` before assembly because H1-A planned unsupported
specificity, production must use the append-only transaction documented in
[`internal-h1-plan-return.md`](internal-h1-plan-return.md). It rejects the old
assemble order, preserves the rejected plan and fragments as evidence, and
starts a new H1-A plan session from the unchanged current P1.
Development may start only when the latest persisted state has
`development_status=ready` and the final completion revalidates all nine stage
completions plus the current author approval.

Branches:

- `approved`: author state is persisted, then a resumable final transaction
  publishes development admission;
- `revise`: the return request is persisted before the revise state and names
  the exact owner/resume point; invalidated downstream packages are non-current;
- `rejected`: terminal state, no final completion.

The historical `HarnessRunReceipt` remains the result of the compatibility-only
`run_from_rendered_h1` API. It is not evidence that B0–H1 were production-
orchestrated.

The exact final deliverable set, authority order, delivery standards and
acceptance procedure are normative in
[`final-delivery-contract.md`](final-delivery-contract.md).
