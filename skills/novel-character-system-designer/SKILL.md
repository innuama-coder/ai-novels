---
name: novel-character-system-designer
description: Use when HLD artifact 04 must design the complete character and group system, including function, motivation, relationships, and information permissions.
---

# novel-character-system-designer

## Responsibility

Own HLD artifact 04 only: design HLD-level characters and groups required by the PRD.

## Inputs

- Artifacts 01-03
- Proposal character claims, PRD scenes, freeze boundaries, story-logic boundaries
- Methodology reference: `docs/superpowers/references/2026-07-08-hld-methodology-and-best-practices.md`

## Output Artifact

Produce `## Character system table` with columns:

| Character id | Inventory id | Entity type | Entity name | Role type | Function | Relationship/motivation | Relationship targets | Concrete motive evidence | Information permission | Identity boundary | Supports | Source | LLD handoff | Amendment request |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

## Artifact Metadata

Every output must include:

| Field | Value |
|---|---|
| Artifact id | `04` |
| Owner skill | `novel-character-system-designer` |
| Run id | HLD run id |
| Upstream package | final PRD package |
| Input artifacts | artifacts 01-03 |
| Output path | artifact path assigned by harness |
| Version | artifact version |

## HLD Fact Trace

Every character fact must include:

| Fact trace id | Upstream fact id | Upstream fact atom | HLD fact atom | Source refs | Expansion mode | Support mechanism | Preservation status |
|---|---|---|---|---|---|---|---|

Character facts must preserve upstream role/function facts while expanding motivation, relationship, and permission.

Every `Character id` in the main table must have a matching `Fact trace id`; the trace row `Source refs` must exactly match the main row `Source`.

`HLD fact atom` must bind the full character obligation from the main row: `Inventory id`, `Entity type`, `Entity name`, `Role type`, `Function`, `Relationship/motivation`, every non-`none` `Relationship targets`, `Concrete motive evidence`, `Information permission`, `Identity boundary`, `Supports`, `LLD handoff`, and every non-`none` `Amendment request`.

## SOP

1. Select every artifact 01 `character` and `group` inventory row assigned to artifact 04.
2. For each selected inventory row, create exactly one artifact 04 main-table row whose `Inventory id`, `Entity type`, `Entity name`, and `Source` exactly match artifact 01.
3. Preserve the artifact 01 `Upstream fact id` in the matching artifact 04 `HLD Fact Trace` row and include the inventory id, entity type, and entity name in that row's `HLD fact atom`.
4. Consume every ready artifact 02 support row assigned to this artifact through `Supports`.
5. Define narrative function before biography.
6. Define motivation and relationship pressure in human terms: desire, fear, guilt, attachment, concealment, self-protection, ambition, or loyalty.
7. Fill `Relationship targets` with existing artifact 04 `Character id` values other than the current row's own `Character id`, or `none` only when the row has no direct relationship target and `Relationship/motivation` contains no relationship-bound motive terms: attachment, loyalty, relationship, protect, protection, conceal, concealment, trust, distrust, 依恋, 忠诚, 关系, 保护, 隐瞒, 信任, 不信任.
8. Fill `Concrete motive evidence` with a concrete human pressure phrase, not a standalone label; it must include at least one pressure term such as desire, fear, guilt, attachment, concealment, self-protection, ambition, or loyalty.
9. Define information permission: what the character knows, can access, cannot access, and can reveal.
10. Fill `Identity boundary`; for digital life, explicitly state that it has an independent identity and is not the dead senior's resurrection. Block any boundary wording that also treats the digital life as the senior resurrected, equal to the senior, or the same identity as the senior.

## Boundary

Do not write full LLD biographies, scenes, dialogue, prose, or final emotional interpretation. Do not solve event mechanics owned by event/time artifacts.

## Rules

- Every character/group must support at least one PRD scene, story logic item, or inventory support need.
- Artifact 04 must consume every ready artifact 02 support row assigned to this artifact through `Supports`; block instead of leaving assigned support unused.
- Artifact 04 must not consume artifact 02 support rows assigned to any other artifact.
- Every artifact 01 `character` or `group` inventory row assigned to artifact 04 must be represented in artifact 04 by exact `Inventory id`, `Entity type`, `Entity name`, `Source`, and matching `Upstream fact id` evidence in `HLD Fact Trace`.
- `Role type`, `Function`, `Relationship/motivation`, `Information permission`, and `Identity boundary` are mandatory for every row.
- Every non-`none` `Relationship targets` value must resolve to an existing artifact 04 `Character id` other than the current row's own `Character id`; relationship-bound motive terms such as attachment, loyalty, relationship, protect, protection, conceal, concealment, trust, distrust, 依恋, 忠诚, 关系, 保护, 隐瞒, 信任, or 不信任 cannot use `none` or self-targeting.
- `Concrete motive evidence` must be a specific pressure phrase, not only `desire`, `fear`, `guilt`, `attachment`, `concealment`, `self-protection`, `ambition`, or `loyalty`.
- If an artifact 02 support row assigned to artifact 04 names `Inventory obligations`, the artifact 04 row with that exact `Inventory id` must consume the support through `Supports`; unrelated character rows must not consume it.
- Every non-`none` `Amendment request` must be routeable as `HLD-AMEND-xx`; artifact 10 owns closure.
- Relationship/motivation cannot be replaced by abstract ethics or "good/evil" framing.
- `Concrete motive evidence` cannot be abstract ethics, morality, theme-only language, or good/evil framing.
- Block if the digital life lacks a clear identity boundary or is treated as the senior's resurrection.

## References

Good character design makes later decisions inevitable but still painful. Bad character design lists traits without pressure, permission, or causal function.

### Good delivery standards

The reference standard is explicit: a passable artifact 04 must make narrative function, human pressure, relationship target closure, information permission, identity boundary, LLD handoff, and source-backed design independently reviewable.

| Dimension | Standard |
|---|---|
| Narrative function | Every character/group row explains what story work the actor performs for upstream PRD scenes or story logic. |
| Human pressure | `Relationship/motivation` and `Concrete motive evidence` express concrete desire, fear, guilt, attachment, concealment, self-protection, ambition, loyalty, trust, or distrust. |
| Relationship target closure | Direct relationship pressure names a non-self existing `Character id`; no `none`, unresolved id, or self-targeting may stand in for a relationship. |
| Information permission | Each actor states what they know, can access, cannot access, and can reveal without gaining omniscient information. |
| Identity boundary | Each actor has a stable identity boundary; digital life remains independent and is not the dead senior's resurrection. |
| LLD handoff | Each row gives LLD a concrete handoff target for later biography, scene behavior, dialogue, and pressure design. |
| Source-backed design | Every design fact remains source-backed by artifact 01 inventory, artifact 02 support rows, PRD scenes, freeze boundaries, story-logic boundaries, or proposal claims. |

### Blocking anti-patterns

| Anti-pattern | Why it blocks |
|---|---|
| Trait inventory without function | LLD cannot know why the actor appears or what scenes the actor enables. |
| Abstract ethics replacing pressure | Theme-only motive cannot drive decisions, concealment, conflict, or reversal. |
| Relationship pressure without a real target | Attachment, loyalty, concealment, trust, or distrust becomes unverifiable and cannot support relationship design. |
| Unbounded information access | The actor can accidentally solve hidden-information mechanics owned by artifact 07. |
| Digital life treated as resurrection | It violates the required identity boundary and collapses the story's identity conflict. |
| Unsupported biography expansion | It moves into LLD scope and breaks top-down source control. |

## Traceability

Every row cites source refs and the provisional inventory ref when available.

Provisional inventory refs from artifact 01 may be used before reconciliation. `artifact 10 finalizes inventory`; do not require final `inventory:INV-xx` ids in artifact 04.

Character/group inventory coverage is structural: artifact 04 must carry the artifact 01 provisional `Inventory id`, entity identity, source refs, and upstream fact id forward; prose-only claims of coverage are not sufficient.

## Acceptance

Pass only when all required character/group inventory rows have artifact 04 design coverage, all required actors have function, motive/relationship, closed relationship targets, concrete motive evidence phrase, information permission, identity boundary, source closure with exact main-row/trace source match, LLD handoff, no foreign support consumption, every inventory-bound artifact 02 support row assigned to this artifact is consumed by the bound character/group row, every ready artifact 02 support row assigned to this artifact is consumed, and every amendment request is routeable for artifact 10 closure.

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
