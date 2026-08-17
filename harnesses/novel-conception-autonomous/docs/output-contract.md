# Output Contract

The production scheduler returns a `ProductionContext` after every committed
transaction. Its state reference is the only current orchestration authority;
receipts do not replace stage packages or completion records.

The run root contains:

- append-only canonical `state/revision-NNN.json` snapshots;
- immutable gates and one-shot work orders with consumed receipts;
- the current H1 workspace chain;
- formal B0, S1, W1, E1, T1, C1, Q1 and P1 packages;
- H1-A plan, H1-B fragments, H1-A assembly, H1-C HTML and formal H1 package;
- the external author event and, for revise, its deterministic return body;
- final conception completion only on the current approved branch.

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
