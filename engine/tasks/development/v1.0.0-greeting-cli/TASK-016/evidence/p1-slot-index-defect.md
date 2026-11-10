# TASK-016 production defect handoff: P1 cannot index canonical character slots

Status: blocked by production contract/runtime mismatch  
Owner: P1 implementation owner (`novel-conception-deliverable-assembler`;
TASK-010 lineage)  
Reporter scope: TASK-016 E2E only; no runtime or schema change made

## Real-chain reproduction

Command:

```powershell
uv run --with jsonschema python -m unittest testing.test_conception_autonomous_v2_e2e.GenericRealChainProbe.test_real_public_entries_reach_p1 -v
```

The isolated, declarative generic run passed the real B0, S1, W1, E1, T1,
C1 and Q1 runners. Q1 also passed its public destination validator after the
full P1–P5 dual-identity state machine.

Last sealed evidence:

- Q1 input gate:
  `67d5245de5a6dd9549541e709b0ac8bc7b09f2a7a2df6facce1af65ded6a8b0a`
- Q1 completion:
  `be6722bd2c114dba2c110015d7494d77cc332ed203605ff265d910327dfc4884`
- C1 in the failing run passed its owner runner and supplied a canonical
  `slot_resolution` for the required `SLOT-001`.

The first P1 error was:

```text
P1_CROSS_REFERENCE_UNRESOLVED:
S1:/storylines/0/actor_slot_ids/0 -> SLOT-001
```

No P1 candidate package or coordinator transition was accepted.

## Contract contradiction

1. `storyline-architecture.schema.json` requires every storyline to contain
   at least one `actor_slot_ids` value matching `SLOT-*` (lines 44 and 49).
2. `character-system.schema.json` defines resolution of those slots through
   `slot_resolution[].slot_id` (lines 12 and 47–53).
3. A slot-resolution object has `additionalProperties: false`; adding an
   `id` alias is invalid.
4. P1 `_cross_model_index` creates definitions only for mappings containing
   a string-valued `id` (around `run_v2.py:372–391`).
5. P1 treats `actor_slot_ids`, `participant_slot_ids`,
   `counter_slot_ids`, and `visibility_ids` as references, but never admits
   `slot_resolution[].slot_id` into the definition map.

Therefore a schema-valid C1 slot declaration cannot satisfy P1's otherwise
legitimate slot references.

## Why TASK-016 cannot repair this in its owned adapter

- Adding `id` to `slot_resolution` violates the C1 schema.
- Renaming `slot_id` to `id` violates the C1 schema and C1 runtime.
- Removing S1/T1 slot references violates their schemas and owner validators.
- Adding a separate fake object such as a design decision with
  `id: SLOT-001` would make P1 resolve the reference to the wrong semantic
  kind. That is evidence fabrication, not an E2E fix.
- Rewriting or patching P1 validation is outside TASK-016 ownership.

There is no legitimate fixture/proposal-only repair path.

## Expected versus actual

Expected: P1 indexes each canonical C1 `slot_resolution[].slot_id` as a
formal `SLOT-*` definition, allowing exact S1/T1/C1 cross-reference closure.

Actual: P1 ignores the formal slot key and rejects the first valid S1 slot
reference as unresolved.

## Suggested minimal production fix

In `_cross_model_index`, add a narrowly scoped alternate-definition rule:

- stage must be `C1`;
- JSON pointer must identify an item under `/slot_resolution`;
- `slot_id` must be a valid string;
- record that `slot_id` as a definition whose occurrence points to the
  slot-resolution object and whose value hash covers that whole object.

Do not treat arbitrary `*_id` fields as definitions and do not weaken
unresolved-reference rejection.

## Required regression matrix

1. Valid S1 `actor_slot_ids` resolves to the exact C1 slot resolution.
2. Valid T1 participant, initiator, counter and visibility slot references
   resolve to the same slot definition.
3. An unknown `SLOT-*` remains `P1_CROSS_REFERENCE_UNRESOLVED`.
4. Duplicate canonical slot definitions fail closed.
5. A non-C1 or non-`slot_resolution` `slot_id` is not admitted as a
   definition.
6. Cross-model index and P1 manifest hashes remain deterministic across two
   fresh isolated runs.
7. Existing non-slot ID definitions and unresolved-reference tests remain
   unchanged.

