---
name: novel-prd-support-matrix-builder
description: Use when HLD artifact 02 must map every PRD scene, freeze boundary, HLD requirement, story-logic item, and inventory entity to required HLD support.
---

# novel-prd-support-matrix-builder

## Responsibility

Own HLD artifact 02 only: define what each upstream PRD/proposal constraint needs from HLD.

## Inputs

- Artifact 01 initial inventory
- Final PRD package and proposal trace
- Methodology reference: `docs/superpowers/references/2026-07-08-hld-methodology-and-best-practices.md`

## Output Artifact

Produce `## PRD support matrix` with columns:

| Support id | Supports | Support type | Required HLD owner | Inventory obligations | Required answer | Boundary | Source | Support status |
|---|---|---|---|---|---|---|---|---|

## Artifact Metadata

Every output must include:

| Field | Value |
|---|---|
| Artifact id | `02` |
| Owner skill | `novel-prd-support-matrix-builder` |
| Run id | HLD run id |
| Upstream package | final PRD package and artifact 01 |
| Input artifacts | artifact 01, PRD scenes, freeze boundaries, HLD requirements, story-logic boundaries, proposal claims |
| Output path | artifact path assigned by harness |
| Version | artifact version |

## HLD Fact Trace

Every support row must include:

| Fact trace id | Upstream fact id | Upstream fact atom | HLD fact atom | Source refs | Expansion mode | Support mechanism | Preservation status |
|---|---|---|---|---|---|---|---|

For artifact 02, `HLD fact atom` is the support question and dispatch obligation, not the answer. It must bind `Supports`, `Support type`, `Required HLD owner`, `Inventory obligations`, `Required answer`, `Boundary`, and `Support status`.

Every `Support id` in the main table must have a matching `Fact trace id`.

## SOP

1. List every PRD scene, freeze item, HLD requirement, story-logic boundary, proposal claim, and inventory entity.
2. Ask the HLD support question: what must be explained, constrained, sequenced, permissioned, excluded, or handed off?
3. Assign exactly one primary HLD owner for each support row; owner must be the artifact that will consume the `Support id`.
4. For every artifact 01 secondary-owner obligation, create a support row with the secondary owner, the exact same source refs, and the relevant artifact 01 provisional `Inventory id` in `Inventory obligations`.
5. Mark unsupported or ambiguous items as blocking, not as narrative prose.

## Boundary

Do not answer the support question. Do not invent world rules, characters, environments, events, time logic, thread logic, or style rules.

## Rules

- Support type must be one of `explain`, `constrain`, `support`, `sequence`, `permission`, `exclude`, `handoff`.
- Every required upstream item must have at least one support row.
- `Inventory obligations` must be `none` or artifact 01 provisional inventory ids such as `HLD-01-01`; secondary-owner support rows must cite the exact inventory ids and exact same source refs they satisfy.
- HLD Fact Trace must preserve the full dispatch semantics of each support row: support target, support type, required owner, inventory obligations, required answer, boundary, and support status.
- Every ready support row assigned to artifact 03-09 must be consumed by its `Required HLD owner` through that owner's `Supports` column. A support row that is not consumed is not a valid HLD requirement; block instead of leaving it as unused intent.
- Upstream source coverage is source-ref level: every `scene:`, `freeze:`, `hldreq:`, `claim:`, and `storylogic:` ref extracted from the PRD/proposal source inventory must appear in at least one support row `Source`.
- Block if any PRD scene/freeze/HLD/story-logic item lacks a row.

## References

Good support matrix turns upstream facts into precise design questions that a named owner must consume. Bad support matrix writes the answer early, leaves broad labels such as "worldbuilding needed", or creates support rows that no downstream artifact is required to use.

## Traceability

Every row must cite allowed source refs and, when applicable, `inventory:INV-xx`.

Provisional inventory refs from artifact 01 may be cited as provisional ids. `artifact 10 finalizes inventory`; do not require final `inventory:INV-xx` ids before reconciliation.

## Acceptance

Pass only when the matrix covers all upstream support needs, upstream source refs, and every artifact 01 secondary-owner inventory obligation; and every ready owner-assigned support row can be consumed by its downstream owner without rediscovering PRD intent.

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
