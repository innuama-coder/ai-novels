# Autonomous Novel-Conception V2 Workflow

## Fixed graph

```text
B0 → S1 → W1 → E1 → T1 → C1 → Q1 → P1
                                      ↓
H1-A plan → H1-B fragments → independent fidelity review → H1-A assemble → H1-C render
                                      ↓
                         formal H1 completion
                                      ↓
                    external sealed author decision
                      ↙             ↓             ↘
                 approved         revise        rejected
                    ↓               │               │
          final completion     routed return      stop
                    ↓
          development_status=ready
```

The diagram is logical: P1 is the sole top-level input to H1-A plan, while all
H1 packages and workspaces carry the same run/session/lineage.

An approved correction to completed conception authority starts a new
revision-000 fork. The producer first builds deterministic review material
without writing a run. A different reviewer task seals an external, canonical
semantic-review artifact against that material. The bootstrap validates that
artifact before acquiring its run lock, copies it byte-for-byte, and never
creates or changes the review verdict. Only then may the exact seven allowed
text edits be replayed and the new run promoted.

The fork's B0 current source is always `authority_revision`; base ancestry is
separate. A finalized-migration parent is admitted only through its accepted
B0 baseline/completion/manifest chain. B0 copies that chain read-only, retains
its migration finalization as ancestry, and overlays exactly the reviewed
seven I3-I5 values. It never represents migration and authority revision as
two simultaneous current sources.

The fork's current state is also separate from base ancestry. Its initial B0
gate binds the exact authority bootstrap revision-000, whose
`source_interview_state` equals finalization `parent_run`. An append-only B0
refresh after a routed return instead binds the exact current descendant state;
the complete canonical state chain back to revision-000 must preserve the same
source and finalization identity and is copied into the refreshed package. B0
publishes the parent-run reference as its source `run_state`; an older migration
B0 state remains available only through the copied parent baseline lineage.

B0 implementation identity covers only the runtime modules and authoritative
contracts that define or validate B0 behavior. The package-level
`runtime/__init__.py` public-export aggregator is not a required B0 identity:
later-stage exports added there cannot make an already sealed baseline stale.
New B0 packages omit that aggregator from their implementation catalog. Older
packages that stored it remain replay-compatible only through the exact frozen
full-catalog digest registered in the harness manifest. That historical branch
revalidates every copied binding and permits exactly the registered old-to-new
`runtime/baseline.py` hash pair. Its separate
`runtime/b0_implementation_identity.py` authority is required and hash-bound in
every new B0 package; the historical package may lack only that newly introduced
identity. Every other current required file must still equal its stored hash.
The branch is read-only and cannot generate or reseal a package. Outside that
exact profile, a stored aggregator is merely a catalog superset member, while
every required runtime, validator and B0 schema binding is still mandatory and
hash-exact; missing or tampered required bindings fail closed.

The same ownership rule is versioned for S1 through P1 by
`runtime/stage_implementation_identity.py`. A stage binds its own executable
runner, directly used shared helpers, schemas, and review contracts; it does
not absorb the source files and schemas owned by every upstream validator.
Upstream public validation remains mandatory and fail-closed at the point of
use, so this removes maintenance cascade rather than upstream verification.
New packages use contract `1.0` and an exact catalog. Historical run19
catalogs are a one-way read-only migration: the full catalog digest, explicit
removed/missing set, and each runner old-to-approved-current hash pair must all
match. Any future drift requires a new declared contract version and cannot be
silently accepted by an old migration entry.

The current T1 owner contract is schema `2.5` with review protocol
`t1-initial-event-plan-semantics-v5`. Each adjacent S1 transition is realized
by one ordered atomic event span: direct causal continuity, strict time order,
one shared storyline, and exactly one final `story_transition` state commit.
That commit is the source line's final state-changing/transition-span event.
After it, the current contract admits only an E1-readiness-bound causal SEND
tail: non-state `connection_bridge` events owned by the source storyline,
forming the exact source-anchor-to-target-anchor path and an injective exact
cover of the connection's transport steps. It rejects lifecycle effects,
foreign or duplicate bridges, path bypass, post-target placement, and any
unowned trailing action. This is a runtime contract correction within schema
`2.5`/review protocol v5—the public JSON shape and review-claim universe do not
change, while the exact implementation identity does.
Typed edges distinguish `narrative_causal`, capability, proposition, token,
sequencing, and subject-lifecycle dependencies. Lifecycle validation follows
effective story time and the typed dependency DAG, not chapter or disclosure
order. It proves one `NOT_STARTED → ACTIVE → SHUTDOWN` sequence, a causal path
from formal acceptance through the single-use permit producer to startup, and
exactly one permit consumption. Only narrative edges realize S1 connections or
participate in the associative-connection ban. T1 `2.4` and earlier remain
read-only legacy replay branches and cannot authorize a new generation
session or a relabeled reseal. The exact T1 `2.3` full implementation snapshot
is retained for provenance audit, but no trusted `2.3` or `2.4` ready-package
identity is currently registered; both package inventories are explicitly
empty and replay therefore remains fail-closed.

The independent fidelity review is a bounded quality dependency, not another
top-level stage and not a content producer. It reads only sealed P1, plan,
fragments and the candidate report, and H1-A consumes its pass verdict before
publishing the assembly package. A missing, producer-authored, incomplete or
semantically failing review blocks assembly.

C1 treats the coordinator gate's B0/S1/W1/E1/T1 completion paths as canonical
logical identities. Its physical inputs and copied public `sources/` tree may
live at attempt-qualified Windows extended-length roots; both admission and
public replay prove canonical completion bodies, sibling manifest/validation
hashes, and the complete nested upstream lineage. Legacy flat logical paths
remain replay-compatible, while foreign, escaped or backslash paths fail
closed before workspace or package publication.

At the filesystem boundary, Windows normal and extended namespace spellings
(`C:\\...` and `\\\\?\\C:\\...`, including the UNC equivalent) have one
resolved containment identity. The prefix is never admitted into a logical
artifact reference. Resolution still occurs before containment comparison, so
`..`, drive-qualified logical paths, backslashes, cross-root paths and
symlinks that leave the run root remain fail-closed.

## P1 crash recovery boundary

If the P1 destination already exists, the P1 runtime must not overwrite or
repair it. It may reuse a fully valid package only when its sealed input gate,
B0-Q1 source packages, hashes, lineage, and implementation snapshot exactly
match the current invocation. The coordinator must either be at the exact
recorded pre-state with P1 non-current, or, for forward mode only, at a
persistent successor whose `previous_state`, current P1 completion, and
successor reference path exactly match. The runtime revalidates the package
and current sources read-only, repeats the source inventory check immediately
before coordinator admission, and leaves the existing directory byte-for-byte
unchanged.

The pre-state case returns `P1RunReceipt.replayed=true` and
`transition.replayed=false`; exact forward persistent replay returns both as
`true`. A return-resolution completion already present in `resolved_returns`
is strictly one-shot: propagate `COORD_RETURN_ALREADY_RESOLVED` unchanged and
return no new receipt. A partial, invalid, tampered, stale, differently gated,
or differently sourced directory fails closed and remains in place for
forensic inspection. Recovery is a runtime rule and does not change the public
JSON Schemas. Packages carrying an older implementation snapshot, including
the A4 artifact, are stale and must not be reused.

## H1 crash recovery boundary

The formal H1 publisher uses the same fail-closed publication boundary without
turning H1-A/B/C workspaces into top-level stages. The first completion uses
`H1/stage`; a later completion after that immutable package was superseded uses
a fresh `H1/stage-attempt-N` root. The publisher never overwrites, repairs,
merges, or deletes an existing root. It may reuse the selected directory only
after validating the complete formal package against the current rendered
workspace, current P1/plan/fragments/assembly/HTML packages, their byte
inventories, the exact sealed plan input gate and state-before, the current
implementation snapshot, and the canonical H1 completion at that same logical
root.

At the recorded pre-state, accepting a valid non-current orphan returns
`H1CompletionReceipt.replayed=true` and `transition.replayed=false`. A
coordinator reconstructed from the exact forward `waiting_author` successor
must additionally match `previous_state`, current H1 completion, rendered H1
workspace, and `next_state_path`; its persistent replay returns both flags as
`true`. Coordinator errors are propagated unchanged. Partial, tampered, stale,
foreign, differently gated, differently sourced, or differently pathed
packages fail closed and remain untouched. If atomic publication loses a race,
only an independently valid exact winner is recovered.

## Public production invocation

For a new approved interview baseline, call
`runtime.production_orchestrator.initialize_production_run`. For every later
process or Agent turn, call `resume_production_run`; the append-only state chain,
not conversation memory, is authoritative.

The scheduler then repeats this transaction:

1. `issue_stage_work(action=...)` builds the exact current input gate and one
   pending work order. The action fixes its owner through `ACTION_CONTRACT` and
   `dependency-spec.json`.
2. The owner submits its exact actor id and executes its existing controlled
   start/submit/run API. The orchestrator rejects an actor mismatch before the
   executor is called. Domain content never enters the orchestrator.
3. `execute_stage_work` persists a top-level transition, or
   `commit_h1_workspace` persists an H1 internal transition.
4. A crash reloads the latest valid state. A published package orphan may be
   admitted only after its owning validator passes and the recovery API proves
   the current gate, state and completion.

Before any state/workspace successor is persisted, the orchestrator writes an
immutable commit intent binding the work order, actor, input gate, H1
predecessor (when present), successor kind and exact successor hash. If a crash
occurs before the consumed marker is written, `resume_production_run` reconciles
only the byte-exact successor named by that intent. An unjournaled or ambiguous
successor fails closed. Input-gate paths include both the state revision and
action, so a routed return never overwrites its forward gate.

The intent is prepared only after a fresh coordinator reconstructed from the
persisted predecessor recomputes the complete state transition from the exact
gate and owner completion. Author revise additionally reuses and compares the
sealed return request, including its round-specific `return_id`. H1 internal
work similarly proves the exact owner manifest and complete workspace delta.

Retryable H1-B and H1-C successors use manifest-qualified immutable workspace
paths. The accepted fragment or HTML manifest SHA prefix is part of the
`fragments_ready` or `rendered` filename, so a corrected same-session package
cannot collide with a superseded attempt. A legacy prepared intent that still
names the historical flat path may be recovered only through an append-only
relocation receipt: production must reconstruct the exact successor body,
prove the occupied file belongs to the superseded H1 attempt, derive the same
qualified path as current production, and leave both the old workspace and
prepared intent unchanged.

After P1, call `initialize_h1_workspace` exactly once for the new H1 session.
Repeating the same session id is an idempotent recovery; a different session
cannot replace an active workspace. A new session is admitted only when a new
P1 invalidates the old binding or a sealed H1 return requires a revision.

Only one pending work order may exist. Work orders are immutable and one-shot;
wrong owners, stale contexts, forged bodies, direct state writes and semantic
fallback owners fail closed.

## Contract-upgrade admission

`apply_contract_upgrade()` derives the next stale owner from the sealed
current E1 and T1 completion canonical identities, in dependency order. The
request's target is only an equality assertion and cannot skip a stale E1 by
claiming T1. Inventory includes only unfinished, not-yet-invalidated sessions,
unconsumed work orders, and actual current completions; every path and digest
is recomputed from disk.

The stage identity is the complete validated package identity, not merely the
canonical model-version string. It binds completion, manifest, validation and
canonical references; exact runtime, JSON Schema and review-protocol artifacts;
the protocol names sealed by the generation session; and a successful public
package-validator replay. Qualification recomputes this identity from current
E1/T1 completions before resume, reconcile, issue and execute. A current version
label cannot conceal a stale or resealed implementation.

`resume_production_run_for_contract_upgrade()` is the only migration-only
entry that may open a formally stale run whose qualification is missing or
old. It grants no normal work issuance. Ordinary resume, reconcile, E1/T1
issuance, and execution remain blocked until the append-only upgrade completes.
After one owner is upgraded, a later upgrade recomputes the next target from
the newly sealed completions and uses a distinct immutable receipt. Replaying
one prepared upgrade is idempotent and never creates a competing receipt.

If the production identity changes again while the contract-upgrade return is
still active, the orchestrator performs an `active_return_refresh` instead of
registering another return. The exact active return body/reference and its
accepted state remain immutable; a new state revision changes only
`revision`/`previous_state`, and a new qualification receipt records the prior
qualification, refresh generation, actual target identity, current production
contract, and a digest of the automatically scanned session/work-order/current-
completion inventory. A different return, fake target, fake predecessor digest,
or stale caller fails before any artifact is written. Prepared refreshes recover
through the same append-only journal as first-time upgrades, and already
invalidated sessions or rejected orders are not inventoried again.

A different, qualification-only edge applies when the current run has already
reached an active H1 return and every current B0-P1 package passes its public
validator under the versioned implementation-catalog migration authority.
`apply_compatible_qualification_refresh()` admits the digest rebase only when
owner schema versions, review-protocol names, binding identities and production
contract shape are unchanged, and every old-to-current implementation hash is
the exact pair in the frozen migration registry. It appends one state revision
with no semantic field change, retains every B0-P1 completion and the exact H1
workspace bytes, rejects the stale pending H1 order, and issues the same H1
action with a fresh gate/state binding. A validator failure routes to that
package's actual B0-P1 owner; schema, protocol, owner-version, unregistered-code,
tamper, missing-package, or state/order/workspace drift remains fail-closed and
cannot use this edge.

An already consumed H1-B order is never rewritten by that rebase. Protected
fragment review may continue to use it only when the current qualification is
the exact direct compatible-refresh successor of the order's state: the two
states have identical semantic fields, the fragments-ready workspace is the
same sealed reference, and the rejected/reissued pending assemble orders have
identical action, inputs, actor and workspace. The trusted qualification plan
and receipt must prove the direct edge. Any intervening revision, foreign
receipt, workspace/order drift or semantic state change rejects the material.

## First stage-origin return admission

When a pending stage fails hard admission before it can produce a completion,
the stage owner builds one sealed request with `route_return()` and calls
`apply_stage_return()` with the exact pending work order and its required actor.
This entry point is valid only when no return is active, the current state and
forward input gate still match the pending order, the current E1/T1 production
qualification is valid, and the deterministic route targets the same or an
earlier owner.  A caller-supplied `_contract_qualification` is forbidden.

The `stage_return` transaction uses the existing append-only qualification
journal without claiming a production-contract change: old and new contract
digests are the same current digest, and the receipt names the prior current
qualification.  Under one run lock it preflights the complete immutable write
set, persists the return request and one-revision coordinator successor,
rejects the abandoned pending order (and any pending commit intent), records
suffix session/completion invalidations, and publishes the target owner's
`return_resolution` gate and replacement pending work order.  The replacement
E1/T1 order binds the prior qualification receipt because the new receipt and
order are committed by the same transaction and cannot hash-reference each
other.

All immutable artifacts are checked before the first write.  The current state
may advance before derived receipts during a crash, but the prepared plan
contains the exact successor and complete post-return documents.  Ordinary
`resume_production_run()` must recover prepared-only, mid-derived-prefix, and
complete-receipt pointer gaps byte-for-byte, then publish the replacement work
order and current qualification pointer.  Rejection and invalidation markers
are trusted only when reachable from that replayed receipt.  Do not emulate
this transaction with direct coordinator/store writes.

If the active owner itself must move upstream while that return is still
unresolved, `apply_active_return_escalation()` performs a distinct
`active_return_escalation` qualification transaction. The submitted return
must be a newly sealed route whose target/resume stage is strictly earlier than
the old active return's resume stage; its origin is the old resume stage and
the caller must be `production-orchestrator`. Normally the production contract
digest does not change. When the current qualification is stale and the
recomputed actual contract-upgrade target is strictly earlier than the active
return owner, the same escalation transaction advances from the prior digest
to the current production-contract digest; the asserted new return must name
that exact actual target. The old return, its accepted state, and earlier qualification
receipts stay immutable and unresolved; the new receipt alone records
`superseded_return`, the new return, actual target, full invalidation inventory,
prior qualification, old/new contract digests, and the current owner-version
map. The successor advances one revision, activates the
new return, retains only completions before the new target, and invalidates the
entire target-through-H1 suffix. Same-stage, downstream, foreign-origin,
misrouted, stale-order, stale-context, or forged requests fail before writing.
The new return, successor, current-contract qualification, invalidation receipts,
return-resolution gate, and first pending owner order remain one preflighted
write set; no intermediate refresh or downstream return may become current.

Escalation also seals the new target's `return_resolution` input gate and
pending work order inside the prepared transaction. Their complete canonical
bodies are hash-bound by the plan and replayed from the predecessor, old/new
returns, and successor. The old pending order, active sessions, current suffix
completions, and pending commit intent are rejected/invalidated/abandoned by
the same write set. All immutable documents are written before the new
work-order pointer; the current-qualification pointer is the final commit
marker. Prepared-only, mid-derived-prefix, and complete-receipt pointer gaps
therefore recover the exact gate, order, receipts, and pointers idempotently.
Caller inputs may not contain the reserved `_contract_qualification` key. The
plan binds only the caller's raw inputs; the post-order is rebuilt with the same
qualification helper used by ordinary `issue_stage_work`. B0 and other
non-contract stages receive no reserved field. E1/T1 bind the qualification
that was current when the escalation was prepared, its exact contract digest,
target owner/schema version, and—for T1—the E1 schema version observed in the
successor. Using this prior receipt avoids a receipt/order hash cycle; execution
admits it only for the exact first order at the escalation receipt's successor
and target. Recovery and trusted-chain replay recompute the full qualified
inputs from the prior qualification and successor, so a missing or forged
receipt, digest, owner, owner version, or upstream version cannot be replayed.

If the active owner remains correct but its pending order predates the current
owner implementation or sealed executor bindings, call
`refresh_active_stage_return()` with a fresh immutable return request. The new
route must preserve the exact target, resume stage, and resume point; exact
request reuse and earlier/later routes are rejected. This separate
`active_stage_return_refresh` transaction leaves accepted upstream completions
current, supersedes only the old active-return binding, rejects the old pending
order, inventories unfinished objects in the same suffix, and publishes one
fresh return-resolution gate and authoritative-input work order. Prepared,
derived-prefix, and complete-receipt pointer-gap recovery use the same trusted
append-only qualification replay. Do not emulate this operation with contract
upgrade or relax the strict-earlier escalation rule.

The same-owner state primitive is isolated in the production-owned
`runtime/production_coordinator.py`. Portable `runtime/coordinator.py` remains
byte-stable for B0-Q1 package identities; stage implementation catalogs must
never include the production-only module. Ordinary stage returns, upstream
escalations, contract upgrades, and skill execution continue to use the
portable `AutonomousCoordinator`.

Before a first upgrade, refresh, or escalation writes its request, prepared plan, or
successor state, storage purely derives and byte-preflights the complete
append-only write set: plan, state, order rejection, commit-intent abandonment,
session/completion invalidations, and complete qualification receipt. Internal
path collisions and conflicting existing bytes fail with zero transaction
writes; exact existing bytes are idempotent. Mutable state/qualification
pointers are validated during that preflight and published only after every
immutable path has passed.

“Already processed” is not inferred from a marker filename. Work-order
rejections, commit-intent abandonments, and session/completion invalidations
are trusted only when their exact path, hash, body, target and successor are
reconstructed from a state-bound complete qualification receipt in the current
qualification lineage. That lineage starts only at the current-qualification
pointer and follows exact `prior_qualification` references; scanning the
contract-upgrades directory can never add a trusted candidate. A reachable
legacy core-shape receipt remains compatible, while a self-consistent but
unreachable complete receipt is still an orphan. An orphan, malformed,
foreign-target or drifted marker blocks
before inventory can be reduced or the transaction can write anything.

Every reachable modern qualification receipt is also transaction-replayed,
not merely checked for the existence of its successor. Storage loads the exact
predecessor, return request, plan and successor, verifies deterministic
migration identity and one-revision hash-chain advance, then invokes the
coordinator's normal return-registration, active-return-refresh, or
active-return-escalation transition
in memory. The recomputed successor must be byte-identical, including active
return, invalidated suffix, current completions, status and previous-state
binding. Modern receipts cannot terminate with a null prior; the chain must
reach one strict bootstrap receipt whose exact fields, path, deterministic id,
digest and E1/T1 version map validate. Legacy compatibility applies only to a
reachable exact legacy core transaction, never as an unverified chain stop.

After the full write set passes byte preflight, the successor state and its
mutable current-state pointer may be published before the derived receipts are
written. This is an intentional crash boundary: the prepared plan lets resume
reconstruct and preflight the same receipts, finish them idempotently, and only
then publish the current-qualification pointer. Thus state publication never
weakens receipt trust and a pointer-gap crash remains recoverable.

Recovery is batch-atomic at its entry boundary. Before reconciling the first
unresolved prepared plan, storage orders every unresolved plan into one exact
state/qualification chain, reconstructs every expected complete receipt and
derived marker set, coordinator-replays every predecessor/request/successor,
validates each plan's `prior_qualification` and old digest against the virtual
qualification immediately before it, and byte-preflights the union of all
immutable writes. Only after the entire batch passes may any successor state,
receipt, or pointer be published. A stale/forked/null prior, fake request,
wrong migration identity, drifted successor or production identity, or one bad
plan among several therefore leaves all other prepared plans untouched and
commits none of them.

The orphan scan is deliberately last in that validation phase. Recovery first
rebuilds trusted markers from the current qualification chain without scanning
the whole marker directory, then validates every unresolved prepared plan and
adds all of its expected derived marker references to the allowed set. Only
then does one global scan reject extra, foreign or drifted markers, followed by
the union byte preflight. Consequently a legal crash after writing any exact
prefix of derived markers—or after writing every derived marker and complete
receipt but before advancing the qualification pointer—recovers idempotently;
the same files without a valid prepared transaction remain untrusted orphans.

## Author and final transactions

Before H1-A assembly, a `presentation-fidelity-review` verdict of `revise`
whose deterministic owner is H1-A plan must use
`apply_internal_h1_plan_return`. The review must bind the exact candidate
report, current P1, plan and fragment manifests and must be task/thread
independent of both producers. Candidate and review must already exist as
sealed documents under a precommitted reviewer assignment. The dedicated
reviewer actor records the verdict and protected completion; generic document
persistence cannot mint either authority artifact. The transaction rejects the pending assemble
order, retains all rejected artifacts as immutable evidence, and issues a new
H1-A-plan gate/order against a fresh initialized workspace. Missing review,
producer attribution, cross-owner routing, stale state and repeated return all
fail before any pointer changes. A replacement attempt may expose a new defect
while the earlier H1 return remains unresolved. A fresh independent plan
failure then performs a same-owner H1-A refresh; a fresh independent fragment
failure performs a local H1-B refresh. The fragment reviewer task and thread
must each differ from the sealed fragment generation-session producer; its
declared independence basis is not sufficient evidence by itself. H1-B must
use `assign_internal_h1_fragment_fidelity_review` →
`record_internal_h1_fragment_fidelity_failure` →
`apply_internal_h1_fragment_return`; assignment, review and completion use
protected namespaces and bind the exact current state, workspaces, consumed
order and marker, manifest, generation session and reviewer. Both append a
successor that names the
exact superseded H1 return and preserve the complete parent lineage, old
workspace and old work order as immutable evidence. Foreign owners, downstream
widening, reused assignment/evidence/reviewer identity and stale bindings
remain fail-closed. The fragment review+completion pair is protected by an
immutable prepared/complete journal: caught write failure rolls back the pair,
and resume validates the assignment before completing a process-interrupted
pair.

After H1-C, an independent production-owned human-readability review must seal
an exact `pass` over the author-facing JSON report, rendered HTML, and every
fragment text. Its five ordered dimensions are `natural_zh`, `readability`,
`humanized_character_voice`, `scene_not_spec`, and
`excludes_internal_ids_and_audit_jargon`. The reviewer task and thread must be
independent of both H1-A plan and H1-B fragment producers. Only then may the
orchestrator issue `H1-publish` and call `publish_h1_transaction`. Missing,
failed, stale, or producer-authored reviews fail before publication.

The H1 stage package copies the canonical review bytes as an immutable
manifest file and binds the original sealed review reference in its execution
record. The shared package-manifest role catalog is unchanged. Public replay
reconstructs the review binding from the execution record and checks the
copied bytes, manifest file hash, and sealed review hash together.

After publication, persist the resulting `waiting_author` state before
requesting a decision. The next process may resume that state and issue
`author-decision`; `record_author_transaction` accepts only the external sealed
event. Author-decision validation derives the H1 root from the current sealed
H1 completion and the HTML root from that completion package's sealed execution
record. It never falls back from an attempt-qualified current package to the
legacy `H1/stage` or `H1/html` path.

If a fresh independent review discovers unreadable author-facing language
while the run is still `waiting_author`, no author decision may be fabricated.
`apply_internal_h1_readability_return` requires author decision, pending work,
and active return all to be absent. It binds the current H1 completion,
manifest, report, HTML, fragment manifest, fragment package, every fragment
text hash, and exact finding evidence; then atomically supersedes the full H1
suffix, preserves B0--P1, advances to `revise`, and issues a fresh
`H1-A-plan` against a new initialized workspace. Prepared, partially derived,
and complete transactions replay from one canonical plan; collisions and
tampered receipts are zero-write failures.

If that independent review fails before formal H1 publication while an older
H1 return is still active, `apply_internal_h1_html_readability_return` is the
only HTML-only retry path. It accepts no author decision, H1 completion, or
pending order. The failure must bind the exact rendered workspace, report,
HTML, fragment package, producer identities, and quoted evidence. One
append-only transaction replaces the active return with a fresh `H1-C`
return. The predecessor may be broader, or it may be an older `H1-C` return
whose completed retry produced a second independently rejected page; no other
same-action refresh is accepted. The transaction rolls the workspace pointer back to the exact accepted
`assembled` predecessor, preserves plan/fragments/assembly and B0--P1, marks
only HTML/completion superseded, and issues one fresh H1-C order. The old
rendered package and old return remain immutable evidence. Prepared,
partially-derived, and complete-receipt pointer gaps replay byte-for-byte;
direct pointer edits or overwrite-in-place retries are forbidden.

H1 publication has two explicit gate bindings. The H1-A plan gate remains
sealed provenance and is replayed unchanged when validating the plan,
fragments, assembly, and HTML chain. The `H1-publish` work-order gate is the
sole execution admission: the completion copies its gate reference, run-state,
and active-return binding exactly. A local H1 return may change only those
admission fields; run, target stage, baseline, and upstream topology must still
equal the plan gate. Neither gate may be caller-overridden, and recovery
revalidates both bindings before advancing state.

The formal publisher resolves each H1 source from the exact manifest reference
already sealed in the rendered workspace. Plan, assembly, and HTML may use
their legacy roots or an accepted flat `*-attempt-N` root. Fragments may also
use an accepted nested root after an internal return. Every logical path must
map exactly to the supplied physical package root and its manifest byte SHA.
No directory search or fallback package selection is allowed.

The sealed plan, fragment, and assembly logical roots are passed explicitly
through formal H1 completion revalidation into H1-C and H1-A. Legacy defaults
are compatibility-only; none can be substituted for an accepted
attempt-qualified or nested reference.

- `revise` persists its return body first, then the state and deterministic
  invalidation route.
- `rejected` persists the terminal state and creates no final completion.
- `approved` persists approval; a later resumable `final` transaction alone may
  call `publish_final_transaction` and grant development admission.

No transaction overwrites an existing package or invents a missing decision.

## Terminal compatibility API

`runtime.harness.run_from_rendered_h1` remains available only for callers that
already own a complete rendered H1 chain and can finish its old atomic boundary.
It is not the public entry for new interview-to-conception work and must not be
used to bypass persisted production work orders.
# Gate-authoritative worker inputs

For S1 through P1, the production orchestrator derives package roots from the
sealed gate and current stage-completion references. Completion, manifest, and
validation must resolve uniquely as hash-bound same-parent siblings; missing,
ambiguous, foreign, escaped, or tampered roots fail before work-order
publication. Executors receive sealed inputs explicitly, and mismatches fail
before callback execution. Stage-return reissue applies the same rule.

P1 independently replays Q1 quality coverage. For T1 2.2–2.5 it merges only
the three contract-defined planned/canonical projection pairs and rejects ID-set
drift, duplicate registry IDs, third sources, missing counterparts, and
projection conflicts. T1 2.5 additionally projects token-instance consumption
and lifecycle effects; the frozen 2.2–2.4 field set and canonical hashes remain
unchanged. The resulting S1/T1 targets must exactly equal Q1's
sealed required and covered certificate values before P1 admission succeeds.

P1's cross-model index is schema/path-aware: explicit descriptors bind each
story reference path to allowed stage/kind identities. Operational E1 actor
slots do not alias C1 character slots, and semantic-review provenance IDs are
technical-local rather than inferred story references.
