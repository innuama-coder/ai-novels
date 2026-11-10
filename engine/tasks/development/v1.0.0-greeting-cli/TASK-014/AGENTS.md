# TASK-014 AGENTS.md

## Required reading

- `engine/docs/ai-novel-workflow/conception-autonomous-workflow-v2.md` §12–§15
- TASK-014 `task.md`
- autonomous-v2 public schemas
- coordinator、return router 和 H1-C formal validator

## Ownership

Production owner may edit runtime modules, public contracts and task documentation. Independent test owner alone edits `tests/test_final_completion.py`.

## Rules

- Treat the author event as external sealed authority; do not generate or normalize it.
- Compute revise ownership and invalidation; never accept caller-provided owner.
- Keep H1 completion outside H1-C.
- Publish through staging, validation, TOCTOU check, atomic replace, post-validation and coordinator, in that order.
- Preserve a valid orphan if coordinator rejects after publication.
- Do not report acceptance; root owns acceptance.

## Verification

Run the focused TASK-014 suite and the contract/coordinator regressions. Record exact counts and failures.
