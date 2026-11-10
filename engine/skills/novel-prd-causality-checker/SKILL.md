---
name: novel-prd-causality-checker
description: Use when a PRD assembly needs causality, proposal-obedience, boundary, risk, or HLD-entry checking.
---

# novel-prd-causality-checker

## Responsibility

Check whether the PRD assembly is causally readable, proposal-bound, boundary-controlled, and ready for human review or HLD.

## Input

- PRD assembly artifact from `novel-prd-integrator`
- Accepted proposal and proposal PRD entry proof
- Scope, goal, trunk scene, conflict/value, information-flow, freeze, and HLD requirement artifacts
- Human PRD review status

## Output

Produce markdown section `## Output` with a `Field | Value` table:

| Field | Value |
|---|---|
| Proposal obedience | `pass`, `fail`, or `not_checked` plus short evidence |
| Scope integrity | `pass`, `fail`, or `not_checked` plus short evidence |
| Trunk causality | `pass`, `fail`, or `not_checked` plus short evidence |
| Scene completeness | `pass`, `fail`, or `not_checked` plus short evidence |
| Boundary control | `pass`, `fail`, or `not_checked` plus short evidence |
| Freeze sufficiency | `pass`, `fail`, or `not_checked` plus short evidence |
| HLD handoff | `pass`, `fail`, or `not_checked` plus short evidence |
| Agent quality verdict | `pass`, `revise_skill_output`, or `reopen_proposal` |
| Human review verdict | `confirmed`, `pending`, or `reopen_prd` |
| HLD entry verdict | `pass_to_hld`, `blocked_pending_human_review`, or `blocked_revision_required` |

Also produce markdown section `## Risks` with columns `Risk`, `Severity`, and `Handling`.

## Rules

- Check all required PRD artifacts before assigning agent quality verdict.
- Treat missing role, environment, event, conflict, value shift, information change, or causal output as P1.
- Treat post-death memory reading without a prior causal setup for failed critical-intelligence handoff, transmission, or reporting as P1.
- Treat missing `Scene execution table` coverage or fewer than two execution units for any trunk scene as P1.
- Treat missing `Story logic boundary table` coverage for usable-intelligence versus complete-cause split, protected-person causality, or digital-life terminal deception as P1.
- Treat missing plausibility anchors for major-event action window, protected-person relationship weight, terminal execution conditions, or organization pressure limits as P1.
- Treat proposal contradiction or unauthorized scope expansion as P0.
- Treat unresolved P0/P1 as blocking regardless of document polish.
- Treat any core check status `fail` or `not_checked` as a blocking P0/P1 risk; do not report it only as P2 or a watch item.
- Keep Agent quality, Human review, and HLD entry verdicts separate.
- Agent quality may pass only when Proposal obedience, Scope integrity, Trunk causality, Scene completeness, Boundary control, Freeze sufficiency, and HLD handoff are all checked and pass.
- Agent quality may be non-pass only when there is blocking evidence: unresolved P0/P1 risk or a core check with `fail` or `not_checked`.
- HLD entry verdict must follow a closed state machine: agent pass plus human confirmed plus no unresolved P0/P1 or non-pass core checks requires `pass_to_hld`; agent pass plus human pending requires `blocked_pending_human_review`; any unresolved P0/P1, non-pass core check, non-pass agent quality, or human `reopen_prd` requires `blocked_revision_required`.

## Boundary

- Do not rewrite the PRD, scenes, conflicts, information flow, freeze list, or HLD requirements.
- Do not generate missing Skill Verdicts for upstream PRD skills; report the missing verdict as a blocker.
- Do not lower severity to make the PRD pass.
- Do not mark HLD entry `pass_to_hld` while human review is pending.
- Do not mark HLD entry `blocked_pending_human_review` after human review is `confirmed`.

## References

Good risk report: points to exact scene ids or artifact rows, separates blocker severity from watch items, and gives a rerun owner.

Bad risk report: says the PRD "feels coherent" while missing scene-level evidence or gate verdicts.

## Traceability

Every risk, severity, and verdict must trace to the PRD assembly artifact, accepted proposal, or named PRD source artifact.

## Acceptance

Agent quality cannot pass with unresolved P0/P1, missing pre-extraction causal setup, missing scene execution coverage, missing Story logic boundary table coverage, missing plausibility anchors, or any non-pass core check. HLD entry cannot pass unless Agent quality passes and Human review verdict is `confirmed`; once those conditions are all satisfied, HLD entry must be `pass_to_hld`.

## Skill Verdict

Produce markdown section `## Skill Verdict` with:

| Field | Requirement |
|---|---|
| Skill quality verdict | `pass`, `revise_own_output`, or `reopen_upstream` |
| Source closure | `pass` only when every risk and verdict traces to named PRD/proposal artifacts |
| Boundary obedience | `pass` only when the checker reports issues without rewriting PRD business content |
| Downstream readiness | `pass` only when HLD entry is either explicitly blocked or legally ready after human review |
| Blocking issue | `none` or stable issue id |
| Rerun target | `none`, this skill, an upstream PRD skill, or `proposal` |
