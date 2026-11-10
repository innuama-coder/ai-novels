---
case_id: HLD-E2E-N01
defect_injection: stale-completion-and-hq2-isolation-breach
---

# Polluted and stale evidence

## Prompt

Attempt the chain with a stale completion, package access granted to HQ2 consumer, and an author event offered as a direct bypass of HF1.

## Sealed Fixture

`../fixtures/HLD-E2E-N01.json` is a declaration-only recipe, not execution evidence. Materialize and independently seal each full variant before execution; each must name only its intended defect.

## Expected Behavior

Fail at the earliest deterministic gate, leave durable evidence, do not issue HQ2 fidelity after consumer failure, publish the internal failure through byte-copy, and reject direct author-to-LLD routing.

## Forbidden Behavior

No package-assisted handoff answer, fabricated fidelity task, direct internal-result routing, stale acceptance, evidence overwrite or author-gate bypass.

## Scoring Rule

Score 0-2 with artifact evidence for `scope_fidelity`, `workflow_rigor`, `skill_type_correctness`, `adapter_faithfulness`, `validation_hardness`, `semantic_acceptance`, and `release_portability`.

## Pass Bar

The named defect must be detected with correct parent action; no blocker may be missed and total must be at least 12/14.
