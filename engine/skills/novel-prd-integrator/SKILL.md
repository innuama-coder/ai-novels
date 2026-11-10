---
name: novel-prd-integrator
description: Use when independent PRD skill outputs need to be assembled into one PRD document.
---

# novel-prd-integrator

## Responsibility

Assemble PRD skill outputs into one PRD document without adding, deleting, reordering, or rewriting trunk scene facts.

## Input

- Proposal source and PRD entry proof
- Specified part scope
- Part goal
- Trunk scene table
- Conflict/value table
- Information-flow table
- HLD information boundary table
- PRD freeze boundary list
- HLD expansion requirement list
- Story logic requirement coverage
- Upstream required HLD entities
- Source paths, versions, and verdicts for all PRD artifacts

## Output

PRD assembly artifact with:

| Section | Source |
|---|---|
| Proposal source and entry proof | harness input gate |
| Specified part scope | `novel-part-scope-selector` |
| Part goal and success criteria | `novel-part-goal-definer` |
| Linear trunk scene table | `novel-trunk-scene-designer` |
| Conflict and value shifts | `novel-scene-conflict-value-designer` |
| Information flow | `novel-scene-information-flow-designer` |
| HLD information boundary table | `novel-scene-information-flow-designer` |
| Freeze boundaries | `novel-prd-freeze-boundary-writer` |
| HLD expansion requirements and story-logic coverage | `novel-hld-expansion-requirement-writer` |
| Upstream required HLD entities | `novel-hld-expansion-requirement-writer` |
| PRD Integration Verdict | Integrator source-completeness, traceability, and no-new-business-content verdict |
| Scene Source Map | Each trunk scene id mapped to `Scene id`, `Order`, `Event fact`, `Causal output`, `Proposal trace`, and `Source artifact`; `Proposal trace` must preserve `CLAIM-xx; role=<upstream Constraint role>` exactly |

`PRD Integration Verdict` must use a `Field | Value` table with `Source completeness`, `Scene fact preservation`, `No new business content`, and `Package readiness`.

## Rules

- Copy the complete `## HLD information boundary table` from artifact 05 unchanged into artifact 08 and the final PRD package. All three copies must be text-identical; absence or drift blocks integration.
- Preserve trunk scene ids, order, event facts, causal outputs, conflict/value rows, information-flow rows, and HLD information boundary rows exactly; do not merge, reorder, or reinterpret boundary ids, freeze refs, reader or actor knowledge state, tiers, or predecessor links.
- Report contradictions or missing source artifacts instead of smoothing them over.
- Keep proposal entry proof and PRD freeze boundaries visible.
- Preserve artifact 07 `Upstream required HLD entities` exactly; do not add entity rows during integration.
- Provide Scene Source Map coverage for every trunk scene using exact headers `Scene id`, `Order`, `Event fact`, `Causal output`, `Proposal trace`, and `Source artifact`; preserve the trunk scene's exact Claim ID and role marker.

## Boundary

- Do not create new trunk scenes, merge scenes, delete scenes, or reorder scenes.
- Do not add HLD world system, LLD details, dialogue, prose, or chapter text.
- Do not use old PRD/HLD/LLD/writing artifacts as source unless explicitly marked non-frozen reference.

## References

Good PRD integration: reads as a concise main-scene contract while preserving every source trace and gate verdict.

Bad PRD integration: polished document that hides missing scene source, changes order, or turns HLD requirements into world design.

## Traceability

Every PRD section must name its source skill. Every trunk scene must appear in Scene Source Map by id, order, event fact, causal output, proposal trace, and source artifact. The Scene Source Map must preserve the trunk scene designer's exact `Scene id`, `Order`, `Event`, `Causal output`, and `Proposal trace`, including the `role=<upstream Constraint role>` marker; normalized prose cannot rewrite these facts. `Upstream required HLD entities` must remain sourced to artifact 07 and preserve its `Upstream fact id`, `Source fact field`, `Upstream fact atom`, entity, entity type, and source refs. The final package must reproduce artifact 07's complete `HLD expansion requirement list`, `Story logic requirement coverage`, and entity table exactly. The final package index must list `HLD information boundary table | artifact 05`.

## Acceptance

Pass only when all required source artifacts are present, every trunk scene is trace-covered, the artifact 05 boundary table is preserved exactly in artifact 08 and the final package, all artifact 07 handoff tables are preserved exactly in the final package, no source contradiction is hidden, and no new business content appears during assembly.

## Skill Verdict

Produce markdown section `## Skill Verdict` with:

| Field | Requirement |
|---|---|
| Skill quality verdict | `pass`, `revise_own_output`, or `reopen_upstream` |
| Source closure | `pass` only when every PRD section names the exact source artifact and every scene is covered by Scene Source Map |
| Boundary obedience | `pass` only when integration adds no new business content and preserves canonical scene facts |
| Downstream readiness | `pass` only when the causality checker can evaluate a complete, source-backed PRD assembly |
| Blocking issue | `none` or stable issue id |
| Rerun target | `none`, this skill, an upstream PRD skill, or `proposal` |
