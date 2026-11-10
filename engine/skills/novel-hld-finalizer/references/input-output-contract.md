# Input and output contract

## Exact inputs

Stage `HF1`, owner `novel-hld-finalizer`, upstream order `[HB0,HA1,HS1,HC1,HI1,HR1,HK1,HD1,HQ1,HP1,HQ2,HH1]`. The allowlist has exactly these semantic/operational roles:

- `run_state`, `author_decision`
- `hp1_package`, `hp1_manifest`, `lld_handoff`, `hld_cross_index`
- `hq2_acceptance`, `hh1_manifest`, `hh1_html`, `render_target_registry`
- `validation_HB0` through `validation_HH1`

Completion, manifest and primary canonical references are carried only by `work_order.upstream_completions`; no fictitious `completion_*` or `manifest_*` allowlist roles are added. Validation references require eleven explicit roles because `artifactReference` does not carry validation. All references contain path and SHA-256. References with different operational roles compare through their exact `path/sha256` projection. `run_state.accepted_completions` and the work-order upstream array are value- and order-equal. Every content manifest has exact closure over package content while excluding `package-manifest.json` and `stage-completion.json`; the public completion then binds that finished manifest, validation and canonical artifacts without a hash cycle. Accepted completions may come from earlier revisions and may retain sealed return bindings; currency is established by the current state’s exact accepted chain, not by forcing historical revision or return fields to match HF1. HQ2 and HH1 top-level completions use the composite publisher public identity. Run state is `waiting_author_decision`, `current_stage=null`, and has no revision plan/state or active return.

The external `author-decision.json` has `decision`, event sequence, non-empty author text, external/current/unconsumed flags, and exact bindings for HP1 package, HQ2 acceptance, HH1 manifest, and HTML. Its event is later than the waiting state and earlier than the issued (or reissued) HF1 work order. Approved/rejected require no targets; revise requires at least one target. New revise decisions use schema version `1.1` so every change is explicitly classified as presentation-only, HLD-semantic, or conception-authority.

## Revision targets

Each target contains `target_kind`, `target_id`, `requested_change`, `author_text_locator`, `change_scope`, and `target_field_paths`. An `hld_semantic` change additionally contains `semantic_target_ids`; every ID resolves in `hld-cross-index.json`, all IDs in one target have one canonical owner, and the router resumes that owner. `report_content` is presentation-only: it may change ordering, wording, grouping, or visual expression but may not introduce or alter a city, character, environment, event, relationship, causal rule, terminal state, or other story fact. `render_expression` uses HUI and resolves in the registry. `conception_authority` uses an existing source/control ID and causes harness-level conception reentry. HF1 validates only; it does not choose, merge, or reclassify targets. A semantic request aimed only at HRE/HVG is invalid rather than being silently treated as a report edit.

## Approved output

Exact package: `hld-completion.json`, `final-validation.json`, `finalizer-execution.json`, `package-manifest.json`. External `stage-result.json` is top-level ready and references the completion. Completion binds the complete chain, author event, HP1, HQ2 acceptance, HH1 manifest, HTML, current handoff, and final validation; it declares `next_stage=novel-lld` but contains no post-state.

## Revise output

Exact package: byte-copied `author-decision.json`, `revision-report.json`, `finalizer-execution.json`, `validation.json`, `result-manifest.json`. `revision-report.revision_targets` is a value-identical projection. External result is `revise/external_author_request` with author event and revision report refs. No completion, return, plan, or state.

## Rejected output

Exact package: `gate-data.json`, `blocked-report.json`, `validation.json`, `result-manifest.json`. External result is `blocked/author_rejected`. No completion or state.

Any stale/missing input, bad binding, unresolved target, consumed event, HQ2 non-pass, active return, or unresolved plan fails closed and cannot produce approved output.
