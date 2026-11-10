# HK1 Input and Output Contract

## Input gate

Accept only a harness-signed work order for `stage=HK1`, exact owner `novel-hld-key-scene-function-planner`, and `mode=forward|return_resolution`. Ordered upstream is exactly `[HB0,HA1,HS1,HC1,HI1,HR1]`.

Required content is HB0 control/source index and all current HA1–HR1 canonical models, validations, manifests, and completions. Required semantic fields include structures/chapter shells/turning points, story-line segments/connections, character choices/costs/results, POV/knowledge/suspense/reveal states, time/space/pacing/tension/continuity, plus authorized baseline objects already in the source index. Read only the allowlist and never read `quality` sources.

Validate owner, stage, run, revision, state, ordered completion chain, hashes, return binding, and revision-plan binding before story interpretation. Generate the complete HK1 HDD set before any candidate.

## Canonical output

`package/key-scene-function-map.json` is the sole content authority and contains common governance fields plus:

- `key_scene_functions[]`
- `structural_coverage_matrix[]`
- `storyline_coverage_matrix[]`
- `arc_coverage_matrix[]`
- `information_coverage_matrix[]`
- `climax_and_payoff_coverage`
- `lld_work_requirements[]`
- `lld_freedoms[]`

Each `HKF-` records chapter/unit location; preconditions and trigger; one primary function; compatible secondary functions; source obligation IDs; storyline/event/character/environment refs; POV constraint; knowledge before/after; required state change; choice/cost/result; tension and pacing role; completion criteria; forbidden solutions; and bounded LLD freedom.

Each `LWR-*` records one or more HKF IDs, a merge/split rationale, entry/exit state, required elaboration, LLD freedoms, prohibitions, and acceptance criteria. Every HKF belongs to at least one LWR and every LWR consumes at least one HKF. HK1 owns this grouping. HP1 must project each current LWR one-to-one into its separately owned `LWK-*`; HK1 must never emit an `LWK-*` ID.

Canonical elements preserve source authority and use one legal ownership class. `decision_dependencies[]` exactly matches the projected HK1 HDD set.

## Package/result split

Ready package exact files are canonical JSON; generation session; five ordered generation-evidence files; execution record; non-authoritative Markdown; validation; package manifest; stage completion. The only `stage-result.json` is outside `package/`, has `result_scope=top_level`, copies work-order sequence/timestamp, and references completion without routing fields.

`required_now` creates the standard blocked package and external blocked result before candidate generation. Local HK1 correction uses local-candidate revise. Upstream contradictions use blocked/upstream-defect evidence with affected IDs; HK1 cannot alter upstream content or nominate a final owner.

## Ready semantic conditions

- Every structural turn, mandatory line connection, core character choice, mandatory reveal/payoff, and climax/result obligation has HKF coverage.
- Each HKF has a unique primary function, necessity evidence, legal preconditions, and a meaningful exit-state change.
- Merge/split decisions respect time, place, POV, knowledge, state, tension, and causal compatibility.
- No critical conflict is solved by unsupported coincidence, one sentence, unauthorized power/information, or a disposable tool character.
- No HKF is filler and no LWR is an arbitrary size bucket.
- LWR required elaboration and acceptance let LLD start without deciding missing HLD structure, while preserving genuine scene-detail freedom.
- No action, dialogue, imagery, sensory, prop, memory-text, or prose leakage appears.
