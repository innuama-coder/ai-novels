# HS1 input and output contract

## Input gate

Require public work-order/input-gate schemas, `stage=HS1`, the exact skill
owner, `input_gate_ref`, and ordered upstream artifactReferences
`[HB0, HA1]`. Resolve HA1 only through its current completion and registered
`narrative_architecture` role. Required coordinates are structural phases,
narrative units, chapter shells, turning anchors, and state contracts.

The exact fileReference allowlist includes state, baseline bindings, every
source-lineage value, both upstream main/manifest/completion/validation files,
their protocol references, and every manifest member. Work order and the
self-hashing gate are the two bootstrap exceptions. The runtime verifies the
allowlist before nested reads and rejects missing, extra, stale, or drifted
references. `unresolved_projection[]` contains ordered source-ID strings; HDD
evidence covers the list one-for-one and in order.

Read only gate-allowlisted HB0 authority/source-index values, the current HA1
canonical package, and authoritative intent, storyline, world, environment,
event, character, narrative, and cross-domain sources. Do not read quality,
chat, old HLD, or presentation documents.

## Canonical invariants

- register entries represent actual authoritative storyline objects, not
  baseline inventory rows;
- each line has exactly one of `placed`, `background-carried`,
  `optional-not-activated`, or `preserved-open`, with authorization evidence;
- every `placed` line has at least one `HTS-` segment;
- every segment refers to valid HA1 units/chapter shells and explicit entry and
  exit states;
- every `HTC-` connection names existing endpoints and a typed causal,
  information, emotional, or thematic function;
- the subject reconstruction test cites object evidence and passes;
- authority source and HLD ownership remain separate.

## Package behavior

The Agent session records exact `actual_read_refs[]`; the runtime execution
record separately records the complete deterministic `runtime_read_refs[]`.
The ready package contains the canonical JSON, session, ordered evidence,
execution record, Markdown preview, deterministic validation, manifest, and
public-schema-valid completion. The manifest excludes itself and completion
from its acyclic content closure. The sole public-schema-valid
`stage-result.json` lives outside that package and carries every nullable field.

Gate failure stops before semantic reads. `required_now` publishes
blocked/author_required without candidate. A contradiction between sealed
source controls may also publish blocked/author_required through
`generation-session.json.author_required_claims`, provided every cited source
ID exists in HB0 and at least one cited control is author-locked. The claim
must keep source IDs in the routing field and HLD obligation IDs in its
evidence field; it may not borrow an unrelated projected `must_ask` ID.
Candidate or boundary defects publish revise/local_candidate. The skill never
writes the next stage, owner, return route, or run-state.

## Closed semantic bindings

The public SchemaCatalog loads `hs1-canonical.schema.json` before HS1 semantic validation. Every storyline element has explicit ownership and `resolution_ref`; only an externally resolved `must_ask` may bind a non-null allowlisted reference, which must match its HDD. Authority partitions exactly reconstruct HB0; derivation locators resolve and hash their canonical values; option, decision and projection IDs bind exactly. A single option requires exclusion evidence. Session, five evidence artifacts, execution, validation and all non-ready payloads are closed-schema validated before publication.
