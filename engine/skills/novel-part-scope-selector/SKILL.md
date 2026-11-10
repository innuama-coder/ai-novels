---
name: novel-part-scope-selector
description: Use when a proposal-approved PRD candidate must be selected as the specified part for PRD work.
---

# novel-part-scope-selector

## Responsibility

Select one proposal-authorized specified part for PRD design.

## Input

- Accepted proposal document
- Proposal Risk Report with `PRD entry verdict = pass_to_prd`
- Proposal PRD candidate list or human-approved PRD scope
- Proposal frozen items and open/watch items

## Output

Produce markdown section `## Specified part scope table` with:

| Field | Requirement |
|---|---|
| Scope id | Stable id for this PRD scope |
| Scope name | Human-readable name |
| Start boundary | First story condition covered by this PRD |
| End boundary | Last story condition covered by this PRD |
| Excluded material | Adjacent story material not covered |
| Independence proof | Why the part can be designed and reviewed alone |
| Proposal trace | `CLAIM-xx; role=<upstream Constraint role>` authorizing the scope |
| Verdict | `pass`, `revise_scope`, or `reopen_proposal` |

## Rules

- Choose only a scope authorized by the accepted proposal or by explicit human scope selection.
- Define start and end as story-state boundaries, not vague chapter labels.
- Keep the scope small enough for human review and HLD handoff.

## Boundary

- Do not design scenes, conflicts, world rules, character dossiers, or prose.
- Do not widen the scope to solve unrelated proposal open items.
- Do not treat old PRD/HLD/LLD/writing material as scope authority.

## References

Good scope: clear start, clear end, explicit exclusions, and an independence proof.

Bad scope: an attractive title with no boundary, or a range that requires redesigning the whole novel.

## Traceability

Every scope row must trace to the accepted proposal, proposal PRD handoff, or explicit human scope selection by preserving both Claim ID and upstream Constraint role.

## Acceptance

Pass only when the scope has start, end, exclusions, independence proof, proposal trace, and no contradiction with frozen proposal items.

## Skill Verdict

Produce markdown section `## Skill Verdict` with:

| Field | Requirement |
|---|---|
| Skill quality verdict | `pass`, `revise_own_output`, or `reopen_upstream` |
| Source closure | `pass` only when the scope is authorized by proposal or explicit human scope selection |
| Boundary obedience | `pass` only when the scope does not widen, shrink, or rewrite proposal constraints |
| Downstream readiness | `pass` only when goal and trunk-scene skills can use the scope without guessing start/end boundaries |
| Blocking issue | `none` or stable issue id |
| Rerun target | `none`, this skill, an upstream PRD skill, or `proposal` |
