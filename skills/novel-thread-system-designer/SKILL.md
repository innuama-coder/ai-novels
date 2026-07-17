---
name: novel-thread-system-designer
description: Use when HLD artifact 08 must design main, hidden, emotional, thematic, and support threads with distribution, crossover, and closure.
---

# novel-thread-system-designer

## Responsibility

Own HLD artifact 08 only: design the HLD thread system.

## Inputs

- Artifacts 01-07
- PRD trunk scene sequence, conflict/value, story-logic boundaries
- Methodology reference: `docs/superpowers/references/2026-07-08-hld-methodology-and-best-practices.md`

## Output Artifact

Produce `## Thread system table` with columns:

| Thread id | Thread type | Thread function | Thread anchor refs | Required pressure refs | Core question | Node distribution | Thread progression | Crossover | Closure state | Closure outcome | Supports | Source | LLD handoff | Amendment request |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

## Artifact Metadata

Every output must include:

| Field | Value |
|---|---|
| Artifact id | `08` |
| Owner skill | `novel-thread-system-designer` |
| Run id | HLD run id |
| Upstream package | final PRD package |
| Input artifacts | artifacts 01-07 |
| Output path | artifact path assigned by harness |
| Version | artifact version |

## HLD Fact Trace

Every thread fact must include:

| Fact trace id | Upstream fact id | Upstream fact atom | HLD fact atom | Source refs | Expansion mode | Support mechanism | Preservation status |
|---|---|---|---|---|---|---|---|

Thread facts must preserve PRD causal answers while mapping pressure distribution and closure.

Every `Thread id` in the main table must have a matching `Fact trace id`.

## SOP

1. Consume every ready artifact 02 support row assigned to this artifact, then identify main crisis, hidden cause, emotional relation, digital-life identity, organizational pressure, and theme threads required by PRD.
2. Bind each core thread to the required HLD design anchor: main/theme to an event, hidden to information, emotional to a character, institutional to a world rule, and identity to both a character and information object.
3. Resolve every PRD scene through HLD event/information ids, then define each thread as a question whose ordered node states change in `Thread progression` using `HLD-06/07-id: state -> HLD-06/07-id: changed state`.
4. Define crossover points, closure state, and the resulting story state.

## Boundary

Do not invent new plotlines, reorder PRD scenes, write chapter outlines, or decide prose execution.

## Rules

- Thread type must be main, hidden, emotional, theme, institutional, identity, or support.
- The system must include at least one main, hidden, emotional, theme, institutional, and identity thread. Each core question must be a substantive question ending in `?` or `？`.
- Core `Thread function` values are fixed by type: `main=advance_crisis_resolution`, `hidden=withhold_then_reframe_cause`, `emotional=convert_private_relation_to_cost`, `theme=test_value_through_choice`, `institutional=apply_systemic_pressure`, and `identity=separate_digital_life_from_human_memory`; a support thread uses `support`.
- Core `Thread anchor refs` must resolve to actual HLD rows: main and theme include `event:HLD-06-nn`, hidden includes `information:HLD-07-nn`, emotional includes `character:HLD-04-nn`, institutional includes `rule:HLD-03-nn`, and identity includes both `character:HLD-04-nn` and `information:HLD-07-nn`.
- `Required pressure refs` must use structured `scene:`, `freeze:`, `hldreq:`, `claim:`, or `storylogic:` refs that occur in the row's consumed artifact 02 support sources. Core questions must be distinct, and every core thread must have at least one pressure ref not used by another core thread.
- Node distribution must contain at least two distinct HLD event or information ids, in the same order as `Thread progression`; PRD scene ids are evidence only and cannot be node ids. Each progression state must be substantive and differ from the other states. A required thread cannot remain `blocked`.
- `Crossover` must use `thread:HLD-08-nn; effect=<substantive crossover effect>`, target another declared thread, and make the required-thread graph connected.
- Artifact 08 must consume every ready artifact 02 support row assigned to this artifact through `Supports`; block instead of leaving assigned support unused.
- Closure state must be explicit: closed, deliberately unresolved, transferred_to_lld, or blocked.
- Closure outcome must state the resulting story state; a closure enum alone is not a closure.

## References

Good threads create accumulated expectation and release through a type-specific function, resolved HLD design anchors, independently traced pressure, an ordered change of state across story nodes, a named crossover, and an explicit resulting state. Bad threads are labels, duplicated questions, shared-only pressure, PRD scene ids presented as HLD nodes, stateless node lists, decorative crossovers, or closure enums without an outcome.

## Traceability

Every row cites source refs and relevant event/info ids through supports.

Provisional inventory refs from artifact 01 may be used before reconciliation. `artifact 10 finalizes inventory`; do not require final `inventory:INV-xx` ids in artifact 08.

## Acceptance

Pass only when every required story pressure has resolved HLD anchors, node distribution, ordered progression, crossover, closure, LLD handoff, and every ready artifact 02 support row assigned to this artifact is consumed.

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
