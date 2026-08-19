# HP1 input/output contract

## Purpose and authority

HP1 owns package construction, indexing, trace projection and deterministic validation only. HB0 owns source controls; HA1–HK1 own HLD semantics; HQ1 owns semantic acceptance. HP1 cannot repair any of them.

## Input

The only CLI input is an absolute or repository-relative `work-order.json` path. It must validate against the common work-order schema and bind:

- stage `HP1`, exact skill/version/implementation hash, supported mode and immutable run identity;
- matching sealed input gate and state-before references;
- exact ordered upstream chain `[HB0,HA1,HS1,HC1,HI1,HR1,HK1,HQ1]`;
- one unique allowlisted role for every main artifact, manifest, validation and completion, plus `hb0_source_index`;
- empty `unresolved_projection`; HP1 has no source access;
- fixed output directory and package-external result location.

Every reference is a normalized workspace-contained path plus SHA-256. Current ready upstreams must have exact public profiles, closed manifests, main/validation manifest bindings and completion bindings. HQ1 requires `verdict=pass` and `findings=[]`.

## Ready package

Exactly these top-level files:

1. `novel-hld-package.json`
2. `canonical-models/{narrative-architecture,storyline-choreography,character-arc-placement,narrative-information-architecture,rhythm-continuity-architecture,key-scene-function-map}.json`
3. `canonical-models/hld-semantic-review.json`
4. `novel-hld-spec.md`
5. `hld-cross-index.json`
6. `hld-traceability-matrix.json`
7. `hld-traceability-matrix.md`
8. `lld-handoff.json`
9. `assembly-execution.json`
10. `validation.json`
11. `package-manifest.json`
12. `stage-completion.json`

The workspace also receives exactly one package-external `stage-result.json`.

Canonical models are byte-for-byte copies. `novel-hld-package.json` contains hash-bound model/decision references, HB0 source controls, exact authority partition, preserved open values and mechanical HDD aggregation. The cross-index resolves every stable HLD ID and every HB0 source-control ID.

## LWR to LWK rule

HK1 must provide complete `lld_work_requirements` whose IDs are `LWR-*`. HP1 produces exactly one `LWK-*` per LWR using the identical suffix, records `source_lwr_id`, copies every required field without conversion, and stores `source_value_sha256`. Missing, duplicate, colliding or input `LWK-*` IDs block delivery.

## Blocked package

Exactly `gate-data.json`, `blocked-report.json`, `validation.json`, `result-manifest.json`, plus package-external blocked `stage-result.json`. No ready artifact or completion may coexist.

## Acceptance

Ready requires schema validity, exact package profile, manifest closure excluding the acyclic completion file, completion-to-manifest/validation/artifact binding, byte reproduction, eight-current-upstream admission, source and decision trace resolution, stable-ID uniqueness, authority equality, HQ1 pass/empty findings and LWR↔LWK bijection.

Character and environment coverage is defined by typed entity collections in the sealed HB0 source index, not by a whole semantic domain. Production conception inputs use exactly the object entries at `P1/canonical-models/character-system.json#/profiles/{index}` and `P1/canonical-models/environment-system.json#/environments/{index}`. A generic non-conception fixture is accepted only when the source-index entry is the single typed object at `/value` with the exact `characters-definition` or `environments-definition` discriminator. Relationship records, character demands, development freedoms, functional zones and other domain controls remain trace obligations; they must never be reclassified as character or environment entities. Every canonical character requires an HC1 disposition, and every non-context character plus every canonical environment must be placed in at least one LWK.
