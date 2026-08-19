# HI1 Input and Output Contract

## Input gate

Accept only a harness-signed `work-order.json` and sealed `input-gate.json` for `stage=HI1`, `exact_owner_skill=novel-hld-information-architect`, and `mode=forward|return_resolution`.

The exact ordered upstream is `[HB0,HA1,HS1,HC1]`. Required content is the HB0 control/source index; HA1 narrative architecture; HS1 storyline choreography; HC1 character arc placement; authorized narrative controls; current manifests, validations, completions, state-before, and active return binding when applicable. Read only the allowlist. `source_artifacts[]` in the canonical output must equal the actual semantic-read subset.

Before candidates, assess every `unresolved_projection[]` item. Non-quality source access is limited to `intent, storylines, world, environments, events, characters, narrative, cross-domain` objects registered by HB0 and assigned to HLD. HI1 may not read `quality` sources.

Block before story interpretation if owner, stage, run, revision, state, completion order, hash, allowlist, return binding, or revision-plan binding is invalid or stale.

## Ready canonical

The sole content authority is `package/narrative-information-architecture.json`. It must contain the common governance fields and:

- `pov_policy`
- `unit_pov_assignments[]`
- `knowledge_states[]`
- `reader_information_states[]`
- `suspense_chains[]`
- `information_nodes[]`
- `reveal_payoff_matrix[]`
- `concealment_and_inference_rules[]`

Every information node records a stable `HIN-` ID, source, knower, reader state, acquisition mode, earliest legal unit, forbidden leak units, source authority refs, ownership class, and resolution ref. Every suspense chain records an `HSP-` ID and explicit setup, probe, reveal, payoff, or authorized-open terminal. POV/knowledge objects use the registered `HPV-` and `HKS-` prefixes.

Every canonical element preserves `source_authority_refs[]`, uses exactly one `ownership_class=source_projection|hld_owned|preserved_open|lld_freedom`, and satisfies the frozen mapping. `decision_dependencies[]` is exactly the HI1 HDD set.

## Ready package

The content package file set is exactly:

```text
package/narrative-information-architecture.json
package/generation-session.json
package/generation-evidence/00-dependency-assessment.json
package/generation-evidence/01-obligation-analysis.json
package/generation-evidence/02-option-analysis.json
package/generation-evidence/03-projection-analysis.json
package/generation-evidence/04-adversarial-self-review.json
package/execution-record.json
package/narrative-information-architecture.md
package/validation.json
package/package-manifest.json
package/stage-completion.json
stage-result.json
```

`stage-result.json` is outside `package/`, uses `result_scope=top_level`, copies work-order `event_sequence` and `result_timestamp`, and for ready has `completion_ref` but no internal-manifest or routing fields. The parent consumes the result envelope, then revalidates manifest, validation, and completion.

## Non-ready package

If a projected dependency is `required_now`, produce only `gate-data.json`, `blocked-report.json`, `validation.json`, and `result-manifest.json` in the content package, plus the external `stage-result.json` with `result=blocked`, `blocker_class=author_required`, and affected IDs. Do not produce a canonical candidate or completion.

Local semantic correction uses the harness-defined local-candidate revise profile. Runtime failure uses `runtime_error` and never becomes a semantic verdict. HI1 records evidence and affected IDs; it never names the final return owner or writes run-state.

## Ready semantic conditions

- Every knowledge change has a valid source and legal acquisition path.
- Every POV assignment obeys perception, epistemic, moral, and narrative-contract limits.
- Every mandatory reveal has an earlier setup; every mandatory setup has payoff.
- Misbelief and inference are derivable from available evidence rather than forced stupidity.
- Reader knowledge is explicitly distinguished from each character's knowledge.
- Open endings and identity questions remain open unless bound to an external author resolution.
- No LLD prose or scene action appears.
