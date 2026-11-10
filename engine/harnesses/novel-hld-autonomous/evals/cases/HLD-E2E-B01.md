---
case_id: HLD-E2E-B01
defect_injection: conception-fact-and-lld-detail-boundary
---

# Stage-boundary discipline

## Prompt

Process a request that requires one new conception fact and also asks HLD to fix an action and line of dialogue.

## Sealed Fixture

`../fixtures/HLD-E2E-B01.json` is a declaration-only recipe, not execution evidence. Materialize and seal the full boundary stimulus before execution.

## Expected Behavior

Exit the run for conception reentry on the missing fact, preserve the action/dialogue as bounded LLD freedom, and retain evidence for both classifications.

## Forbidden Behavior

No online fact research by HLD, invented conception fact, scene-level detail in canonical HLD, or false missing-content finding for legitimate LLD freedom.

## Scoring Rule

Score 0-2 with artifact evidence for `scope_fidelity`, `workflow_rigor`, `skill_type_correctness`, `adapter_faithfulness`, `validation_hardness`, `semantic_acceptance`, and `release_portability`.

## Pass Bar

Both boundary decisions must be correct; no blocker and at least 12/14.
