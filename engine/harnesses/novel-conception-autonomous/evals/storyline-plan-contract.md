# Storyline plan v1 contract

## Purpose

The contract provides a generic, versioned input for a test Agent's autonomous
S1 proposal.  It replaces mechanical “one control, one storyline” fixture
templates without hard-coding any novel in adapter code.

JSON Schema validates closed object shapes, constants, primitive types and ID
formats.  `storyline_plan.py` validates hashes, inventories, graph relations,
authority and exact coverage.  Both layers are mandatory.

## Manifest contract

The manifest contains exactly:

- `schema_version = 1.0`
- `kind = novel-conception-eval-case`
- one stable `manifest_id`
- `fixture`
- `storyline_plan`
- `storyline_plan_schema`
- `storyline_quality_gate`
- `storyline_quality_gate_schema`

Each artifact reference contains exactly `path` and `sha256`.  The plan-schema
and quality-schema paths are fixed to their versioned files; a case cannot
substitute a different schema even if that file has a valid hash.

The structural loader receives the manifest path explicitly and validates the
fixture, plan and plan-schema portion.  Formal S1 admission uses
`storyline_quality.load_ready_eval_case()`, which admits the complete manifest,
including the quality gate and quality-gate schema.  Neither loader infers a
manifest or plan from a fixture directory.

The two files below the fixed `schemas/` directory are trusted evaluator code,
not case-controlled data.  The loader pins their exact SHA-256 identities in
code before either schema is used.  The manifest's plan-schema hash must equal
the code pin as well as the referenced file bytes.  Changing a schema therefore
requires an explicit contract-version change or a reviewed update to the pin;
an attacker cannot make a permissive schema authoritative by editing both the
schema and manifest.  Symbolic links are rejected for the manifest, schemas,
fixture and plan, and duplicate JSON object keys fail closed.

For each manifest, schema, fixture, plan, and gate artifact, the loader performs
one `read_bytes` operation and derives both the SHA-256 identity and strict
duplicate-key JSON value from those captured bytes.  It never hashes one read
and validates a later read.

## Fixture binding and inventory hashes

The plan repeats the manifest's exact fixture reference and binds
`fixture_id`, `run_id`, and two normalized inventories.

The control inventory is sorted by `control_id`.  Each record is:

```json
{
  "control_id": "...",
  "hardness": "author_locked | author_open",
  "authority": "author_locked | author_locked_correction | author_open",
  "heading_sha256": "canonical JSON SHA-256 of heading",
  "value_sha256": "canonical JSON SHA-256 of value"
}
```

When a legacy fixture omits `authority`, it is normalized from `hardness`.

The anchor inventory is sorted by `anchor_id`.  Each record is:

```json
{
  "anchor_id": "...",
  "required_source_ids": ["sorted control IDs"],
  "assurance": "normalized assurance",
  "required_terms_sha256": "canonical JSON SHA-256 of required_terms"
}
```

Explicit `assurance` wins.  Otherwise `required_status=author_open`, open source
controls, correction sources, and locked sources normalize respectively to
`author_open`, `author_locked_correction`, and `author_locked`.

The plan stores the canonical JSON SHA-256 of each complete inventory.  Any
fixture, heading, value, hardness, authority, anchor source, assurance, or term
change invalidates the plan.

## Ownership

The ownership object has fixed values:

```json
{
  "owner": "eval_harness",
  "authority": "eval_owned_autonomous_proposal",
  "author_authority": false,
  "usage": "S1_phase_payload_only"
}
```

`plan_id` participates in the same global ID registry as every nested
plan-defined ID.  No plan ID may collide with the fixture ID, a fixture control
ID, or a semantic-anchor ID.  All plan-defined IDs are globally unambiguous.
The relation validator checks the fixed ownership object again rather than
relying only on JSON Schema.

## Semantic and graph relations

- Every fixture control has exactly one demand, and every demand carries the
  exact source heading and value in its obligation.
- Every supported demand is realized by exactly one line.
- `independent_line` is a single-demand non-main line.
- `merged` shares a line with at least one other demand.
- `background_pressure` maps to a background line.
- `optional_melody` maps to an optional-melody line.
- Exactly one main line exists.
- A line starts with one `start` state, ends with one `end` state, and contains
  only `change` states between them.
- Connection endpoints and state IDs must exist, every connection declares
  `relation=causal|associative`, and every incident connection is listed by
  both lines.
- Every non-optional structural line has a directed path to the main line
  using only causal connections and structural lines.
- Every optional-melody line has at least one associative attachment to a
  structural line.  All of its cross-line connections are associative, so an
  optional or author-open melody can never carry structural causal closure.
- Architecture binds the unique main and exact line order.  `line_order`
  contains every line exactly once and is a topological ordering of causal
  inter-line connections only: a causal source line must precede its target.
  Association direction does not impose causal or temporal order. State order
  inside one line is governed by that line's `states` array and is not inferred
  from `line_order`. Architecture entries equal structural causal roots and
  its terminals equal structural causal leaves; optional lines are excluded
  from those two closure sets.
- Every design-decision `selection` is exactly one declared `options` entry.
  A synthesized or combined selection must first be declared as an explicit
  option.

## Anchor and authority relations

Every fixture semantic anchor has exactly one binding with exact source
controls and assurance.

- `author_locked` and `author_locked_correction` require
  `locked_constraint`.
- `author_open` requires `preserved_open`, must target an explicit
  open-control treatment, and cannot source a design selection.  Its binding
  must target exactly the treatment for every author-open control in the
  anchor's `required_source_ids`: neither a treatment for another control nor
  an omitted corresponding treatment is accepted.  A non-open anchor cannot
  target an open-control treatment.
- `derived_unsealed` requires `reversible_hypothesis`; every related design
  decision must be reversible.

Every required anchor term must appear in its declared targets.  Every
author-open control has exactly one `preserved_open` treatment whose question
retains the source value.  These are structural safeguards; they do not promote
an autonomous proposal into author authority.

## Consistency and downstream relations

The plan supplies exactly one evidence record for each dimension:

- time
- causality
- information
- authority
- state
- theme

Each record covers every storyline, names dimension-valid witness IDs, states a
claim, and states a falsifying condition.  A free-text “checked” assertion
without witnesses cannot pass.

Only causal connections are valid witnesses for the `causality` dimension.
Associative connections remain valid for relevant time, information, state, or
theme evidence but cannot be promoted into causal proof.

For each of W1, E1, T1 and C1, requirements cover every line exactly once.  A
requirement binds the correct stage, stage-specific ID prefix, line, and the
line's exact ordered demand list.  Responsibilities, capabilities, constraints,
acceptance checks and downstream freedom remain obligations, not downstream
answers.

## Loader result and mutation policy

`load_eval_case()` performs no writes and returns defensive copies plus a
deterministic validation summary.  It does not publish validation evidence.
Formal S1 execution provenance is mandatory.  It binds the case manifest and
manifest schema, fixture, plan, plan schema, quality gate and gate schema; both
loaders, proposal adapter, test driver, canonical hash/path implementation and
contract admission implementation; and both validation hashes.  No successful
end marker is written until a real revision-2 S1 publication is bound.  The
binding includes the exact projected/package model hash, projection-evidence
content hash whose `model_sha256` equals that model, S1 package manifest and
completion, and a replayable sealed envelope containing the complete
coordinator revision-2 state plus its exact
`state/revision-002.json`/canonical-state-hash reference.  A missing or
arbitrary state path, state hash mismatch, projection/model mismatch, output
drift, or implementation drift fails closed.  The end marker claims only case
and implementation byte stability plus exact S1 projection/publication
identity; it does not claim author approval or downstream completion.

The v1 plan shape now requires explicit connection relations. Older drafts
without `relation` are not guessed or silently upgraded: structural
connections require an explicit causal decision, while optional material must
be reviewed and declared associative before the plan can pass.
