---
name: novel-prd-freeze-boundary-writer
description: Use when a PRD needs explicit frozen items and downstream no-change boundaries.
---

# novel-prd-freeze-boundary-writer

## Responsibility

Write the PRD freeze boundary list for HLD and downstream stages.

## Input

- Accepted proposal frozen items
- Specified part scope and goal
- Trunk scene table
- Story logic boundary table, when artifact 03 contains one
- Conflict/value and information-flow tables

## Output

Produce markdown section `## Freeze boundary list` with:

| Field | Requirement |
|---|---|
| Freeze id | Stable id such as `PRD-FREEZE-01` |
| Frozen item | Scene order, event fact, role function, information state, or boundary |
| Source | Structured source refs, such as `scene:PRD-S01` or `claim:CLAIM-01` |
| Downstream no-change rule | What HLD/LLD/writing cannot alter |
| Reopen condition | What kind of issue requires upstream reopen |

## Rules

- Freeze only items needed to preserve proposal and PRD trunk causality.
- Distinguish frozen facts from HLD expansion needs.
- Every frozen item must have a source.
- If artifact 03 contains `Story logic boundary table`, freeze each PRD-level causal answer needed to prevent HLD from rewriting usable-intelligence split, protected-person causality, or terminal-deception capability.
- Source may cite only canonical PRD scene facts as `scene:PRD-Sxx` or upstream proposal claims as `claim:CLAIM-xx`.
- Free text source labels, raw `PRD-Sxx`, and raw `CLAIM-xx` are not valid source closure.
- Freeze types should stay limited to scope, scene order, event fact, role function, environment function, information state, and terminal constraint.

## Boundary

- Do not add proposal-unauthorized core concepts.
- Do not freeze HLD/LLD details that PRD has not designed.
- Do not make all wording immutable; freeze story facts and boundaries.

## References

Good boundary: concrete enough for checking and narrow enough to allow HLD expansion.

Bad boundary: either vague ("keep tone") or overfrozen ("all details cannot change").

## Traceability

Every freeze row must trace through structured `Source` refs to proposal claims or canonical PRD trunk scene facts.

## Acceptance

Pass only when downstream can tell which scene order, event facts, role functions, and information states cannot be changed.

## Skill Verdict

Produce markdown section `## Skill Verdict` with:

| Field | Requirement |
|---|---|
| Skill quality verdict | `pass`, `revise_own_output`, or `reopen_upstream` |
| Source closure | `pass` only when every frozen item source resolves to canonical PRD scene facts or proposal claims |
| Boundary obedience | `pass` only when the freeze list does not freeze HLD/LLD details that PRD has not designed |
| Downstream readiness | `pass` only when HLD/LLD/writing/checking can tell exactly what cannot change |
| Blocking issue | `none` or stable issue id |
| Rerun target | `none`, this skill, an upstream PRD skill, or `proposal` |
