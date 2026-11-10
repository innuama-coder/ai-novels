# C1 runtime contract

## 1. Purpose and ownership

`novel-character-system-designer` is the controlled generative stage C1. It
resolves the character slots frozen by S1 and used by T1 into canonical
characters, then defines only character-owned semantics:

- story responsibility, goals, values and two kinds of boundary;
- story position across entry, ongoing development and ending;
- exact storyline, event and environment participation plus causal contribution;
- conception-level individual definition: recognizable appearance, personality,
  life background, occupation/daily life, social circle and embodied/interface limits;
- capability, authority and information limits at the time of a frozen event;
- available choices, chosen action, cost and non-delegable choice;
- character arcs, relationship functions and relationship levers;
- Agent-selected core characters and their graph-distance 1/2/3 networks;
- exact storyline cast, event cast and terminal-aftermath responsibility.

C1 does not revise storylines, world rules, environments, event order, event
participants, initiating actions, observable results, scenes, chapters,
dialogue, prose, exhaustive biographies, wardrobe catalogs or scene-level
performance. Stable individual controls are required and are not treated as
prose development. If a credible character cannot perform a
frozen T1 event, C1 returns the problem to T1 or the actual earlier owner.

Python is a controller and validator. It never invents names, motives,
relationships, choices or character prose.

## 2. Hard admission

The runner accepts exactly:

1. a current B0 package;
2. a current S1 package descended from that B0;
3. a current W1 package descended from that B0 and S1;
4. a current E1 package descended from that B0, S1 and W1;
5. a current T1 package descended from that B0, S1, W1 and E1;
6. a coordinator-issued C1 input gate whose upstream completion list is
   exactly `[S1,W1,E1,T1]`;
7. a non-empty `CODEX_THREAD_ID`.

All five canonical models must have the same `run_id`. Every copied upstream
completion hash is compared to the current package. Gate content, gate hash,
run-state and return binding are fail-closed.

The sealed gate is authoritative for every upstream completion's canonical
logical path. Both legacy flat paths (`T1/stage-completion.json`) and immutable
attempt-qualified paths are accepted, but backslashes, absolute paths and path
escapes are rejected. A logical completion path must bind the canonical/raw
completion body plus same-parent manifest and validation hashes. Physical
source roots may use different directory names, including Windows
extended-length paths. Session admission and public package replay apply the
same full B0-to-T1 nested completion-lineage proof before any write.

S1 `character_requirements` are copied exactly to C1 `character_demands`.
Every S1 actor slot must occur in T1 and every T1 participant, initiator and
counter slot must resolve to the exact S1 slot universe. C1 returns instead of
guessing when this topology is incomplete.

T1 must contain at least one real `information_change`. C1 does not fabricate
information movement merely to satisfy the character schema.

## 3. Controlled five-phase session

The controller freezes all B0/S1/W1/E1/T1 source hashes and semantic bindings
in `generation-session.json`. A controlled Agent must submit these phases in
order:

| sequence | phase | exact payload |
| --- | --- | --- |
| 1 | `character-demand-scan` | `character_demands` |
| 2 | `slot-resolution-and-profiles` | `design_decisions`, `slot_resolution`, `profiles` |
| 3 | `agency-and-relationships` | `responsibility_matrix`, `agency_matrix`, `information_matrix`, `character_arcs`, `relationships`, `three_layer_networks` |
| 4 | `cross-model-cast-test` | `storyline_cast_coverage`, `event_cast_coverage`, `aftermath_responsibility`, `development_freedoms`, `authority_partition`, `derivation_claims`, `open_items` |
| 5 | `final-character-model` | `model` |

Each evidence record binds the session, previous evidence hash and canonical
payload hash. Non-final payloads must equal the corresponding fields of the
final model. The finalizer reads the sealed final workspace; it has no model
parameter and cannot accept an unrecorded replacement.

## 4. Slot and profile rules

- The resolved slot set equals the frozen S1/T1 slot set.
- Each slot has exactly one `slot_resolution`.
- Its `event_ids` equal the exact reverse event index for that slot.
- Its `demand_ids` equal the exact reverse S1 demand projection.
- Each slot rationale contains one exact per-demand block
  `[DEMAND:<CHD>:<semantic_hash>]...exact CHD responsibility...[/DEMAND]`.
  The hash covers that CHD's responsibility, sources, required capability,
  constraints, acceptance checks and downstream freedom; the block also
  preserves the exact human-readable responsibility, so it is not an unused
  aggregate hash.
- Multiple slots may map to one character only when a C1 decision binds the
  exact sorted slot-set digest and no event makes that character both
  initiator and counter.
- Profiles equal resolved characters plus explicit relationship-extension
  characters. Every extension must remain structurally necessary through a
  relationship function; unreferenced profiles are orphans and fail.
- Names begin with `[CLASS:core]` or `[CLASS:support]`; the classification is a
  C1 decision, not a profession template.
- Every profile contains story responsibility, non-empty goals and values,
  one `[TYPE:blind-spot]` boundary, one `[TYPE:hard-boundary]` boundary,
  pressure behavior, agency choices, non-delegable choices, information
  limits and arc direction. Capability and authority arrays may honestly be
  empty when no frozen event duty requires them.
- For a resolved character, `story_responsibility` contains the exact demand
  blocks for the union of its slots. Its goals and hard boundaries contain
  per-demand `DEMAND_EFFECT` bindings with non-placeholder explanations.
  Relationship-extension characters with no CHD do not receive fake demand
  bindings.
- Every profile contains one story position with entry, ongoing and ending
  functions. Narrative level is `core`, `support` or `context` and must agree
  with the name classification for core/support profiles.
- Every resolved profile's `activity_participation.storyline_ids`, `event_ids`
  and `environment_ids` equal the exact reverse projection of its resolved
  slots through S1/T1. Relationship-extension profiles may use empty reference
  sets, but must describe the relationship activity and causal contribution.
- Every profile contains non-placeholder individual controls for appearance,
  personality, life background, occupation/daily life, social circle and
  embodied/interface limits. “Unknown”, “待定” and generic role labels are not
  acceptable substitutes. A non-human or disembodied character states that
  condition explicitly instead of receiving a fabricated human appearance.

## 5. Seven structural duties

The runtime derives obligations from frozen inputs, not from prose:

1. `decision` for every event initiator;
2. `information` for every T1 information visibility slot and change event;
3. `capability` for every event participant;
4. `counteraction` for every counter slot;
5. `relationship-pressure` for every storyline actor slot;
6. `action` for every event initiator;
7. `aftermath` for the initiator of each storyline terminal event.

`responsibility_matrix` covers each derived obligation exactly once. Every row
binds `[KIND:*]`, `[SLOT:*]` and exact source IDs. A decision row also binds the
canonical hashes of the responsible profile's goals and values. Event
responsibility alone is sufficient to justify a character; no arbitrary
relationship or biography quota is imposed.

Each assignment's formal constraints also contain exactly the per-CHD
semantic bindings projected through its slot. This makes a changed CHD alter
the applicable structural duties, not merely the phase-1 demand copy.

## 6. Event feasibility and agency

Every initiator and counter has agency at that event. An agency record has at
least two genuine options, the chosen action is one of them, and the cost is
non-placeholder. Its chosen action retains human-readable text and binds the
exact set of event-role obligations it covers:

- `[INIT_ACTION:<event_id>:<initiating_action_hash>]` for each initiator duty;
- `[COUNTER_PRESSURE:<event_id>:<complication_hash>]` for each counter duty.

The set may span several events, but it may neither omit nor add an event-role
binding. Every frozen initiator/counter obligation is owned exactly once.
Chosen action, cost and the matching arc theme also bind the canonical digest
of that character's demand-derived `story_responsibility`, while retaining
human-readable event choices and costs.

For each frozen event:

- the initiator profile has
  `[ACTION_SHA256:<hash of T1 initiating_action>]`;
- every participant has `[ENV_ACCESS:<environment_id>]`;
- every T1 state-ledger provider required for the event appears in the
  initiator's authorities;
- counter profiles have the applicable counter capability when counters
  exist.

These tokens prove feasibility without letting C1 rewrite the event.

## 7. Information and arcs

`information_matrix` covers exactly the characters whose slots occur in real
T1 `information_changes`; other characters are not forced into a fake change.
Each row binds its exact change events and has disjoint `knows`,
`does_not_know` and `misreads`. Known and unknown claims use
`[KNOWN_AFTER:<info>:<event>][BEFORE_SHA256:<hash>][AFTER_SHA256:<hash>]` and
`[UNKNOWN_BEFORE:<info>:<event>][BEFORE_SHA256:<hash>][AFTER_SHA256:<hash>]`.
For each visible character those token sets equal every real T1
information-change/event tuple exactly; unknown claims also occur in the
profile's `information_limits`.

Every character making an event choice has an arc. Arc choice events must be
events where that character has agency. Arc pressure events must be real
events connected to that character by participation, an explicit
responsibility or a relationship change. Stable relationship-extension
characters need not receive a fabricated growth arc.

## 8. Relationships and three layers

Relationships have two real character endpoints, an exact function token,
real change events, boundaries and distinct start/end states. Each profile's
`relationship_levers` equals its incident relationship IDs.

The controlled Agent chooses the core set in `DEC-C1-CORE`. The decision must
include a digest of the exact selected core IDs and must include at least one
true main-line initiator. It is forbidden to mechanically classify every main
slot, every initiator or every profile as core.

Each selected core has one network. Layers are the complete global
shortest-distance sets in the relationship graph:

- layer 1: shortest relationship distance 1;
- layer 2: shortest relationship distance 2;
- layer 3: shortest relationship distance 3.

No real character at distance 1, 2 or 3 may be omitted or placed in another
layer. The three sets are non-empty, disjoint and do not contain the core. Existing
slot/event characters may occupy any layer; institutional or contextual
characters may also participate in events. Layer names are not fixed
character categories. A network need not contain every profile.

## 9. Exact closure and governance

- Storyline cast coverage equals resolved characters for every S1 storyline
  slot set.
- Event cast coverage equals resolved characters for every T1 participant
  set.
- Each coverage evidence field contains the exact set of
  `[CHAIN:<CHD>:<semantic_hash>:<SLOT>:<CHR>:<SL-or-EV>]` records, proving the
  CHD→slot→character→storyline/event responsibility chain bidirectionally.
- Every storyline terminal event has exactly one aftermath owner: its frozen
  initiator.
- No profile may be removed without losing an event/slot duty, relationship
  function or aftermath duty.
- `author_locked` and `author_open` equal B0 exactly.
- `autonomous_owned` equals every C1-generated authoritative ID in the governed
  fields after subtracting both exact B0 authority sets. A canonical profile may
  preserve an author-locked/open B0 identifier without transferring ownership
  to C1. The set also excludes every `DEV-` ID.
- `development_freedoms` uses unique `DEV-` IDs. Its subject union equals the
  canonical character set, every subject is a profile, every source resolves to
  a frozen input or authoritative C1 object, and scope/allowed/forbidden/check
  text is non-placeholder.
- `downstream_freedom` equals the `development_freedoms` ID set, not the
  canonical character set.
- author-locked, autonomous-owned, downstream-freedom and author-open are
  pairwise disjoint.
- Every design decision is owned by C1 and selects one declared option.
- Every profile, arc and relationship has a recomputable derivation claim.
  Each resolved profile claim also names exactly that character's CHD sources.
- Open items preserve every B0 author-open control exactly.

## 10. Package and acceptance

The package allowlist is:

- `input-gate.json`
- `character-system.json`
- `generation-session.json`
- `generation-evidence/*.json`
- `generation-evidence-index.json`
- `execution-record.json`
- `character-preview.md`
- `validation.json`
- `package-manifest.json`
- `stage-completion.json`
- `implementation/*`
- exact copied `sources/B0`, `sources/S1`, `sources/W1`, `sources/E1`,
  `sources/T1`.

The finalizer validates the package before and after completion sealing,
records the exact implementation catalog, asks the coordinator to accept the
completion and only then atomically installs the package. Existing
destinations fail closed. Any mutation of a canonical model, source,
manifest, gate, session, evidence link, implementation file, validation or
completion hash invalidates the package.

Ready means all admission, schema, responsibility, feasibility, information,
relationship-network, cast, terminal-development-freedom, governance,
evidence, manifest and completion checks pass. It does not mean scenes or
prose have been developed. A legacy model without `development_freedoms`
fails schema validation and must be regenerated.
