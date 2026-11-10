---
name: novel-part-goal-definer
description: Use when a selected PRD scope needs its story function, required outcome, and acceptance boundary defined.
---

# novel-part-goal-definer

## Responsibility

Define what the specified part must accomplish in the larger novel.

## Input

- Specified part scope table
- Accepted proposal
- Proposal frozen items, story chain, POV rule, and PRD handoff

## Output

Produce markdown section `## Part goal table` with:

| Field | Requirement |
|---|---|
| Required story state at start | What must be true before the first trunk scene |
| Required story state at end | What must be true after the last trunk scene |
| Story function | What this part must prove, change, or unlock |
| Required pressure | External, internal, relationship, or information pressure inherited from proposal |
| Success criteria | What a human reviewer can check |
| Proposal trace | `CLAIM-xx; role=<upstream Constraint role>` for the source claim |
| Verdict | `pass`, `revise_goal`, or `reopen_scope` |

## Rules

- Goals must be concrete enough to judge the trunk scene list.
- Goals must preserve proposal-level reader promise, focal POV rule, and terminal direction.
- Goals may answer proposal watch items only within this part's boundary.

## Boundary

- Do not create a new novel premise, ending, major relationship, or world system.
- Do not define all scenes or HLD details.
- Do not use abstract theme statements as a substitute for story-state changes.

## References

Good goal: states what must change between start and end, why it matters, and how to verify it.

Bad goal: only says the part should be tense, emotional, or atmospheric.

## Traceability

Each goal and success criterion must cite proposal story chain, frozen item, PRD handoff, or approved scope row while preserving both Claim ID and upstream Constraint role.

## Acceptance

Pass only when start state, end state, story function, inherited pressure, and success criteria are checkable and proposal-bound.

## Skill Verdict

Produce markdown section `## Skill Verdict` with:

| Field | Requirement |
|---|---|
| Skill quality verdict | `pass`, `revise_own_output`, or `reopen_upstream` |
| Source closure | `pass` only when the goal traces to the approved scope and proposal story function |
| Boundary obedience | `pass` only when the goal does not create a new premise, ending, major relationship, or world system |
| Downstream readiness | `pass` only when trunk-scene design can verify start state, end state, pressure, and success criteria |
| Blocking issue | `none` or stable issue id |
| Rerun target | `none`, this skill, an upstream PRD skill, or `proposal` |
