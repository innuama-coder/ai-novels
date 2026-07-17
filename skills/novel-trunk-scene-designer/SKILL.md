---
name: novel-trunk-scene-designer
description: Use when a PRD needs a linear list of indispensable trunk scenes for the selected part.
---

# novel-trunk-scene-designer

## Responsibility

Design the specified part's linear trunk scene list.

## Input

- Accepted proposal
- Specified part scope table
- Part goal document
- Proposal frozen items and open/watch items

## Output

Produce markdown section `## Trunk scene table` with:

| Field | Requirement |
|---|---|
| Scene id | Stable id such as `PRD-S01` |
| Order | Linear order within the specified part |
| Entry state | Story state before the scene |
| Roles | Characters or groups present/affected and their relationship state |
| Environment | Place or environment type and narrative function |
| Event | Core action or change |
| Causal output | What this scene makes possible or unavoidable |
| Proposal trace | `CLAIM-xx; role=<upstream Constraint role>` for the source proposal claim |
| Scene content | Concrete scene-level content: who is present, what happens on screen/page, what pressure is visible, and what changes inside the scene |
| Previous dependency | What prior scope/goal/story state makes this scene necessary |
| Next pressure | What pressure this scene creates for the next trunk scene |
| Indispensability proof | Why removing this scene would break the specified part |

Also produce markdown section `## Scene execution table` with at least two execution units for every trunk scene:

| Field | Requirement |
|---|---|
| Unit id | Stable id such as `PRD-S01-U01` |
| Parent scene id | The trunk scene id this unit belongs to |
| Unit order | Linear order inside the parent scene |
| Scene objective | What the unit must accomplish on the page |
| On-page action | Concrete visible action, exchange, discovery, or decision |
| Conflict turn | What pressure changes inside this unit |
| Exit state | What exact state the next unit or scene inherits |
| Proposal trace | `CLAIM-xx; role=<upstream Constraint role>` for the governing proposal fact |

When the selected part contains a causal split between usable intelligence and complete cause, a protected-person motive, or a digital-life terminal deception, also produce markdown section `## Story logic boundary table`:

| Field | Requirement |
|---|---|
| Boundary id | Stable id such as `PRD-LOGIC-01` |
| Logic concern | The specific story-logic risk being closed |
| Frozen answer | The PRD-level causal answer that downstream stages cannot rewrite |
| HLD expansion room | What HLD may still design within the frozen answer |
| Required HLD entity refs | Every character or group HLD must inventory to preserve this boundary, as `entity:<名称>` |
| Source | Structured source refs such as `scene:PRD-S01` or `claim:CLAIM-01` |

The table must include minimum plausibility anchors when those story risks exist:

| Anchor | Requirement |
|---|---|
| Major-event action window | State what usable intelligence gives action teams, including a concrete action/handling window rather than only "important information" |
| Protected-person relationship weight | State why the protected person matters enough, such as private relationship, debt, family tie, promise, or life-saving bond |
| Digital-life terminal execution condition | State the bounded execution mechanism, such as existing alerts/logs/system prompts plus terminal flow or multi-confirmation constraints |
| Organization pressure limit | State why the organization still pressures the case after crisis resolution but cannot directly copy, seize, or take over the terminal choice |

## Rules

- Every trunk scene must be indispensable to the selected part's causal progression.
- Scene order must be readable without hidden skipped causes.
- If the selected part reaches post-death memory reading, include a prior causal setup scene that shows how critical intelligence failed normal handoff, transmission, or reporting because of the accident/death context.
- Each scene must include roles, environment, event, and causal output.
- Each scene must include concrete scene content, not only a plot label or proposal-level claim.
- Every trunk scene must be decomposed into at least two execution units so downstream writing can follow visible actions, conflict turns, and exit states instead of expanding a summary.
- If scenes depend on withholding a complete cause while using partial intelligence, protecting a person tied to the event, or a digital life deceiving someone into termination, freeze those causal answers in `Story logic boundary table`.
- Story logic boundary rows must contain plausibility anchors for action window, protected-person relationship weight, terminal execution conditions, and organization pressure limits where relevant.
- Every story logic boundary must name its required HLD character/group refs. Omission is not a handoff to HLD: it is a PRD gap.
- Each scene must prove previous dependency, next pressure, and indispensability.
- Keep the table at trunk-scene level, not chapter draft level.

## Boundary

- Do not write dialogue, prose, full chapter outline, full world system, or LLD scene blueprint.
- Do not change proposal's focal POV rule, terminal agency, or frozen story facts.
- Do not solve HLD-only background mechanics unless required to state the scene event.

## References

Good trunk scene: one causal node that changes the situation and pushes the next node.

Bad trunk scene: a mood beat, exposition note, or scene that can be removed without changing the part.

## Traceability

Every trunk scene must trace to part goal and proposal story chain or frozen item while preserving both Claim ID and upstream Constraint role.

## Acceptance

Pass only when scenes are linear, indispensable, proposal-bound, include any required pre-extraction causal setup, each has role, environment, event, entry state, scene content, and causal output, every trunk scene has at least two execution units, and any usable-intelligence/complete-cause, protected-person, or terminal-deception risk has a Story logic boundary table with minimum plausibility anchors.

## Skill Verdict

Produce markdown section `## Skill Verdict` with:

| Field | Requirement |
|---|---|
| Skill quality verdict | `pass`, `revise_own_output`, or `reopen_upstream` |
| Source closure | `pass` only when every scene traces to scope, goal, and proposal |
| Boundary obedience | `pass` only when no scene rewrites proposal, scope, POV, or terminal agency |
| Downstream readiness | `pass` only when HLD can expand roles, environment, event, and causality without inventing the trunk |
| Blocking issue | `none` or stable issue id |
| Rerun target | `none`, this skill, an upstream PRD skill, or `proposal` |
