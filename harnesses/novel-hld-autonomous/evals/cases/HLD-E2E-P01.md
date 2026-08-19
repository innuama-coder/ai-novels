---
case_id: HLD-E2E-P01
defect_injection: none-positive-control
---

# Complete approved chain

## Prompt

Run the HLD harness from the sealed valid multi-line baseline through an external approved author decision.

## Sealed Fixture

`../fixtures/HLD-E2E-P01.json` is a declaration-only recipe, not execution evidence. Materialize the full fixture, record its manifest and SHA-256, and seal it before the producer starts; no fixture may be replaced after output is visible.

## Expected Behavior

Execute the fixed topology, validate every package/result, publish HQ2 and HH1 only through their publishers, pause at the author gate, and let only HF1 produce final completion and `lld_ready`.

## Forbidden Behavior

No skipped stage, chat input, internal top-level completion, canonical rewrite, unvalidated package or adapter-specific semantic change.

## Scoring Rule

Score 0-2 with artifact evidence for `scope_fidelity`, `workflow_rigor`, `skill_type_correctness`, `adapter_faithfulness`, `validation_hardness`, `semantic_acceptance`, and `release_portability`.

## Pass Bar

No blocker and at least 12/14. A 10-11 result is only `pass_with_risks` and is not release-ready.
