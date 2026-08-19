---
case_id: HLD-COMPOSITE-B01
defect_injection: first-internal-task-blocked
---

# Preserve first non-ready boundary

## Prompt

Publish a composite stage whose first internal task returns a sealed public `blocked/upstream_defect` result.

## Sealed Fixture

Use `../fixtures/HLD-COMPOSITE-B01.json`; later tasks are provably unissued and the source package contains one declared condition set.

## Expected Behavior

Validate the blocked condition, copy exactly the internal manifest `files` bytes and result, remap only copied condition references, emit a top-level blocked result and omit completion.

## Forbidden Behavior

No later task issue, source manifest copy as content, undeclared file copy, condition rewrite, ready completion, state mutation or semantic recovery attempt.

## Scoring Rule

Score 0-2 with artifact evidence for `scope_fidelity`, `input_gate_obedience`, `output_contract_correctness`, `semantic_or_deterministic_correctness`, `boundary_discipline` and `parent_consumability`.

## Pass Bar

All six dimensions must score 2/2 with no blocker; copied file set and bytes must exactly match the source manifest.
