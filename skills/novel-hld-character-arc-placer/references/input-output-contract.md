# HC1 input and output contract

## Input gate

Require public work-order/input-gate schemas, `stage=HC1`, the exact skill
owner, `input_gate_ref`, and ordered upstream artifactReferences
`[HB0, HA1, HS1]`. Consume HA1 coordinates and HS1 storyline segments, unit
matrix, typed connections, and event placement only through current completion
roles. All person, relationship, motivation, ability, permission, knowledge,
event, and outcome facts must resolve to HB0-indexed authority.

The exact fileReference allowlist closes over state, baseline bindings,
source-lineage values, all upstream main/manifest/completion/validation and
protocol files, and every file declared by each upstream manifest. The work
order and self-hashing gate are the only bootstrap exceptions. Missing, extra,
stale, or gate-drifted references fail before unauthorized nested reads.
`unresolved_projection[]` is an ordered source-ID string list and HDD evidence
must cover it exactly in that order.

Read only gate-allowlisted sources and current upstream packages. Do not read
quality sources, chat, report prose, old HLD, or downstream artifacts.

## Canonical invariants

- every core character in the participation register has an arc state model;
- the path contains start, pressure, choice, cost, and result functions;
- each arc step binds an existing narrative unit, storyline segment, event,
  pressure, choice, cost, and consequence;
- relationship steps bind exactly two existing characters and record both
  pre- and post-states;
- event alignment names the responsible participant for every key result;
- capability, information, and permission checks use existing facts and reject
  unsupported action;
- no element introduces biography, appearance, relation, feeling, ability, or
  information not present in authority;
- authority source classification and HLD ownership are never merged.

## Package behavior

The Agent session uses exact `actual_read_refs[]`; execution records the full
runtime read closure separately. The ready content package contains
`character-arc-placement.json`, session,
ordered evidence, execution, preview, deterministic validation, manifest, and
public completion. The manifest excludes itself and completion to avoid a hash
cycle. The single public stage-result envelope is package-external and contains
all required nullable fields.

`required_now` creates blocked/author_required before candidate publication.
A malformed, unsupported, or boundary-leaking candidate creates
revise/local_candidate. The skill submits affected evidence but never writes
the final owner, route, next state, or repair plan.

## Closed semantic bindings

`hc1-canonical.schema.json` is merged into the public SchemaCatalog before HC1 semantic checks. Every role, arc, relationship and feasibility element declares ownership and `resolution_ref`; a non-null value is legal only for an externally resolved `must_ask` and must exactly match its HDD allowlisted input. HB0 authority reconstruction, RFC 6901 derivation hashes, option-to-decision-to-projection bindings, and unique-solution exclusion evidence are hard checks. Session, five evidence artifacts, execution, validation and every non-ready artifact are closed-schema validated before packaging.
