# HA1 input and output contract

## Input gate

Accept only a public `work-order.schema.json` instance with `stage=HA1`,
`exact_owner_skill=novel-hld-narrative-architect`, `input_gate_ref`, ordered
HB0 `artifactReference`, and a public-schema-valid `input-gate.json`. Forward mode
must have null return and revision-plan bindings. Return mode must bind the
active HA1 target group; the harness, not this skill, owns that check.

`file_allowlist[]` is the exact ordered set of role/path/hash file references,
not a list of paths. It closes over state-before, HB0 main/manifest/completion/
validation, every file in the HB0 manifest, source index, and authorized source
values. The invocation work order and the self-hashing input gate are the only
bootstrap reads outside that closure. Missing, extra, stale, or gate-drifted
references fail before the omitted file is read.

Read only HB0 control/source-index artifacts and allowlisted authoritative
values in the intent, storylines, world, environments, events, characters,
narrative, and cross-domain source domains. Never read quality-domain sources,
chat, prior HLD, or human-review prose.

## Draft contract

The agent supplies exactly:

- `canonical.json`;
- `generation-session.json`, whose `actual_read_refs[]` are exact allowlist
  references and include every source-lineage value plus the HB0 main artifact;
- five generation-evidence files in the order frozen by the SOP.

`decision_dependencies[]` must byte-for-value equal the HDD assessments.
Every canonical element separates `source_authority_refs[]` from
`ownership_class`. `hld_owned` may derive only from `freedom`; unresolved
`must_ask` may not become a design decision.

## Ready package

The content package profile is exactly:

```text
narrative-architecture.json
generation-session.json
generation-evidence/*.json
execution-record.json
narrative-architecture.md
validation.json
package-manifest.json
stage-completion.json
```

The manifest content closure excludes the manifest itself and
`stage-completion.json`, avoiding a hash cycle. Completion uses the public
schema and binds the work order, manifest, validation, upstream artifact and
canonical artifact. `stage-result.json` is the sole package-external,
top-level result envelope; every nullable public field is present.
It copies the work order's event sequence and result timestamp and contains no
route or run-state mutation.

## Non-ready behavior

- gate identity or stale input: fail before semantic reads; no output is
  trusted;
- `required_now`: publish blocked/author_required with gate data and no
  candidate or completion;
- malformed or boundary-leaking candidate: publish revise/local_candidate with
  candidate, evidence, revision report, validation, result manifest, and the
  external result envelope;
- runtime failure is not a semantic verdict.

The harness is the only consumer allowed to advance or return the run.

## Closed semantic bindings

`canonical.json` is validated by the local `ha1-canonical.schema.json` merged into the public SchemaCatalog before any HA1 semantic callback. Every canonical element has `resolution_ref`: mandatory, freedom and open projections use null; only an externally resolved `must_ask` may use a non-null allowlisted reference, and that reference must equal its HDD resolution. Authority partitions exactly reconstruct HB0. Each derivation claim points to its canonical value with an RFC 6901 locator and matching canonical SHA-256. Candidate IDs, decision bindings and projection IDs must agree; one candidate is legal only with non-empty unique-solution exclusion evidence. Session, all five evidence files, execution, validation and every non-ready artifact also use closed schemas.
