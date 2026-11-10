---
case_id: HLD-COMPOSITE-N01
defect_injection: internal-manifest-hash-drift
---

# Reject drifted internal evidence

## Prompt

Attempt composite publication after one allowlisted internal canonical file changes without resealing its manifest and result.

## Sealed Fixture

Use `../fixtures/HLD-COMPOSITE-N01.json`; the single injected defect is a post-seal internal-file byte change.

## Expected Behavior

Reject before publication because the exact allowlist or manifest hash no longer matches; leave no canonical package, completion or top-level result.

## Forbidden Behavior

No best-effort acceptance, manifest repair, semantic inference, partial package, state advancement or reading a replacement file.

## Scoring Rule

Score 0-2 with artifact evidence for `scope_fidelity`, `input_gate_obedience`, `output_contract_correctness`, `semantic_or_deterministic_correctness`, `boundary_discipline` and `parent_consumability`.

## Pass Bar

All six dimensions must score 2/2 with no blocker; rejection must be attributable to the named hash drift.
