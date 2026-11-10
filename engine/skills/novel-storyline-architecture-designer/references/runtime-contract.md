# S1 V2 runtime contract

## Bounded current-session correction: cause and design

The prior current-session shape made four independent decisions collide: a
numbered adjacency candidate had to look relational even when an independent
review rejected the relation; numbered normative constraints lacked exact
source-to-dimension provenance; structural closure assumed convergence was the
only legitimate ending; and connection identity was checked without a unique
physical endpoint/relation key or target-first-occurrence timing. As a result,
valid no-relation and terminal-consequence designs could fail while duplicate
or belated edge declarations remained under-specified.

Current sessions therefore add only the following bounded declarations:

- `non_relational_candidate` records a reviewed no-relation disposition for a
  candidate ordered link and carries no anchors, reservation, fulfillment, or
  consistency dimension;
- `consistency_constraint` atoms declare a non-empty unique set of consistency
  dimensions, and each matching consistency record exact-covers its source atom
  and control provenance outside generic witness IDs;
- every structural line declares whether it converges to the main line or is a
  terminal consequence entered causally from the structural trunk, with exact
  source anchor and entry connection declarations for the latter;
- physical connections are unique by exact endpoint plus relation, and causal
  connections are registered at the target state's first milestone occurrence.

The independent reviews must judge candidate no-relation dispositions and each
source consistency claim/failure separately. They must not invent an
uncontrolled antecedent merely to avoid a realization collision. Historical
packages remain readable under their frozen session markers; the new fields
and exact semantic gates are mandatory only for newly started sessions.

`scripts/run_v2.py` is the sole production runtime for S1. Python controls
lineage, order, validation, sealing, and publication; the Agent authors every
semantic design field. The runtime must not synthesize storylines or silently
repair an Agent submission.

## Controlled generation protocol

1. Call `start_s1_session()` with the current B0 package and coordinator-issued
   S1 gate. It requires `CODEX_THREAD_ID` and freezes the exact gate, B0
   completion, run state, B0 source hashes, and each control's ID, domain,
   heading, value hash, source artifact, and stable `control:<ID>` selector.
2. Let the Agent read the frozen inputs and call `submit_s1_phase()` exactly
   once, in order, for `demand-scan`, `line-design`,
   `topology-and-consistency`, `downstream-requirements`, and
   `final-storyline-model`.
3. Each phase accepts only its declared fields. Its evidence binds the session,
   thread, gate, pre-stage state, B0 completion, complete control bindings,
   previous evidence hash, and payload hash.
4. Call `run_s1()` with that controlled workspace. It reads the final model from
   the fifth evidence record, verifies that all earlier payloads equal the
   corresponding final-model projections, validates the package, seals the
   completion, asks the coordinator to accept it, and only then publishes it.

A one-shot candidate model is not a production input. Evidence may not be
backfilled after generating a model. Changing a source control value requires a
new frozen session and new Agent-authored phase payloads.

Construct phase payloads as Unicode objects and pass them directly to
`submit_s1_phase()`. Do not round-trip semantic text through a Windows default
code page, shell redirection, or a text writer without explicit UTF-8. The
runtime writes canonical JSON with UTF-8 itself. Before any phase evidence is
written, the submit gate recursively rejects U+FFFD, three or more consecutive
ASCII question marks, `锟斤拷`, and repeated high-confidence UTF-8/Latin-1
mojibake pairs with `S1_TEXT_ENCODING_CORRUPT`. A normal Chinese question mark
or a single ASCII `?` remains valid. The same deep check runs during final-model
and read-only package validation.

Every `submit_s1_phase()` call also runs the semantic checks that can be decided
at that phase, before writing its evidence record. The check always rereads and
verifies the sealed payloads of all preceding phases; later phases cannot repair
or reinterpret an earlier accepted payload.

- `demand-scan` requires an exact one-to-one B0 control mapping, valid source
  control IDs, and literal participation of the complete author heading and
  value in the demand obligation.
- `line-design` derives each demand's realized line from literal heading/value
  participation and requires an exact match with the declared realization. It
  also checks real-line decision projection, reciprocal decision provenance,
  complete source-control participation in a projected decision, and the
  author-open/optional authority boundary. Its `line_claim_authority` ledger
  must exactly equal the runtime's non-overlapping span decomposition of every
  conclusion-bearing storyline and decision text leaf. Exact B0 heading/value
  spans are separated from every residual span; pointer, offsets, text, and
  hash must bind without a gap or overlap. A `source_bound` span must equal its
  source fragment, never merely contain it. New sessions also require
  `source_sequence_realizations` to exact-cover every source unit whose
  `relation_mode=required` or `kind=ordered_link`. Each record binds one source
  unit either to exact from/to semantic state anchors (`within_line` or
  `cross_line`) or to a non-state `semantic_constraint`. A within-line
  transition must move to a later state and carries null boundary anchors. A
  cross-line transition also declares exact `boundary_from_anchor` and
  `boundary_to_anchor`. The source semantic anchor must reach the source
  boundary by forward same-line order, and the target boundary must reach the
  target semantic anchor by forward same-line order. Direct cross-line
  realization uses semantic endpoints as its boundaries. The transition must
  reserve one connection ID listed by both boundary-owner lines;
  different ordered transitions may not reuse that reservation. Before phase 2
  seals, a line-level realizability graph treats each reservation as a fixed
  directed edge and each connection ID shared by exactly two lines but unused
  by every reservation as potential capacity in either direction. Every
  current non-main, non-optional structural line must declare its closure mode.
  A `converges_to_main` line must be able to reach the main line in that graph;
  a `terminal_consequence` must instead reserve an entry from an exact anchor
  on the non-terminal structural trunk. An unproved declaration fails with
  `S1_SOURCE_SEQUENCE_STRUCTURAL_CLOSURE_MISSING` or its specific closure error.
  Potential edges prove only capacity; phase 3 must choose actual directions
  and still pass the state DAG and structural state-closure gates. A semantic
  constraint has null semantic
  anchors, null boundary anchors, and a null reservation, plus a concrete
  rationale, a
  `phase3_fulfillment_kind`, and its matching `expected_witness_type`. This
  disposition is only for narrative norms, information boundaries, evaluation
  rules, and comparable non-state semantics; it is not an escape hatch for a
  causal or character-development sequence.
  A candidate `ordered_link` may instead use
  `realization_scope=non_relational_candidate` after independent review. That
  record has null semantic anchors, boundary anchors, reservation,
  fulfillment, witness type, and consistency dimension. Required relations
  cannot use it. Current storylines also declare closure explicitly: main and
  optional lines use null closure fields, each other structural line uses
  `converges_to_main` or `terminal_consequence`, and a terminal consequence
  identifies an exact structural-trunk source anchor and shared entry
  connection reservation.
- `topology-and-consistency` first combines the sealed demand and line phases
  with the candidate topology, then validates that view against the canonical
  schema's composable `upstreamPhasePayload` definition before any review
  request or phase evidence can be written. That definition reuses the same
  demand, line, and `topologyPhasePayload` property contracts as the final
  model, so nested forbidden fields and local cardinality constraints fail in
  phase 3 without requiring phase-4 fields. The combined view then runs the
  shared prefix of final-model semantic validation. This single owner covers
  accepted line design, endpoints, state bindings, reciprocal connection
  indexes, causal order, temporal phases and milestones, global temporal
  semantics, narrative markers, cross-line consistency, and every story
  obligation decidable from the current topology. The final-model gate runs
  that exact prefix before its phase-4 realization and envelope checks. Every
  reserved source-sequence connection must exist under the same ID and use the
  exact phase-2 boundary direction, line IDs, state indexes, and state text.
  Only those boundary states must co-occur in the connection's milestone;
  semantic endpoints are reached through the declared same-line ordering. Each
  semantic constraint must own at least one non-`non_relational` source atom,
  and every such atom must be traceable with its source control to the declared
  obligation, narrative marker, or consistency witness. A consistency
  fulfillment also declares its exact `consistency_dimension`.
  Only atom/control IDs traced from that phase-2 declaration are added to that
  dimension's consistency witness allow-list; another dimension and every
  undeclared ID remain invalid. Before this phase can be sealed, a distinct
  reviewer must pass the immutable
  topology-and-information semantic request described below.
  In the current contract, numbered normative source units use
  `atom_kind=consistency_constraint` with a non-empty unique
  `consistency_dimensions` list. Each `(atom, dimension)` pair appears exactly
  once in that dimension check's `source_claim_atom_ids`; its exact control
  appears in `source_control_ids`, and the atom claim participates in both the
  check claim and failure condition. These provenance IDs are forbidden in
  generic `witness_ids`. Historical semantic-constraint consistency evidence
  retains its narrow witness allow-list.
- `downstream-requirements` builds the complete candidate from the four sealed
  phase payloads and runs the full model validator. The final phase must equal
  those sealed projections and passes the same validator again.

Failures are closed before phase evidence is written, with stable phase-specific
codes: `S1_DEMAND_PHASE_SEMANTIC_INVALID`,
`S1_LINE_PHASE_SEMANTIC_INVALID`, `S1_TOPOLOGY_PHASE_SEMANTIC_INVALID`,
`S1_DOWNSTREAM_PHASE_SEMANTIC_INVALID`, or
`S1_FINAL_PHASE_SEMANTIC_INVALID`. These checks intentionally validate source
participation and authority provenance rather than trying to recognize names or
other story-specific vocabulary.

### Independent line-claim and source-sequence review

The production call order around the second phase is fixed:

1. Call `inspect_s1_line_claims(line_payload, controls)` to obtain the exact
   span universe, then author one `line_claim_authority` disposition for every
   span. The four allowed dispositions are `source_bound`,
   `s1_structural_derivation`, `downstream_requirement`, and `open_item`.
2. From the frozen generation thread call `start_s1_line_claim_review()` with
   the complete line payload. It mechanically validates the ledger and writes
   an immutable request under the candidate hash.
3. From a different authenticated `CODEX_THREAD_ID`, call
   `submit_s1_line_claim_review(..., review=envelope)`. The envelope must contain
   exactly `claim_verdicts` and `source_sequence_verdicts`; each list supplies
   one ordered `pass|fail` verdict and concrete rationale for every requested
   claim or realization. The reviewer must reject a structurally valid mapping
   when an endpoint is semantically too early to realize the complete ordered
   source step. For a cross-line causal path, inspect neighboring states and
   surrounding context at both semantic and boundary anchors. The rationale
   must separately explain why the semantic endpoints realize the complete
   source step and why the boundary pair is a valid implementation exit/entry;
   a later boundary must never replace the semantic endpoint. The review binds
   the request hash, candidate hash,
   claim-register hash, source-sequence-register hash, session, generation
   thread, and reviewer thread. Current sessions never synthesize pass verdicts.
   The reviewer independently judges the realization disposition: arbitrary
   state anchors do not realize a narration-wide rule, and a global causal
   spine may not be relabeled `semantic_constraint` merely to avoid anchors.
   A candidate numbered adjacency may pass as `non_relational_candidate` only
   when its source has no relation to promote. The reviewer must not create an
   uncited antecedent merely to avoid a collision with another realization.
4. Return to the frozen generation thread and call
   `submit_s1_phase(..., phase="line-design", ...)`. The phase is sealed only
   when the same candidate has a complete all-pass independent review.

A failed review never writes `02-line-design.json`. Revise the candidate,
rebuild its span ledger, and repeat the review under the new candidate hash;
the rejected review remains immutable and cannot contaminate the new attempt.
`downstream_requirement` and `open_item` spans are explicitly non-canonical.
The full-model gate later requires their referenced requirement/open-item
objects to exist and carry the exact span text.

New sessions carry
`line_review_protocol=line-claim-and-source-sequence-semantics-v2`. Their review
request exposes `review_protocol`, `source_sequence_realization_count`,
`source_sequence_register_sha256`, `source_sequence_realization_ids`, and the
exact `ordered_source_units`. Read-only package validation accepts historical
sessions without this marker and their legacy line-review evidence, but a newly
started production session cannot select the legacy field set or `verdicts=`
submission path.

### Independent topology and information review

After sealing `line-design`, the generation thread calls
`start_s1_topology_semantic_review()` with the exact third-phase payload. The
runtime first applies all mechanical topology checks, then freezes a request
under `topology-semantic-reviews/<candidate-sha256>/request.json`. A different
authenticated thread calls `submit_s1_topology_semantic_review()` and supplies
the six verdicts in this fixed order: `time`, `causality`, `information`,
`state`, `source-sequence`, and `overcorrection`.

The request contains a deterministic `coverage_universe`. Verdict evidence is
an exact cover, not a sample: all source-declared ordered transitions, every
milestone-bound state conclusion, both endpoints of every causal or associative
connection, every information atom, and every visibility-bound locked control
must be accounted for by the declared source IDs, candidate JSON pointers,
object witnesses, source order, and milestone order. A visibility control must
either own a complete unknown/first-disclosure pair or appear in an audited
`visibility_exemptions` record with a concrete justification and candidate
witness IDs. The review binds the exact candidate hash, line-design hash,
session, generation thread, reviewer thread, request hash, source IDs, and JSON
pointers. Any missing, duplicate, surplus, stale, or reordered evidence fails
closed. All six verdicts must pass before phase 3 and final publication.
For current sessions the coverage universe also exposes every reviewed
non-relational candidate and every consistency-constraint atom, pointer, and
dimension list. Reviewers check each source atom against the exact consistency
claim and distinct failure condition; generic witnesses never stand in for
source provenance.

Sessions carrying `semantic_review_protocol=topology-information-semantics-v1`
use this gate. Read-only validation continues to recognize historical packages
that predate the marker, while every newly started session carries the marker
and cannot use the legacy path.

## Ready guarantees

- every B0 control has exactly one demand, and the demand carries its exact
  heading and value;
- every demand is realized exactly once and exactly one main line exists;
- one canonical state-causal graph uses `(storyline_id, state_index)` nodes,
  adjacent-state forward edges within each line, and exact `causal` connection
  endpoints across lines. The complete graph is acyclic;
- from state index `0`, every `converges_to_main` line reaches at least one
  main-line state in that graph, possibly through another structural line. A
  `terminal_consequence` instead is reached through its single declared causal
  entry from the non-terminal structural trunk, reaches its own terminal state,
  and has no causal outbound edge;
- every `optional_melody` has at least one `associative` attachment to a
  structural line, has no causal cross-line connection, and is excluded from
  structural causal closure; this also prevents author-open optional material
  from becoming a required causal predecessor;
- every connection declares `relation=causal|associative`; its state text and
  zero-based state index identify the same state on the declared owner line,
  and both endpoint lines list the connection exactly once;
- current connections are unique by the exact tuple of relation, directed line
  endpoints, state indexes, and state text. A second ID cannot duplicate one
  physical edge. A causal connection is registered in exactly the milestone
  where its target state first appears, never in a later milestone;
- a `converges_to_main` structural line retains the canonical state path into
  main. A `terminal_consequence` instead has one declared causal entry from the
  non-terminal structural trunk to its own line, can walk forward to its end,
  and has no causal outbound edge; it is a legal sink and is not forced back
  into main;
- `temporal_architecture` provides one shared time spine for the complete
  multi-line design. Phases are strictly ordered, milestones cannot regress in
  phase or in any line's state index, every structural line reaches both its
  declared start and end, and every cross-line connection is realized by
  exactly one milestone binding both endpoint states;
- every milestone carries at least one narrative marker. The marker vocabulary
  is fixed to `opening`, `setup`, `probe`, `turning_point`, `reveal`, `climax`,
  `payoff`, and `aftermath`. A ready package contains at least one setup,
  probe, turning point, climax, and payoff; probes expose a concrete reader
  question and observable signal, payoffs refer back to an earlier setup, and
  a climax converges at least two structural lines;
- `architecture.line_order` contains every line exactly once and controls only
  presentation order. It is not causal or temporal evidence; causal validity
  comes from the canonical state graph, so a legal early A -> B -> later A
  return is not rejected merely because its line-level projection is A <-> B;
- `story_claim_units` must equal the runtime's deterministic decomposition of
  every B0 control value. Explicit arrow chains produce one required unit for
  every adjacent link; numbered items, numbered adjacency candidates, table
  rows, sentences, and structured leaves remain separate units with exact
  pointers/offsets/text hashes. No domain-keyword inference is used;
- every source unit has exactly one `story_claim_atom`. A required arrow link
  must own one exclusive obligation. A numbered adjacency is only a candidate:
  it may be non-relational, but that disposition requires a concrete rationale
  and semantic review. Thus ordinary numbered classifications are not silently
  converted into chronology;
- `story_obligation_register` carries only `causes`, `strict_before`,
  `not_before`, `requires_all`, `first_disclosure`, and
  `must_remain_unknown`. Every record binds one or more locked B0 controls by
  exact artifact/hash/selector locators and binds each antecedent and consequent
  to a storyline ID, zero-based state index, and exact state text;
- `causes`, `strict_before`, and `not_before` have exactly one antecedent;
  `requires_all` has at least two; `first_disclosure` has one or more
  prerequisites plus one release anchor; `must_remain_unknown` has no
  antecedent and uses its consequent as the unknown-until anchor. Information
  obligations carry a stable `PROP-` ID and an explicit reader/character/both
  audience;
- same-line obligation edges must move forward, the combined temporal/causal
  obligation graph must be acyclic, and one proposition/audience pair may have
  only one first-disclosure record;
- the first occurrence of every scheduled state is ranked globally by
  `(milestone.order, state_refs position)`. Causal endpoints, `causes`,
  `requires_all`, and `not_before` may not reverse that order, while
  `strict_before` must be strictly earlier. Information windows are compared
  globally by `(proposition_id, audience)`, including deterministic ordering
  inside one milestone. Associative edges are not converted into causal order;
  their endpoints remain mandatory independent-review evidence;
- two independent causal/temporal/prerequisite claim atoms may not share an
  indistinguishable realization. Co-realization is permitted only for
  source-unordered semantics when both atoms declare one common group, a
  concrete justification, and witness IDs. Required and ordered-link source
  transitions fail closed even when co-realization metadata is present;
- every antecedent of `causes` and `requires_all` must reach its consequent in
  the state-aware implementation graph: adjacent states provide forward
  within-line edges and only exact `relation=causal` SLC endpoints provide
  cross-line edges. Earlier reverse connections and associative connections do
  not count. `strict_before` and `not_before` remain temporal constraints and
  do not require a causal SLC path;
- `story_obligation_coverage` equals the B0 control set exactly and reverse
  indexes the exact union of each control's atom IDs and obligation IDs. One
  control may own many of both. Locked controls are `obligated`, `mixed`, or
  `no_relational_obligation`; reviewable non-relational dispositions remain
  visible. Author-open controls remain `author_open` and cannot be promoted;
- cross-line consistency contains exactly one structured record for each of
  `time`, `causality`, `information`, `authority`, `state`, and `theme`;
  every record witnesses every storyline and carries a concrete claim plus a
  distinct failure condition;
- witness IDs are checked against dimension-specific object sets. Causality
  accepts only storyline IDs and connections whose declared relation is
  `causal`; an associative connection can never be used as causal evidence.
  Unknown witnesses, incomplete line coverage, duplicate/missing dimensions,
  and placeholder claims or failure conditions fail closed;
- the relevant source value participates in its line and in each W1/E1/T1/C1
  requirement;
- every downstream requirement set covers every line and its assigned demands
  exactly once, targets the correct stage, and equals the downstream authority
  partition;
- the local authority partition is pairwise-disjoint and exact:
  `author_locked`/`author_open` equal B0, `autonomous_owned` equals S1
  decisions, storylines, temporal objects, story obligations, and obligation
  coverage records, and `downstream_freedom` equals the union of all W1/E1/T1/C1
  requirement IDs;
- author-open controls remain open; derivation hashes are current;
- model, session, evidence chain, execution record, implementation snapshots,
  manifest, validation, stage completion, and coordinator transition bind the
  same run, gate, B0 completion, and pre-stage state.

`validate_s1_package()` is read-only. It rereads and schema-validates the copied
B0 package, stored gate, model, manifest, and stage completion; recomputes
semantic set equalities, topology, source-value participation, hashes, session
identity, evidence chain, implementation freshness, and completion lineage.
Deleting or resealing declarations cannot replace these checks. A package
without a valid `stage-completion.json` is not ready.

## Boundary

S1 defines machine-consumable story obligations, lines, causal topology,
non-causal associations, state transitions, the shared multi-line temporal
spine, narrative markers, and downstream requirements. An association is
coverage and resonance, never a causal predecessor. S1 milestones and
obligation anchors are abstract story states:
they say what develops and changes, not where a scene occurs or how it is
dramatized. S1 does not define world rules, concrete environments, event
records, character profiles, chapters, scenes, or POV schedules.
Downstream requirements state obligations and acceptance checks, not downstream
answers. Published output paths are immutable.
