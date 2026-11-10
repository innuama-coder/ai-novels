# E1 V2 runtime contract

New production output uses E1 model schema `2.4`. Schemas `2.0` through `2.3` are
legacy read-only shapes; a public package receives legacy status only when its
packaged E1 runtime/schema digest pair is on the trusted historical allowlist
and its manifest, completion, and canonical digests match an exact released
package identity. The archived package chain is still replayed. Relabels and
full reseals are rejected even when old implementation files remain.
Schema `2.0` uses the legacy common transition/topology/hosting shapes. Schema
`2.1` uses structured trigger bindings but the legacy common hosting record.
Schema `2.2` adds the E1-local structured hosting evidence envelope. Schema
`2.3` replaces affordance exact-once with a multi-environment local-interface
contract. Schema `2.4` adds exact S1 universe digests, state-0 support options,
global capability facts/steps/authority/occurrence rules, and exact readiness
ledgers. Final submission and `run_e1()` generate only `2.4`.

`scripts/run_v2.py` is the sole E1 production runtime. Python controls lineage,
submission order, validation, sealing, and publication. The Agent authors every
environment, zone, interface, risk, topology, and transition contract; Python
does not template environment semantics.

## Controlled generation protocol

1. `start_e1_session()` accepts the current ready B0, S1, and W1 packages plus
   the coordinator-issued E1 gate. It requires `CODEX_THREAD_ID` and freezes
   the exact stage-owned implementation catalog; any owned runtime, schema, skill, or review
   validator change invalidates the session before another phase can seal.
2. The session freezes the exact three completions, gate, pre-stage state,
   source hashes, B0 controls, S1 storylines, complete S1 environment and event
   requirements, W1 rules, and complete W1 environment-demand objects.
3. The Agent submits exactly five phases in order. Each phase validates its
   complete available contract before evidence is written:
   `environment-demand-scan`, `environment-architecture`,
   `zones-and-topology`, `storyline-hosting-test`, and
   `final-environment-model`.
4. Before phase 3 seals, `start_e1_authority_semantic_review()` freezes the
   candidate, session, input gate, P1/P2 evidence, S1/W1 manifests and
   completions, exact upstream pointers/value hashes, implementation, schema,
   and protocol. A different authenticated reviewer task must cover every
   authority and capability-source claim and return a sealed task receipt.
5. Before phase 4 seals, `start_e1_hosting_semantic_review()` freezes the same
   chain through P3, the accepted authority review, and the exact P4 candidate.
   A different reviewer task must cover every transition, connection,
   milestone, obligation, occurrence, ambient-host, and initial-option claim;
   every claim verdict and record check must pass.
6. Every evidence record binds all frozen inputs, implementation catalog,
   thread, payload hash, previous evidence hash, and, at phase 4, the accepted
   semantic-review artifact. Earlier payloads must equal final-model
   projections; phase 5 checks this before writing evidence.
7. `run_e1()` validates, packages, seals the completion, asks the coordinator
   to accept it, and only then publishes E1.

A one-shot model or backfilled evidence is not accepted. Any B0, S1, or W1
change requires a new session and new Agent-authored payloads.

## Ready guarantees

- `storyline_environment_requirements` exactly equals S1 output and
  `environment_demands` exactly equals W1 output;
- four P1 digest objects bind the complete S1 transition, milestone,
  connection, and obligation universes to the sealed S1 canonical artifact;
  validators recompute the canonical items, counts, pointers, and hashes;
- every state-0 S1 anchor has at least one deterministic P2 support option.
  P4 realizes every option exactly once with local P3 facts, steps, ambient
  hosts, and/or topology appropriate to its closed descriptor;
- every schema-2.2/2.3/2.4 hosting record jointly binds exactly one S1 environment
  requirement and one W1 environment demand for the same storyline; it stores
  canonical responsibility hashes, every individual constraint hash, exact
  realization IDs, and restricted environment-local JSON pointers with local
  value hashes and rationales. Both source universes and both token universes
  are covered exactly once across the realization set;
- hosting evidence does not require responsibility or every constraint string
  to appear in every environment. Complete upstream responsibilities, trace
  envelopes, and foreign-line dumps are forbidden in environment definitions.
  A constraint that is already a local executable rule may remain verbatim in
  `access_rules`, `blockers`, or `hazards`; the independent reviewer decides
  semantic fitness. Constraint dumps in descriptive fields are rejected;
- every S1 storyline has a hosting path and every S1 event requirement has at
  least one usable affordance. One event requirement may have several
  affordances in distinct same-line hosting environments; T1, not E1, owns
  exact event coverage;
- every current-2.4 readiness use of a capability step closes through that
  step's affordance to an S1 event-requirement line. Transition claims and
  initial-option realizations serve their exact storyline; connection source
  and target endpoints serve their respective endpoint lines; each transport
  step serves at least one endpoint line; and a direct-obligation step serves
  the anchor-support line selected by its owned occurrence binding. These
  checks run before review artifacts or phase evidence are written;
- schema 2.4 covers every adjacent S1 state transition, milestone, connection,
  and story obligation exactly once. Each support mode belongs to its step,
  constrain-only support requires a reviewed local ambient host, associative
  connections cannot be causalized, and causal connections require local
  endpoint steps, a producer-to-consumer transfer fact, and a continuous
  direction-valid topology path when environments differ. A target endpoint
  that consumes the transfer fact cannot also support a target-line transition
  structurally before the connection anchor; this prevents a hidden backward
  prerequisite while allowing reviewed reuse at or after the anchor;
- capability facts use a closed S1/W1/E1 source-anchor branch with an exact
  sealed artifact, JSON Pointer, and value hash. Story states also bind line
  and state index; noninitial story facts require the precise predecessor
  transition instead of claiming root status. E1-local initial anchors point
  only into sealed P2 environment `state_vocabulary`, `resources`, or
  `access_rules`; their environment/resource/authority subject ID is derived
  from the exact environment, kind, pointer, and value rather than self-reported;
- fact producer/consumer sets and step produces/requires sets are exact
  inverses; the global bipartite prerequisite graph is acyclic. Authority
  tokens have typed issuer/consumer scopes using exact
  environment/affordance/action triples, and actor bindings project token facts
  and token kinds exactly. Occurrence cardinality and sharing are explicit;
- `producer_transition_keys` and `cross_line_dependency` are projected into
  that same global transition/fact/step DAG. A producer support step must
  actually produce the fact, and a consumer transition's exact required-fact
  projection must equal the facts required by its support steps. Producer and
  consumer transition keys are recomputed from those projections rather than
  trusted as declarations. `structurally_precedes` requires a continuous path
  of sealed S1 line-order, causal-connection, or obligation edge IDs. Only
  `causes` and `strict_before` obligations are strict edges; `not_before`
  permits equality and is not added to the strict DAG. An incomparable
  candidate carries no path and is accepted only
  when neither structural direction is reachable. Future and contradictory
  dependencies fail before phase evidence is written;
- connection endpoint steps belong to the exact source and target anchor
  support sets, not merely the same storyline. At state zero the exact anchor
  set is the union of every realized initial-support option for that line,
  independent of option order. Obligation `direct_path` records carry nonempty
  step, fact, and occurrence sets whose step projections match the recorded
  facts exactly. `obligation_occurrence_bindings` project occurrences by exact
  obligation, occurrence, step and selected support ID, rather than collecting
  every global occurrence on a shared step. Each direct step has an owned
  occurrence; a single occurrence cannot be rebound to another obligation.
  `inherited_anchor_path` records select
  complete anchor support and may not add facts, steps, or occurrences.
  Allowed and forbidden disclosure fact sets are disjoint;
- both 2.4 semantic reviews bind every source by sealed artifact, JSON Pointer,
  and value hash. The reviewer first seals `review-task-output.json`; its
  receipt binds task, producer, reviewer, output artifact/hash, request, and
  verdict payload. Self-reported or all-zero digests are not review evidence;
- every affordance action belongs to its environment's `allowed_actions`, its
  EVD lines are hosted by that environment, and its normalized semantic
  signature is unique. A local action plus a foreign action is rejected as a
  bypass. Shared environments contribute only constraints for lines served by
  that affordance;
- environments have distinct narrative duties, observable sensory conditions,
  access, resources, actions, blockers, hazards, state vocabulary, and
  transitions;
- zones, topology, permissions, resource/information channels, hazards,
  affordances, and transitions have closed references;
- the environment graph is reachable; each environment binds its incident
  connections and at least one zone, authority interface, channel, hazard, and
  transition;
- access evidence, affordance constraints, and transition permissions preserve
  the exact W1 support rules instead of providing a bypass;
- each phase-3 transition and the phase-3 affordance catalog seal together.
  Each structured trigger binding fixes a forward trigger ID,
  source environment and S1 state anchor, target S1 state anchor, causal
  evidence, and explicit topology path. `trigger_ids` equals the set of
  binding trigger IDs, and all triggers/bindings are required (all-of);
- the same trigger may have multiple state bindings. Same-environment bindings
  still require real hosted source/target anchors. Cross-environment bindings
  require a continuous, cycle-free path through direction-aware E1 topology;
  every path edge must expose the binding's exact `transport_capability`.
  Local bindings use an empty path and capability `local`; cross-environment
  bindings must use a non-local capability;
  cross-storyline bindings additionally require an exact causal S1 connection
  or a `causes`/`requires_all` obligation. Every `requires_all` antecedent must
  be covered, and optional melody may not drive a non-optional target;
- the optional-line rule is a structural S1 authority guard. Whether a concrete
  environment-state change is semantically optional still requires Agent design
  judgment and review; the runtime does not infer that meaning from state prose;
- phase 4 and final validation resolve each forward trigger ID to an authored
  affordance, require its environment to equal the binding source environment,
  and require at least one of its bound event requirements to belong to the
  source storyline. Legacy 2.0-2.2 packages retain their historical
  exact-once affordance semantics;
- every binding's transition permission set must include at least one access
  assignment governed by its source environment and at least one governed by
  its target environment (one local assignment may satisfy both);
- each resource/information channel uses exact `[DEMAND:id]`,
  `[SUPPORT:id]`, `[MARKER_SHA256:hash]`, and `[ACTION_SHA256:hash]` tokens to
  bind its hosted demand, complete W1 rule/system/institution support set,
  demand meaning, and an exposed environment action; substring matches and
  nonempty placeholder prose are not evidence;
- the local authority partition is pairwise-disjoint: locked/open equal B0,
  autonomous-owned equals all E1 decisions and governed entities (including
  affordances and transition contracts), and downstream-freedom equals the S1
  event-requirement IDs exactly;
- gate, B0, S1, W1, session, evidence, implementation, manifest, validation,
  completion, and coordinator transition share one immutable lineage.

`validate_e1_package()` is read-only and recomputes these guarantees. Resealing
hash declarations cannot replace semantic coverage, reachability, action
interfaces, world-rule consistency, boundary checks, or completion lineage.

## Boundary

E1 defines concrete reusable environments and the conditions under which later
events could act or transition state. It does not add storylines, decide event
time, initiator, occurrence, or result, create event objects, write scenes,
dialogue, camera direction, or character profiles. Those outputs are a hard
`E1_BOUNDARY_VIOLATION`. Package validation uses an allowlist, not filename
guessing: only the formal E1 root artifacts, the five exact phase-evidence
files, the exact `_implementation_paths()` target set, and exactly one sealed
`candidate.json`/`request.json`/`review.json`/`validation.json`/`manifest.json`
package under each phase-3 authority-review and phase-4 transition-review
candidate hash, plus formal
`sources/B0|S1|W1/**` inputs may exist. A second candidate directory or any
other review file is a boundary violation. Each phase evidence references its
review package manifest, whose complete artifact set and hashes are publicly
recomputed. Implementation files must also equal the execution
catalog, execution implementation list, and manifest implementation list. Any
other path is rejected regardless of its name; the formal
`environment-preview.md` remains allowed.

Existing E1 attempt evidence is immutable. An implementation-catalog change
invalidates its session and requires a new attempt. Historical 2.0/2.2/2.3
packages are accepted only under their explicit semantic branch plus trusted
runtime/schema pair and exact released manifest/completion/canonical identity;
they are never rewritten as 2.4. An earlier attempt's sealed evidence, review
package, or candidate is never reused after any bound source changes.
