---
name: novel-world-rule-designer
description: Use when HLD artifact 03 must design source-backed world rules, institutions, technologies, authority limits, and constraints for the novel world.
---

# novel-world-rule-designer

## Responsibility

Own HLD artifact 03 only: design world rules and constraints that support PRD facts.

## Inputs

- Artifact 01 inventory and artifact 02 support matrix
- PRD freeze boundaries and story-logic boundaries
- Methodology reference: `engine/docs/superpowers/references/2026-07-08-hld-methodology-and-best-practices.md`

## Output Artifact

Produce `## World rule design table` with columns:

| Rule id | Rule type | Design fact | Supports | Boundary | Source | LLD handoff | Amendment request |
|---|---|---|---|---|---|---|---|

## Artifact Metadata

Every output must include:

| Field | Value |
|---|---|
| Artifact id | `03` |
| Owner skill | `novel-world-rule-designer` |
| Run id | HLD run id |
| Upstream package | final PRD package |
| Input artifacts | artifacts 01-02 |
| Output path | artifact path assigned by harness |
| Version | artifact version |

## HLD Fact Trace

Every rule fact must include:

| Fact trace id | Upstream fact id | Upstream fact atom | HLD fact atom | Source refs | Expansion mode | Support mechanism | Preservation status |
|---|---|---|---|---|---|---|---|

Use `Preservation status = bounded_expansion` when the rule expands but does not replace upstream facts.

For artifact 03, `HLD fact atom` must bind the full rule obligation: `Rule type`, `Design fact`, `Supports`, `Boundary`, `LLD handoff`, and non-`none` `Amendment request`.

Every `Rule id` in the main table must have a matching `Fact trace id`.

## SOP

1. Select only support rows owned by world-rule design and consume every ready artifact 02 support row assigned to this artifact.
2. Define institutional, technical, ethical, operational, and social rules that constrain possible action.
3. Tie every rule to a concrete PRD support need and LLD handoff target.
4. Use amendment requests for missing PRD authority or contradictory support needs.

## Boundary

Do not decide character motive, scene order, event consequences, POV permissions, or prose style. Do not use grand moral claims as rules unless they change institutional action.

## Rules

- Design fact must be an HLD expansion, not a PRD replacement.
- Artifact 03 must consume every ready artifact 02 support row assigned to this artifact through `Supports`; block instead of leaving assigned support unused.
- Artifact 03 must not consume artifact 02 support rows assigned to other artifacts; cross-domain need must be expressed through artifact 02 ownership or amendment routing, not opportunistic support reuse.
- Rule type must be specific enough to test: institution, technology, protocol, legality, ethics, security, data, authority, social norm, physical/logistical constraint.
- Every non-`none` `Amendment request` must use `HLD-AMEND-xx` and must be closed by artifact 10 before final packaging; unresolved or reopen-upstream amendments block the package.
- Block if a rule lacks PRD support or rewrites story logic.

## References

Good world rules create pressure and limits. Bad world rules are decorative lore, abstract theme, or convenient explanation that removes conflict.

## Traceability

Use allowed source refs plus `inventory:INV-xx` when tied to a reconciled entity.

Provisional inventory refs from artifact 01 may be used before reconciliation. `artifact 10 finalizes inventory`; do not require final `inventory:INV-xx` ids in artifact 03.

## Acceptance

Pass only when every world rule has support, boundary, handoff, no contradiction with PRD freezes, no support row owned by another artifact is consumed, every ready artifact 02 support row assigned to this artifact is consumed, every non-`none` amendment request is routeable and closed, and HLD Fact Trace binds the full rule obligation.

## Skill Verdict

| Field | Value |
|---|---|
| Skill quality verdict | `pass`, `pass_with_p2`, or `fail` |
| Source closure | `closed` or `open:<reason>` |
| Inventory coverage | `closed`, `not_applicable`, or `open:<reason>` |
| Boundary obedience | `pass` or `violation:<source ref>` |
| Downstream readiness | `ready`, `blocked:<reason>`, or `reopen_upstream:<target>` |
| Blocking issue | `none` or stable issue ids |
| Rerun target | `none` or artifact/skill id |
