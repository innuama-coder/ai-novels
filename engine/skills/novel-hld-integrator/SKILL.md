---
name: novel-hld-integrator
description: Use when HLD artifact 11 must assemble accepted HLD business artifacts into a final HLD package with fact-level Source Map and LLD handoff index.
---

# novel-hld-integrator

## Responsibility

Own HLD artifact 11 only: integrate accepted artifacts 03-10 into a final HLD Source Map and LLD handoff package without adding business facts.

## Inputs

- Artifacts 01-10 and their Skill Verdicts
- Final inventory ids and canonical merge resolutions from artifact 10
- Methodology reference: `engine/docs/superpowers/references/2026-07-08-hld-methodology-and-best-practices.md`

## Output Artifact

Produce `## HLD Source Map` with columns:

| HLD fact id | Upstream fact id | Fact type | Upstream fact atom | HLD fact atom | Source refs | Owner artifact | Final inventory id | Expansion mode | Support mechanism | LLD handoff target | Preservation status |
|---|---|---|---|---|---|---|---|---|---|---|---|

Produce `## LLD handoff index` with columns:

| LLD handoff target | HLD fact id | Owner artifact | Final inventory id | Upstream fact id | Upstream fact atom | HLD fact atom | Source refs | Handoff status |
|---|---|---|---|---|---|---|---|---|

## Artifact Metadata

Every output must include:

| Field | Value |
|---|---|
| Artifact id | `11` |
| Owner skill | `novel-hld-integrator` |
| Run id | HLD run id |
| Upstream package | final PRD package |
| Input artifacts | artifacts 01-10 |
| Output path | artifact path assigned by harness |
| Version | artifact version |

## HLD Fact Trace

`## HLD Source Map` is artifact 11's canonical fact-level trace. The required `## HLD Fact Trace` mirrors its trace fields and uses `HLD fact id` as `Fact trace id`; owner, final inventory, and LLD routing authority remain in the Source Map and handoff index.

| Fact trace id | Upstream fact id | Upstream fact atom | HLD fact atom | Source refs | Expansion mode | Support mechanism | Preservation status |
|---|---|---|---|---|---|---|---|

The Source Map is fact-level, not citation-level. `Upstream fact id` is the stable upstream fact identity. The same `Source refs` may support multiple distinct `Upstream fact id` values. The same `Upstream fact id` must never carry conflicting `Upstream fact atom` values, even if additional source refs are added.

Every `HLD fact id` in `## HLD Source Map` must have a matching `Fact trace id` with identical upstream id/atom, HLD atom, source refs, expansion mode, support mechanism, and preservation status.

## SOP

1. Confirm artifacts 01-10 exist and pass their Skill Verdict gates.
2. Convert every accepted artifact 03-09 design fact trace into one atomic HLD Source Map row; no accepted design trace may be omitted or represented twice.
3. Map each accepted design fact without rewriting its upstream atom. Artifact 04-07 rows carry the reconciled final inventory id; artifact 03, 08, and 09 rows use `none` because they have no inventory-bound subject. Preserve the owner, complete HLD fact atom, source refs, and LLD handoff target.
4. Mirror each Source Map row into `## HLD Fact Trace` and reject any field drift.
5. Produce exactly one `ready` LLD handoff index row per Source Map row, copying its handoff target, HLD fact id, owner, final inventory id, upstream id/atom, HLD atom, and source refs.
6. Reject unsupported, rewritten, ownerless, unreconciled, omitted, duplicated, or unready facts.

## Boundary

Do not depend on artifact 12. Do not add, delete, merge, or rewrite HLD business facts. Do not repair missing sources during assembly.

## Rules

- Expansion mode must be `explain`, `constrain`, `support`, `sequence`, `permission`, `exclude`, or `handoff`.
- `Upstream fact id` must use `UPF-...` format and must bind one stable `Upstream fact atom`; adding source refs must not change the bound atom.
- Every accepted artifact 03-09 `HLD Fact Trace` row must have exactly one Source Map row with identical upstream fact id/atom, HLD fact atom, source refs, owner artifact, and LLD handoff target. Omission, duplication, or rewrite blocks integration.
- Final inventory id must be `inventory:INV-xx` for inventory-bound artifact 04-07 facts and `none` for artifact 03, 08, and 09 facts; do not place `scene:`, `claim:`, `hldreq:`, `freeze:`, or `storylogic:` refs in the final inventory column.
- Every final inventory id must resolve through artifact 10 `## Final inventory reconciliation table` to one accepted inventory subject with the same owner artifact, source refs, upstream fact id, and upstream fact atom; reject ids minted by an amendment, rejected row, blocked row, unresolved merge, or a different accepted subject.
- Every Source Map row must have exactly one LLD handoff index row with `Handoff status = ready` and identical handoff target, HLD fact id, owner, final inventory id, upstream id/atom, HLD atom, and source refs. `HLD fact id` is the index's unique key: a second row for the same fact, even with another handoff target, blocks integration. No orphaned handoff-index row is allowed.
- Preservation status must be one of `preserved`, `bounded_expansion`, `blocked`, `checked`, or `risk_reported`. Unsupported, contradictory, replacement, or reinterpretation findings must be rejected or routed as blocking issues; do not emit them as preservation statuses.
- Block if integrator adds unsupported HLD facts.

## References

Good integration is a traceable assembly. Bad integration is a polished HLD that hides missing source closure.

## Traceability

Every HLD fact atom must preserve source refs, owner artifact, final inventory id where applicable, and LLD handoff target. Source Map coverage is complete only when all accepted artifact 03-09 fact traces and all handoff-index rows close one-to-one.

## Acceptance

Pass only when every accepted artifact 03-09 design fact is source-backed and owner-backed, every fact trace has exactly one Source Map mapping, every Source Map row has exactly one ready handoff-index mapping, and the package is ready for independent integrity checking.

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
