# Internal H1 plan fidelity return

`apply_internal_h1_plan_return` is the only production-owned return edge for
an independent presentation-fidelity review that rejects H1-A planning while
the current H1 workspace is `fragments_ready` and the only pending work is
`H1-A-assemble`.

Before review begins, `assign_internal_h1_plan_fidelity_review` seals the exact
reviewer task/thread identity, candidate, current workspace, manifests and
pending assemble order. The assigned reviewer role alone then calls
`record_internal_h1_plan_fidelity_failure`; this writes the review through a
protected store namespace and emits the completion receipt consumed by the
return edge. Ordinary `persist_document` calls cannot create assignments,
reviews or review completions in those namespaces.

H1-B uses the same three-step authority model. Before inspecting a fragment
candidate, `assign_internal_h1_fragment_fidelity_review` seals the current
state, `fragments_ready` workspace, exact prior `planned` workspace, consumed
H1-B order and marker, fragment manifest, generation session and independent
reviewer identity. Only the fidelity-reviewer actor may then call
`record_internal_h1_fragment_fidelity_failure`, which atomically persists the
review and a protected completion. `apply_internal_h1_fragment_return`
requires that exact completion; a review merely written through the public
document API has no authority. The pair write uses an immutable prepared/
complete journal: ordinary exceptions roll back files created by that
transaction, while resume validates the protected assignment and completes a
process-interrupted pair. All three APIs are public runtime exports.

The transaction requires all of the following exact, sealed evidence:

- the current `fragments_ready` workspace and its plan/fragment manifests;
- the current pending H1-A assemble order;
- the deterministic candidate report bytes already persisted before the
  return transaction and reviewed by the independent task;
- an independently produced, already persisted, schema-valid
  `presentation-fidelity-review` with `verdict=revise`, at
  least one concrete revised element, exact candidate quotes, and no blocker;
- reviewer task/thread identity distinct from both plan and fragment producer
  generation sessions;
- a router-produced H1-A-plan return whose evidence id is the review SHA-256.
- the protected review completion that resolves the precommitted assignment.

On first success it appends one state revision, marks the old H1-A assemble order
rejected, preserves all B0--P1 completions, keeps the rejected plan, fragments,
candidate and review immutable, creates a new initialized H1 session, and
issues exactly one new H1-A-plan gate/order from the current P1 package.

An unresolved H1 return is a parent lineage, not a ban on later independent
findings inside the replacement H1 attempt. If replacement planning reaches
`fragments_ready` and a fresh independently assigned review rejects the new
plan, the same API performs an append-only same-owner refresh to a new H1-A
plan. If the plan is sound but a fresh independent fragment-fidelity review
rejects H1-B, `apply_internal_h1_fragment_return` narrows the active H1 lineage
to H1-B. Its reviewer task id and thread id must each differ from the exact
fragment generation-session producer identity; a self-declared independence
basis cannot override either collision. A replacement review must also use a
task and thread distinct from the reviewer recorded by the active H1 return.
Both transactions replace only the
active return binding and record the
exact `superseded_return`, reject the current downstream order, restore a new
initialized workspace or the exact sealed planned workspace as appropriate,
and keep every older return, workspace, package, candidate, review and order
byte-immutable.

If that active H1-B lineage exposes a defect in the still-authoritative plan
(including an author-visible internal token), the plan authority chain may
escalate only through the same protected assign -> record -> apply APIs.  The
assignment is bound to the current H1-B return and qualification, current
planned workspace/order, and the exact earlier `fragments_ready` review
workspace and manifests.  Its reviewer must be fresh relative to both producer
sessions and the H1-B reviewer.  Apply supersedes H1-B with an H1-A-plan return,
rejects the current H1-B order and initializes a fresh H1 workspace.  The
fragment session was already invalidated by the parent qualification, so the
new qualification inherits that exact immutable invalidation receipt and
invalidates only the still-live plan session.  This narrow protected edge is
not available through generic active-return escalation or same-owner refresh.
Prepared transactions reproduce these bindings during recovery; replay,
foreign ancestry, stale state/order/qualification, and forged authority
documents fail closed.

Missing or unsealed review evidence, a `pass`/`blocked` verdict, producer reuse,
wrong run/session/manifest/report binding, a foreign top-level return, an owner
or target mismatch, stale state, exact request/failure replay, or a parent
return other than the sealed current H1-A/H1-B lineage is rejected before any
pointer changes. Direct workspace edits and overwriting any accepted H1 package
are never recovery mechanisms.
The return transaction never creates reviewer evidence on behalf of the
reviewer; an in-memory document, a directly persisted forged review, or a
review without the preassigned protected completion is invalid.
