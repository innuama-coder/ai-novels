---
name: novel-hld-inventory-reconciler
description: Use when HLD artifact 10 must close every initial HLD inventory entity and amendment request into final inventory ids or explicit blocking dispositions.
---

# novel-hld-inventory-reconciler

## Responsibility

Own HLD artifact 10 only: reconcile every artifact 01 inventory entity and every amendment request after artifacts 03-09 into a final inventory disposition.

## Inputs

- Artifacts 01-09
- Every artifact 01 inventory row
- All amendment requests and unresolved inventory rows
- Previous approved artifact 10 when this is a rerun; use no prior artifact only for the first HLD run
- Methodology reference: `docs/superpowers/references/2026-07-08-hld-methodology-and-best-practices.md`

## Output Artifact

Produce `## Final inventory reconciliation table` with columns:

| Initial inventory id | Request id | Entity name | Entity type | Required HLD owner | Requested by artifact | Decision | Canonical subject id | Final inventory id | Reason | Source | Support status |
|---|---|---|---|---|---|---|---|---|---|---|---|

## Artifact Metadata

Every output must include:

| Field | Value |
|---|---|
| Artifact id | `10` |
| Owner skill | `novel-hld-inventory-reconciler` |
| Run id | HLD run id |
| Upstream package | final PRD package |
| Input artifacts | artifacts 01-09 |
| Output path | artifact path assigned by harness |
| Version | artifact version |
| Reconciliation mode | `bootstrap` or `continuity` |
| Previous reconciliation SHA256 | `none` for bootstrap; SHA-256 of prior approved artifact 10 for continuity |

## HLD Fact Trace

Every reconciliation decision must include:

| Fact trace id | Upstream fact id | Upstream fact atom | HLD fact atom | Source refs | Expansion mode | Support mechanism | Preservation status |
|---|---|---|---|---|---|---|---|

For artifact 10, `HLD fact atom` is the final inventory disposition, merge, rejection, or reopen decision.

Every `Initial inventory id` in the main table must have a matching `Fact trace id`.

## SOP

1. Start from artifact 01 and create one disposition row for every `Inventory id`.
2. Add one disposition row for every amendment request from artifacts 03-09, using the amendment id as `Initial inventory id`.
3. Rebuild the authoritative subject register from artifact 01 inventory rows and the amendment ids actually declared in artifacts 03-09; do not create a reconciliation subject from free text.
4. Bind every inventory row exactly to its artifact 01 entity name, entity type, required owner, source refs, and upstream fact trace. Bind an amendment row to its sole declaring artifact, source refs, and fact trace.
5. On a rerun, compare every previously resolved subject with the previous approved artifact 10; preserve its resolved final id or block the run.
6. Decide `accept`, `reject`, `merge`, `reopen_upstream`, or `blocked_unresolved`. An amendment is a rerun request, never a new entity: its accepted resolution must reopen its owner instead of minting an inventory id.
7. For `accept`, mint exactly one final inventory id. For `merge`, set `Canonical subject id` to an accepted inventory subject with the same entity identity and do not mint an id. Use `none` for `Canonical subject id` in every other decision.
8. Mark any downstream use of rejected, unresolved, or amendment subjects as blocking.

## Boundary

Do not redesign the underlying entity. Do not fix world, character, environment, event, time, thread, or POV content. Route ownership back to the relevant skill.

## Rules

- Every artifact 01 `Inventory id` must have exactly one disposition row whose entity, owner, source refs, and fact trace equal artifact 01.
- Every amendment request must have one disposition row; no undeclared amendment id may appear.
- `Request id` must be unique `HLD-10-xx` and is the stable reconciliation-row identity.
- An accepted inventory entity must have exactly one final inventory id in `inventory:INV-xx` format. `merge` reuses only its canonical accepted subject's id.
- An amendment, rejection, reopen, or blocked row must not mint a final inventory id.
- Final inventory ids must be unique across accepted rows and become the only ids artifact 11 may cite.
- Block if a rejected or unresolved amendment is used downstream.
- Only artifact 10 may mint final `inventory:INV-xx` ids.

## References

Good reconciliation makes the design universe closed by turning every provisional entity into a final id or an explicit blocker. Bad reconciliation only handles amendment rows and lets initial inventory entities leak into integration without final ids.

## Traceability

Every decision cites source refs, the initial/provisional inventory id, the requesting artifact, and the matching artifact 01 or amendment-origin fact trace. `Canonical subject id` is an explicit merge edge, never prose in `Reason`.

Provisional inventory refs from artifacts 01-09 are resolved here; only artifact 10 may mint final `inventory:INV-xx` ids.

## Acceptance

Pass only when every artifact 01 entity and every amendment request is resolved from the reconstructed subject register or explicitly blocks integration, final inventory ids are one-to-one and stable against the prior approved reconciliation when present, and artifact 11 can cite only accepted or canonicalized ids.

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
