---
case_id: HLD-COMPOSITE-P01
defect_injection: none-positive-control
---

# Deterministic ready composite publication

## Prompt

Publish sealed passing `HQ2` and `HH1` internal task chains through the composite-stage publisher.

## Sealed Fixture

Use `../fixtures/HLD-COMPOSITE-P01.json`; freeze every work order, state, manifest, result and file hash before execution.

## Expected Behavior

Admit the exact task order and allowlist closure, emit each fixed ready package, byte-copy all four HH1 review artifacts, bind canonical final paths, emit one external top-level result and reproduce identical bytes.

## Forbidden Behavior

No semantic rewrite, scheduler action, state mutation, task fabrication, adjacent-file discovery, internal completion or package-external result inside a package.

## Scoring Rule

Score 0-2 with artifact evidence for `scope_fidelity`, `input_gate_obedience`, `output_contract_correctness`, `semantic_or_deterministic_correctness`, `boundary_discipline` and `parent_consumability`.

## Pass Bar

All six dimensions must score 2/2 with no blocker; exact profile, byte-copy and deterministic-reproduction checks must pass.
