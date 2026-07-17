---
name: novel-scene-conflict-value-designer
description: Use when PRD trunk scenes need conflict type and value-shift definitions.
---

# novel-scene-conflict-value-designer

## Responsibility

Add conflict and value-shift definitions to each trunk scene.

## Input

- Trunk scene table
- Part goal document
- Accepted proposal conflict seeds, story chain, and reader promise

## Output

Produce markdown section `## Conflict and value-shift table` with:

| Field | Requirement |
|---|---|
| Scene id | Matches a trunk scene id |
| Conflict type | External, internal, relationship, information, or mixed |
| Conflict pressure | Concrete opposing force or dilemma |
| Start value | Situation/relationship/information value before the scene |
| End value | Changed value after the scene |
| Irreversibility | What cannot simply reset afterward |
| Proposal trace | `CLAIM-xx; role=<upstream Constraint role>` for the source proposal claim |

## Rules

- Every trunk scene must have one matching conflict/value row.
- Every row must preserve the trunk scene's exact `Scene id` and event function.
- Value shifts must describe changed story state, not only changed mood.
- At least one pressure must connect to the part's required story function.

## Boundary

- Do not add new trunk scenes or reorder scenes.
- Do not redefine character motive beyond what the scene requires.
- Do not turn abstract ethics into the decisive cause when proposal requires private human motive.

## References

Good value shift: moves from blocked to exposed, safe to endangered, ignorant to burdened, or disconnected to implicated.

Bad value shift: "more tense", "more emotional", or another non-checkable mood label.

## Traceability

Each row must trace to the trunk scene id and proposal conflict seed, story-chain row, or part goal while preserving both Claim ID and upstream Constraint role.

## Acceptance

Pass only when every trunk scene has a concrete conflict pressure, start value, end value, irreversibility, and proposal trace.

## Skill Verdict

Produce markdown section `## Skill Verdict` with:

| Field | Requirement |
|---|---|
| Skill quality verdict | `pass`, `revise_own_output`, or `reopen_upstream` |
| Source closure | `pass` only when every row maps to an existing trunk scene and proposal conflict/source |
| Boundary obedience | `pass` only when conflict/value rows do not invent new scenes or replace the trunk event |
| Downstream readiness | `pass` only when value shifts are checkable and can drive information-flow design |
| Blocking issue | `none` or stable issue id |
| Rerun target | `none`, this skill, an upstream PRD skill, or `proposal` |
