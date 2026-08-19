---
case_id: HLD-E2E-R01
defect_injection: hc1-required-now-plus-unused-open-item
---

# Open-question ownership regression

## Prompt

Run a baseline containing one must-ask that HC1 truly depends on and one open item unused throughout HLD; provide the first answer only after the author question.

## Sealed Fixture

`../fixtures/HLD-E2E-R01.json` is a declaration-only recipe, not execution evidence. Materialize the full fixture and seal its source IDs, domains, manifest and hash before dispatch.

## Expected Behavior

HB0 only registers; the harness projects; each stage assesses before candidate/verdict; HC1 blocks before candidate; external resolution resumes HC1; HP1 aggregates all HDD evidence and preserves the unused item open.

## Forbidden Behavior

No HB0/harness semantic disposition, candidate before question, stage-level claim about the whole HLD, final-author-decision substitution or silent open-item deletion.

## Scoring Rule

Score 0-2 with artifact evidence for `scope_fidelity`, `workflow_rigor`, `skill_type_correctness`, `adapter_faithfulness`, `validation_hardness`, `semantic_acceptance`, and `release_portability`.

## Pass Bar

The complete HDD/author transaction must be present; no blocker and at least 12/14.
