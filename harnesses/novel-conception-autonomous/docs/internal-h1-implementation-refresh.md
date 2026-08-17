# Internal H1 implementation refresh

`apply_internal_h1_implementation_refresh` is the production-owned recovery
edge for an unresolved H1 revision whose accepted content can no longer be
replayed because the sealed H1-A implementation differs from the current
implementation. It is not a content approval shortcut and it never edits or
overwrites a sealed H1 package.

Admission is deliberately narrow:

- the run has an active H1 return whose owner and resume point are H1-A plan;
- the current workspace is exactly `fragments_ready`, with sealed plan and
  fragment manifests from that return;
- the only pending work is H1-A assemble, bound to that workspace and return;
- the sealed plan implementation catalog is complete and internally valid;
- at least one current H1-A implementation file has a different raw hash;
- the caller is the production orchestrator.

The transaction seals an implementation-failure record, routes a fresh H1
return, rejects the stale assemble order, invalidates the current H1 plan and
fragment sessions, and marks the current H1 workspace superseded. It preserves
all B0-P1 completions exactly, creates a new initialized H1 workspace, and
issues one fresh H1-A-plan order with the current authoritative P1 package as
its only content input. It does not create an author decision and does not
reuse the stale plan or fragments as current outputs.

The existing `active_stage_return_refresh` journal remains the append-only
transaction envelope. Prepared, partially derived, complete, and pointer-gap
replay must derive the same successor state, initialized workspace, gate,
order, invalidation marker, and qualification receipt. Collisions, wrong
actors, stale state, missing implementation evidence, or a non-H1 route fail
before any run-state mutation.

After the refresh, H1-A, H1-B, assembly, HTML, and H1 publication must run again
against the fresh lineage. Previously accepted human-visible prose may be used
as a content baseline only if its new packages and bindings are regenerated
and independently revalidated; old sealed artifacts are never relabeled as
new evidence.
