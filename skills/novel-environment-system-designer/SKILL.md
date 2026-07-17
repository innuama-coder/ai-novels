---
name: novel-environment-system-designer
description: Use when HLD artifact 05 must design environments, spaces, spatial relations, and state changes that support PRD scenes and later LLD work.
---

# novel-environment-system-designer

## Responsibility

Own HLD artifact 05 only: design HLD-level environments and spatial systems.

## Inputs

- Artifacts 01-03
- PRD scene locations, environmental support rows, freeze boundaries
- Methodology reference: `docs/superpowers/references/2026-07-08-hld-methodology-and-best-practices.md`

## Output Artifact

Produce `## Environment system table` with columns:

| Environment id | Inventory id | Entity type | Entity name | Environment type | Function | Spatial relation | State change id | State change dimension | State before | State after | State change | Supports | Source | LLD handoff | Amendment request |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

## Artifact Metadata

Every output must include:

| Field | Value |
|---|---|
| Artifact id | `05` |
| Owner skill | `novel-environment-system-designer` |
| Run id | HLD run id |
| Upstream package | final PRD package |
| Input artifacts | artifacts 01-03 |
| Output path | artifact path assigned by harness |
| Version | artifact version |

## HLD Fact Trace

Every environment fact must include:

| Fact trace id | Upstream fact id | Upstream fact atom | HLD fact atom | Source refs | Expansion mode | Support mechanism | Preservation status |
|---|---|---|---|---|---|---|---|

Environment facts must preserve PRD scene-location facts while adding bounded function, relation, and state-change support.

Every `Environment id` in the main table must have a matching `Fact trace id`; the trace row `Source refs` must exactly match the main row `Source`.

`HLD fact atom` must bind the full environment obligation from the main row: `Inventory id`, `Entity type`, `Entity name`, `Environment type`, `Function`, `Spatial relation`, `State change id`, `State change dimension`, `State before`, `State after`, `State change`, `Supports`, `LLD handoff`, and every non-`none` `Amendment request`.

## SOP

1. Select every artifact 01 `environment` inventory row assigned to artifact 05.
2. For each selected inventory row, create exactly one artifact 05 main-table row whose `Inventory id`, `Entity type`, `Entity name`, and `Source` exactly match artifact 01.
3. Preserve the artifact 01 `Upstream fact id` in the matching artifact 05 `HLD Fact Trace` row and include the inventory id, entity type, and entity name in that row's `HLD fact atom`.
4. Consume every ready artifact 02 support row assigned to this artifact through `Supports`.
5. Define what the place makes possible, impossible, visible, hidden, urgent, delayed, or dangerous.
6. Define spatial relation among accident/death context, life-support site, lab, organization spaces, digital enclosure, and relevant private spaces.
7. Assign one unique `State change id`, one `State change dimension` (`access`, `evidence`, `pressure`, `safety`, `visibility`, or `containment`), and distinct uppercase `State before`/`State after` tokens to each environment row. Define the state change and hand the exact transition forward for artifact 06.

## Boundary

Do not write scene prose, atmosphere paragraphs, technical event chains, or character decisions. Do not create decorative locations without PRD support.

## Rules

- Every environment must have causal function, not only mood.
- Artifact 05 must consume every ready artifact 02 support row assigned to this artifact through `Supports`; block instead of leaving assigned support unused.
- Every artifact 01 `environment` inventory row assigned to artifact 05 must be represented in artifact 05 by exact `Inventory id`, `Entity type`, `Entity name`, `Source`, and matching `Upstream fact id` evidence in `HLD Fact Trace`.
- `Environment type`, `Function`, `Spatial relation`, `State change id`, `State change dimension`, `State before`, `State after`, and `State change` are mandatory for every row; each `State change id` must be unique and use `ENV-STATE-...` format, and the before/after tokens must be distinct uppercase state identifiers.
- If an artifact 02 support row assigned to artifact 05 names `Inventory obligations`, the artifact 05 row with that exact `Inventory id` must consume the support through `Supports`; unrelated environment rows must not consume it.
- Spatial relation must support event logistics and information access.
- Every environment `State change` is a downstream integration obligation: artifact 06 must later cite its environment and exact state-change id, record the identical `State before=>State after` transition, then record a realization with the same dimension. Artifact 05 records the required spatial condition; artifact 12 checks the completed package.
- Block if accident/lab/enclosure environments lack causal function.

## References

Good environment design makes action legible. Bad environment design is a scenic backdrop with no consequence.

### Good delivery standards

The reference standard is explicit: a passable artifact 05 must make spatial function, spatial relation, state change, access, evidence, pressure, safety, LLD handoff, and source-backed design independently reviewable.

| Dimension | Standard |
|---|---|
| Spatial function | Every environment row explains what action, restriction, observation, concealment, or encounter the place enables. |
| Spatial relation | The relation to adjacent locations makes movement, access, containment, and information flow legible. |
| State change | Each row gives a unique state-change id, an explicit dimension, distinct before/after state tokens, and states how later events must change access, evidence, pressure, safety, visibility, or containment. |
| Inventory closure | Each required environment is bound to exactly one artifact 01 inventory identity and matching upstream fact. |
| Event integration | At least one artifact 06 event cites each required environment and its exact state-change id, records the identical before/after transition, and supplies a same-dimension realization. |
| LLD handoff | Each row gives LLD a concrete spatial-design target for staging, access control, evidence placement, and changing conditions. |
| Source-backed design | Every design fact remains source-backed by artifact 01 inventory, artifact 02 support rows, PRD scenes, freeze boundaries, story-logic boundaries, or proposal claims. |

### Blocking anti-patterns

| Anti-pattern | Why it blocks |
|---|---|
| Scenic backdrop without spatial function | LLD cannot tell what the place does to action, access, evidence, or pressure. |
| Place without spatial relation | Movement and information logistics become arbitrary. |
| Static setting through an escalating event | The design omits the state change that affects safety, visibility, or control, or no later event realizes it. |
| Inventory-free environment row | Required places can be silently omitted or replaced by invented locations. |
| Support obligation consumed by another environment | A required spatial answer is attached to the wrong place and loses causal accountability. |
| Unsupported atmosphere expansion | It crosses into prose or decorative worldbuilding without source-backed necessity. |

## Traceability

Every row must cite source refs and the provisional artifact 01 `Inventory id`.

Provisional inventory refs from artifact 01 may be used before reconciliation. `artifact 10 finalizes inventory`; do not require final `inventory:INV-xx` ids in artifact 05. Environment inventory coverage is structural: artifact 05 must carry the artifact 01 provisional `Inventory id`, entity identity, source refs, and upstream fact id forward; prose-only claims of coverage are not sufficient.

## Acceptance

Pass only when all required environment inventory rows have artifact 05 design coverage, each environment has type, function, relation, state-change id, dimension, before/after transition, source closure with exact inventory-trace/main-row preservation, LLD handoff, every inventory-bound artifact 02 support row assigned to this artifact is consumed by the bound environment row, every ready artifact 02 support row assigned to this artifact is consumed, and every amendment request is routeable for artifact 10 closure. Artifact 06/11/12 integration is a later package-level gate, not an artifact 05 pass condition.

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
