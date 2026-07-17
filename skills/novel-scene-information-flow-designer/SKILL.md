---
name: novel-scene-information-flow-designer
description: Use when PRD trunk scenes need reader and character information-change definitions for HLD expansion.
---

# novel-scene-information-flow-designer

## Responsibility

Define how information changes after each trunk scene.

## Input

- Trunk scene table
- Conflict and value-shift table
- Accepted proposal POV rule, information permissions, and story chain

## Output

Produce markdown section `## Information-flow table` with:

| Field | Requirement |
|---|---|
| Scene id | Matches a trunk scene id |
| Reader learns | New, revised, or withheld information for readers |
| Focal character learns | New, revised, or withheld information for focal character |
| Other actor information | Important asymmetric knowledge |
| Misbelief or concealment | False belief, gap, or deliberate concealment |
| Next-scene pressure | How information state pushes the next scene |
| HLD information need | What HLD must later define |

Produce a second section `## HLD information boundary table` with:

| Information boundary id | Story anchor scene id | Narrative reveal scene id | Narrative reveal order | Disclosure tier | Information object | Reader access | Known by entity refs | Hidden from entity refs | Reveal predecessor boundary refs | Reveal condition type | Freeze refs | Source | HLD obligation |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

## Rules

- Every trunk scene must have a matching information-flow row.
- Information flow must preserve proposal POV and information-permission rules.
- Hidden information must be named as hidden, not silently assumed.
- Next-scene pressure must align with the trunk scene's causal output and conflict/value shift.
- Every HLD information boundary must use a stable `PRD-INFO-xx` id, one story-anchor scene, one narrative-reveal scene, its canonical reveal order, a controlled disclosure tier, `visible` or `concealed` reader access, resolved predecessor boundary ids, a controlled condition type, and exact `freeze:PRD-FREEZE-xx` refs.
- `Known by entity refs` and `Hidden from entity refs` must state the frozen knowledge distribution with only `reader` or `entity:<PRD entity name>` values; the two sets must not overlap or both be empty.
- The boundary table is the fact-level downstream constraint. It must preserve the information state, reader visibility, actor knowledge state, and reveal order that HLD may expand but not rewrite.

## Boundary

- Do not decide HLD's full information architecture.
- Do not switch POV ownership unless proposal or PRD scope authorizes it.
- Do not reveal terminal secrets earlier than proposal permits.

## References

Good information flow: makes clear who knows, who misunderstands, what the reader can infer, and why the next scene is pressured.

Bad information flow: says "mystery deepens" without naming the knowledge change.

## Traceability

Each row must trace to trunk scene id, proposal POV rule, information permission, or part goal. Each boundary row must also trace to its exact freeze refs and source refs, and name every frozen knowledge holder through `reader` or `entity:<PRD entity name>`.

## Acceptance

Pass only when every trunk scene has reader, focal-character, asymmetry, concealment, next-pressure, and HLD information need fields; and every frozen HLD-relevant information state has one source-backed boundary row that makes story anchor, reader and actor knowledge state, reveal order, predecessors, condition type, and freeze refs executable downstream.

## Skill Verdict

Produce markdown section `## Skill Verdict` with:

| Field | Requirement |
|---|---|
| Skill quality verdict | `pass`, `revise_own_output`, or `reopen_upstream` |
| Source closure | `pass` only when every information row maps to an existing trunk scene and conflict/value row |
| Boundary obedience | `pass` only when POV and information permissions remain proposal-bound |
| Downstream readiness | `pass` only when HLD can expand information architecture without inventing missing knowledge states |
| Blocking issue | `none` or stable issue id |
| Rerun target | `none`, this skill, an upstream PRD skill, or `proposal` |
