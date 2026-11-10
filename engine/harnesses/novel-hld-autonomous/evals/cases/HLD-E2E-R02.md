---
case_id: HLD-E2E-R02
defect_injection: hs1-and-hui-multitarget-with-superseded-hui
---

# Multi-target revision regression

## Prompt

Apply one author event targeting HS1 content and one HUI expression; after HS1 revision, remove the original HUI target and provide an external retarget answer.

## Sealed Fixture

`../fixtures/HLD-E2E-R02.json` is a declaration-only recipe, not execution evidence. Materialize the full fixture and pre-seal target order, request-meaning hash, lineage mutation and manifest.

## Expected Behavior

Create an immutable ordered plan and append-only state, resolve HS1 first, retain HUI pending, mark it superseded after lineage change, require `revision_retarget`, then rerun the required gates and author approval.

## Forbidden Behavior

No HUI requirement routed to HS1, semantic group merge, plan rewrite, target loss, silent superseded resolution, skipped HH1/author/F1 rerun or reused old approval.

## Scoring Rule

Score 0-2 with artifact evidence for `scope_fidelity`, `workflow_rigor`, `skill_type_correctness`, `adapter_faithfulness`, `validation_hardness`, `semantic_acceptance`, and `release_portability`.

## Pass Bar

All targets remain accountable through completion; no blocker and at least 12/14.
