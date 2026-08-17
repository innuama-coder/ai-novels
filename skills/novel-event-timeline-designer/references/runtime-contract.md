# T1 V2 runtime contract

New production output uses T1 model schema `2.4` and consumes only E1 `2.4`.
Schemas `2.0` through `2.3` are read-only historical branches. `2.0` is accepted
only for its exact trusted implementation pair and released package identity;
the exhaustive `2.1` trusted identity inventory is empty. T1 `2.2` retains its
previous exact implementation-pair policy. T1 `2.3` has one trusted full
implementation-binding snapshot (including runtime, schema, protocol,
contracts, harness runtime and upstream runtime bindings), recovered from its
sealed generation session. No T1 `2.3` ready package was released, so its
package-identity inventory is explicitly empty: implementation provenance can
be audited, but complete package replay remains fail-closed. Each historical
package that does exist replays its own schema, phase table, lineage and
semantics. Relabels, full reseals and new legacy generation sessions are
rejected; an implementation snapshot is never sufficient to invent a package
identity.

`scripts/run_v2.py` is the sole T1 production runtime. Python may start a
controlled session, accept phase submissions, validate them, seal a package,
and finalize coordinator state. It never authors events, causal links, state
changes, or timeline semantics. Those are Agent-authored inputs.

## Exact input gate

T1 accepts only ready packages from B0, S1, W1, and E1 plus the coordinator's
exact T1 gate and pre-stage run state. `CODEX_THREAD_ID` is mandatory. The
session freezes:

- the four completion references and all twelve selected canonical,
  manifest, and completion source artifacts;
- B0 control values and hardness;
- every S1 storyline, EVD, SLC, and complete start/change/end state chain;
- W1 fact, system, institution, resource-flow, and authority-flow objects;
- every E1 environment and event affordance;
- the gate, thread, return binding, exact implementation/schema/protocol
  catalog, all four upstream manifest/completion identities, and E1's sealed
  authority-capability and transition-support semantic-review packages.

Any changed input, gate, state, thread, source hash, missing completion, or
non-shared lineage invalidates the session.

## Controlled Agent protocol

The Agent submits exactly five phases:

1. `event-demand-scan`: exact S1 `event_requirements` plus three digests
   recomputed from the sealed E1 universe, capability graph and occurrence
   requirement roots;
2. `global-timeline`: design decisions, span, axes and timing constraints plus
   the complete initial-condition, planned event/proposition/edge, transition,
   milestone, connection, obligation, occurrence and authority-instance plan;
3. `event-and-causality-model`: exact P2 event/proposition/edge projection plus
   environment placement;
4. `cross-line-state-test`: line sequences, SLC realization, state and
   information ledgers, EVD coverage, authority, derivations, open items;
5. `final-event-model`: the exact assembled canonical model.

Before P2 may be sealed, deterministic validation must pass and a different
reviewer thread must complete `t1-initial-event-plan-semantics-v4`. Its request
binds session, input gate, P1 evidence, candidate payload, all upstream
manifest/completion identities, both E1 semantic reviews, implementation,
schema and protocol hashes, and every deterministic claim. Any missing claim,
blocking finding, non-pass verdict or changed dependency invalidates the
receipt. The reviewer must seal `review-task-output.json` before submission;
the receipt and public replay bind the exact task, producer/reviewer threads,
candidate and request artifacts, review kind/protocol, raw artifact SHA,
canonical output SHA, and the complete verdict payload. The review package is
the exact ordered five-artifact set candidate/request/review-task-output/review/
validation. Every event declares which propositions it requires, produces, and
discloses; prose is never scanned to infer these facts.
Before phase 4 evidence is written, the runtime assembles the complete
provisional 2.4 model from sealed phases 1-3 plus the phase-4 candidate and
runs full validation. Final submission and package validation recompute it.

Each evidence file binds the frozen session, phase payload hash, and preceding
evidence hash. Every earlier field must equal its final-model projection.
Backfilled evidence and a one-shot Python-generated semantic model are invalid.

## Ready guarantees

### P2 plan and P3 exact realization

- Every S1 state-0 anchor is decomposed into atomic propositions and components.
  Static components have no event or producer; active-process and
  connection-entry components have closed producer events and select at least
  one same-anchor, ready, kind-compatible E1 support option. Component refs and
  the option-selection ledger are exact inverses.
- Every adjacent S1 state transition maps to one non-empty ordered atomic event
  span with unique event IDs. Consecutive span events have direct causal edges,
  strictly increasing world time, and the same storyline membership. Exactly
  one span event is `story_transition`: the last event, whose changed subject
  commits the exact S1 before/after state. Earlier events cannot change that
  storyline subject. A singleton span therefore preserves 2.2 semantics.
  Milestone buckets, S1 connections and story obligations are exact covers;
  first state arrival occurs at the final commit event.
- Each event changes one formal subject. Process events use a finite,
  source-bound process-subject registry and form continuous transitions.
- Each E1 required capability occurrence is covered with its min/max,
  distinct-group and share policy. A distinct group is unconditionally
  event-injective; `share_policy` only governs cross-requirement reuse of one
  occurrence and cannot relax that event separation. An occurrence reserved by an E1
  `obligation_occurrence_binding` is realized only on an event in the complete
  atomic span that implements its exact transition, or on its exact initial-
  option or connection support. Disclosure obligations additionally bind one
  exact occurrence/step/proposition witness event. Capability facts
  used by an event come from its exact local E1 steps; every non-root
  requirement has a strict producer ancestor.
- Authority facts are types. P2 creates deterministic instances from producer
  occurrences or a sealed upstream root. Producer/consumer step, event fact,
  action scope, instance policy and event-ledger inverses must all close.
- P3 has exactly the planned event IDs and copies every frozen field,
  proposition and causal edge. It may add only final event-development fields
  already owned by T1; it cannot alter the plan.

### Storyline and demand realization

- `event_demands` equals S1 `event_requirements` object-for-object.
- Every EVD appears in exactly one coverage record and only realizes events
  belonging to its S1 line.
- Every non-optional line has an ordered, recognizable responsibility chain:
  background/setup, trigger, development, turn or crisis, result, and
  aftermath. These are controlled `[RESP:...]` enum tokens, not inferred from
  prose. One event may carry adjacent compatible responsibilities, and any
  number of events may be used.
- Across a non-optional line, responsibility ranks are monotonic; a long chain
  may repeat or extend the current rank but cannot return to an earlier rank.
  Its final event contains both result and aftermath, and that same event
  performs the final transition into the S1 end state.
- Every line sequence has the exact S1 entry and exit state. Its
  `state_ledger` transitions for the storyline subject exactly implement
  `start_state -> state_changes[] -> end_state`.
- Every SLC has exactly one dedicated `connection_realization` record. Its
  `connection_id`, `relation`, `source_anchor`, and `target_anchor` equal the
  S1 canonical connection, including state index. State index `0` is the
  `before` side of the first event in the line's first transition span; index
  `i > 0` is the `after` side of the final commit event in span `i - 1`. Text equality never substitutes
  for the index, so repeated state text remains unambiguous.
- A causal SLC uses `realization_kind=causal_handoff`, names an ordered,
  continuous source-anchor-to-target-anchor `causal_edge_ids` path, and names
  `[REL:convergence]` timing constraints covering the complete path. Every
  cross-line `narrative_causal` edge is owned by exactly one causal SLC.
- An associative SLC uses `realization_kind=associative_alignment`, has no
  causal-edge claim and no `narrative_causal` path in either direction between
  its anchors, and names `[REL:association]`
  timing that contains both complete anchors.

### Event, causality, and time

- Every event has explicit preconditions, action, complication, one dominant
  before/after change, direct result, and next pressure. Placeholder
  consequences are rejected.
- `predecessor_event_ids` and the union of all typed edges are identical in
  both directions. The graph is acyclic, time never reverses, and every event is
  reachable from a declared root.
- Every edge declares exactly one `edge_kind`: `narrative_causal`,
  `capability_dependency`, `proposition_dependency`, `token_dependency`, or
  `sequencing`. Dependency `payload_ids` equal the exact producer/consumer
  endpoint intersection for their kind; narrative and sequencing payloads are
  empty. Different dependency kinds may share endpoints, but a kind/pair may
  occur only once.
- Every edge carries a strictly parsed header before its non-placeholder,
  human-readable explanation. `mechanism` begins with exact
  `[CAUSE_RESULT_SHA256:...][CAUSE_PRESSURE_SHA256:...]` hashes of the source
  EV's complete `direct_result` and `next_pressure`. `necessary_condition`
  begins with one `[PRECONDITION_SHA256:...]` hash matching one complete target
  precondition. Duplicate, missing, trailing token fragments, junk hashes, or
  empty explanations are rejected.
- Multiple roots are permitted. Each must be a background responsibility and
  have an explicit `[REL:independent-root]` or `[REL:concurrent]` explanation.
- World time uses exact `[WT:NNNNNN]` values. The span equals event min/max.
  The model declares exactly the world, background, event, and narrative
  disclosure axes. Memory, analepsis, concurrency, convergence, and association are
  represented only when used, by controlled `[REL:...]` values.

### Propositions and S1 story obligations

- `proposition_registry` is the closed set used by all event proposition
  fields and obligation realizations. Proposition statements are unique.
  Initially true propositions have no producer; every other proposition has
  at least one producer.
- Every event has at least one produced proposition. A required non-initial
  proposition must be produced strictly earlier by a causal ancestor. A
  disclosure cannot precede production. In the current 2.4 contract, every
  event's required, produced, and disclosed proposition-reference list is
  checked for duplicates before any set projection; an empty produced list or
  duplicate reference rejects P2 before review artifacts or phase evidence are
  written.
- Every S1 `story_obligation_register` item has exactly one T1 realization.
  Its kind, ordered anchor-derived witnesses, proposition binding, and audience
  are exact; free-text evidence cannot replace recomputation.
- Realization cardinality is keyed only by `obligation_id`, never by a source
  control. One source control may yield any number of atomic SOB obligations;
  T1 preserves each chain, branch, disclosure, and unknown-until obligation
  independently instead of merging them by `source_control_ids`.
- `causes` and `requires_all` require causal reach from every antecedent anchor
  to the consequent event. Event-local before-to-after causation is permitted.
  `requires_all` and causal consequents list every antecedent proposition in
  the consequent event's requirements.
- `strict_before` uses strict world-time ordering; `not_before` permits equality
  but never inversion.
- `first_disclosure` binds the S1 proposition and audience to the unique
  earliest disclosure event, which may be inside the consequent arrival span
  before its final state commit. `must_remain_unknown` may likewise name an
  exact event in that span and forbids disclosure through that witness. Other
  obligation kinds continue to use boundary anchor events.
- A `unique_terminal` proposition has exactly one producer, and every
  storyline's final event produces at least one such proposition. Repeating a
  final outcome as though it newly occurred is invalid.

### Environment and participation

- Every event has exactly one E1 environment placement and one or more
  affordances from that same environment.
- Current schema 2.3 rejects P2 before semantic-review artifacts or phase
  evidence are written unless every selected affordance serves at least one of
  the event's declared storylines through exact S1 event-requirement IDs. A
  causal-connection bridge must additionally retain every endpoint line
  actually served by its transport steps; a single-line label cannot erase a
  formally cross-line handoff.
- For every `(EVD,event)` realization, at least one placed affordance from the
  same environment must name that exact EVD, allow the initiating action, and
  contribute all of its prerequisites to the event. Same-line affordances for
  another EVD are not substitutes. A placed affordance that serves none of the
  event's realized EVDs is rejected.
- Participants, initiator, and counter roles use only S1 slot IDs. Empty
  counter roles require an explicit `[NO_COUNTER:reason]`; T1 never creates a
  concrete character.

### State, resource, authority, and information

`event-timeline.schema.json` intentionally has one general `state_ledger`.
T1 uses the formal `subject_id` to project different change kinds:

- `[KIND:state]`: S1 storyline/slot, W1 system/fact/institution, or E1
  environment state;
- `[KIND:resource]`: a W1 `resource_flows[].id`;
- `[KIND:authority]`: a W1 `authority_flows[].id` or E1
  `access_and_authority[].id`.

The event's changed `before_state`/`after_state` key is the structure declaring
the change; no free-text keyword scan is used. It must map one-to-one to a
ledger with the same subject, values, and triggering EV. Every ledger maps
back to such an event. Repeated transitions for one subject must be continuous.
Resources and authority are not fabricated for events that do not change them.
Every `allowed_by_ids` item must also be an applicable provider, not merely a
known object ID: a W1 rule applicable to an event line; a W1 system or
institution assigned to an event line; an E1 access assignment for the event
environment; the event's placed affordance; or an E1 transition contract for
that environment triggered by a placed affordance. SLOT, SL, ENV, flow objects,
and providers belonging to another line/environment are rejected.

Positive resource example: an event changes key `RF-001` from `available` to
`committed`, and one `[KIND:resource]` ledger for subject `RF-001` carries the
same values and EV trigger. Negative example: changing `RF-001` without that
ledger, or labelling it `[KIND:state]`, is rejected.

Positive authority example: an event changes key `AA-001` from `withheld` to
`granted`, and one `[KIND:authority]` ledger for the formal E1 access object
matches it. Negative example: an authority ledger whose subject is not a
formal W1/E1 authority object, or that has no matching event key, is rejected.

Information changes are optional only when the model has no disclosure. In
current 2.4, every `(EV, PROP)` in `discloses_proposition_ids` has at least one
atomic information record. Each record names exactly one disclosed proposition,
one event, and one communication-capable E1 `CSO` occurrence from that event.
Its subject is one visible participating S1 slot, and all visibility slots are
participants admitted by the source capability step. Every S1
`first_disclosure` is additionally bound through its exact E1 obligation
occurrence binding and T1 occurrence cover. The EV's `information_changes` and
the formal records reference each other exactly; repeated changes for one
subject are continuous. A reader-facing obligation may share the event, but C1
receives only the explicit character-slot visibility declared by this ledger.

## Authority, boundary, and package

Author-locked/open sets equal B0. T1 owns the ID-bearing event model and
decisions; downstream freedom is exactly the S1 slot set. Events and sequences
have current derivation hashes.

The four local authority classes are pairwise-disjoint. Any overlap is rejected
before deeper semantic validation; each class must then equal its exact B0,
T1-owned, or S1-slot source set.

T1 does not change storylines, world rules, or environments; create CHR
identities; write psychology, dialogue, scene prose, chapter plans, or finished
fiction. The exact package allowlist contains only the nine formal T1 root
artifacts, five named evidence files, the exact sealed P2 semantic-review tree,
the exact implementation catalog, and the unmodified formal B0/S1/W1/E1 source
trees. `validate_t1_package()` is
read-only and recomputes schema, semantics, evidence, implementation, manifest,
completion, and coordinator lineage.
