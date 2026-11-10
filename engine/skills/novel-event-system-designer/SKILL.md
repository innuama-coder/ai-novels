---
name: novel-event-system-designer
description: Use when HLD artifact 06 must design visible, hidden, background, implied, and causal events required to make PRD scenes logically complete.
---

# novel-event-system-designer

## Responsibility

Own HLD artifact 06 only: design source-backed event systems and causal mechanics that support PRD scenes.

## Inputs

- Artifacts 01-05
- PRD scene facts, story-logic boundaries, HLD event support rows
- Methodology reference: `engine/docs/superpowers/references/2026-07-08-hld-methodology-and-best-practices.md`

## Output Artifact

Produce `## Event system table` with columns:

| Event id | Inventory id | Entity type | Entity name | Event type | Visibility | Cause refs | Event action | Causal role | Participants | Environment refs | Environment state change refs | Environment state transitions | Environment state realizations | Consequences | Supports | Source | LLD handoff | Amendment request |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

## Artifact Metadata

Every output must include:

| Field | Value |
|---|---|
| Artifact id | `06` |
| Owner skill | `novel-event-system-designer` |
| Run id | HLD run id |
| Upstream package | final PRD package |
| Input artifacts | artifacts 01-05 |
| Output path | artifact path assigned by harness |
| Version | artifact version |

## HLD Fact Trace

Every event fact must include:

| Fact trace id | Upstream fact id | Upstream fact atom | HLD fact atom | Source refs | Expansion mode | Support mechanism | Preservation status |
|---|---|---|---|---|---|---|---|

Event facts must preserve PRD scene outcome and order while expanding bounded hidden/background causal mechanics.

Every `Event id` in the main table must have a matching `Fact trace id`.

`HLD fact atom` must bind `Inventory id`, `Entity type`, `Entity name`, `Cause refs`, `Event action`, `Causal role`, `Environment refs`, `Environment state change refs`, `Environment state transitions`, `Environment state realizations`, `Consequences`, supports, LLD handoff, and every non-`none` amendment request.

## SOP

1. Select every artifact 01 `event` inventory row assigned to artifact 06. Create exactly one event row with the same `Inventory id`, `Entity type`, `Entity name`, `Source`, and canonical upstream fact evidence.
2. Consume every ready artifact 02 support row assigned to artifact 06 and apply its character/environment constraints through `Supports`.
3. Classify the event's narrative function as `trigger`, `escalation`, `reversal`, `revelation`, `decision`, or `consequence`; record reader access separately in `Visibility`.
4. Write a concrete HLD-level `Event action`, then identify its `Causal role` and the changed condition in `Consequences`; do not write scene prose.
5. Populate `Cause refs` with the event's exact upstream source refs and, for every non-trigger event, at least one resolved preceding `Event id`. Do not create cycles or self-reference.
6. Resolve `Environment refs` to artifact 05 `Environment id` values and cite exactly the corresponding artifact 05 `State change id` values in `Environment state change refs`. For each state id, write one `Environment state transitions` item as `ENV-STATE-...:STATE_BEFORE=>STATE_AFTER` and one `Environment state realizations` item as `ENV-STATE-... [dimension]: concrete change caused by this event`; both must exactly preserve artifact 05.
7. Preserve PRD scene order and outcome. Ensure major-event mechanics pass through the researcher/digital-life interaction when PRD requires it.

## Boundary

Do not write scenes, decide POV style, or collapse hidden causes into reader-visible exposition. Do not replace PRD crisis resolution.

## Rules

- Every event must have a non-placeholder `Event action`, `Causal role`, and `Consequences`; each must identify a concrete action, story pressure/function, and changed condition rather than say only that the story advances.
- Artifact 06 must consume every ready artifact 02 support row assigned to this artifact through `Supports`; block instead of leaving assigned support unused.
- Every artifact 01 `event` inventory row assigned to artifact 06 must be represented by exact `Inventory id`, `Entity type`, `Entity name`, `Source`, and matching upstream fact id/atom evidence in `HLD Fact Trace`.
- Event type must be one of trigger, escalation, reversal, revelation, decision, or consequence. Visibility must be one of visible, background, hidden, or implied; the two axes must not be conflated.
- Visibility must be one of visible, background, hidden, or implied.
- `Cause refs` must not be empty. Each source ref must exactly occur in the event's `Source`; each event-id ref must resolve to a different artifact 06 event. Every non-trigger event must cite at least one predecessor event, and the resulting event causal graph must be acyclic.
- Participants must resolve to character/group ids or amendment requests.
- Every event must cite one or more resolved artifact 05 `Environment refs`; its `Environment state change refs` must equal the exact state-change ids owned by those environments. `Environment state transitions` must contain the exact before/after pair owned by each cited environment. `Environment state realizations` must contain exactly one non-placeholder realization for each cited state id and the same artifact 05 dimension. Each artifact 05 environment must be cited by at least one event, because decorative locations are out of scope.
- Block if major event mechanics bypass researcher/digital life.

## References

Good event design makes change inevitable and reviewable. Bad event design is chronology without causal pressure, consequence, or source accountability.

### Good delivery standards

| Dimension | Standard |
|---|---|
| Inventory closure | Each required event is bound to one artifact 01 event identity and the same upstream fact. |
| Causal chain | Trigger events begin from their cited upstream conditions; every other event names a resolved predecessor, and the directed chain has no loop. |
| Trigger closure | Every trigger names the exact PRD, freeze, claim, requirement, or story-logic condition that starts it. |
| Event action | Each row identifies the concrete HLD-level action or occurrence, not a scene summary or an abstract theme. |
| Causal role | Each event changes the available choice, pressure, knowledge, permission, relationship, or risk in a way the next event can use. |
| Consequence | Each row states the changed condition left by the event; “the plot advances” is not a consequence. |
| Visibility | What the reader can observe is explicit and remains distinct from the event's narrative function. |
| Environment integration | Every event realizes the exact environment state transition it uses, with a same-dimension consequence. |
| LLD handoff | The handoff gives LLD a concrete event-action, causality, participant, access, and consequence target. |
| Source-backed design | Action, cause, and consequence remain bounded by PRD scenes, freeze boundaries, story logic, proposal claims, inventory, and assigned support. |

### Blocking anti-patterns

| Anti-pattern | Why it blocks |
|---|---|
| Chronology without causal chain | Later events can be rearranged or removed without changing the design. |
| Empty action, role, or consequence | LLD cannot stage what happens, why it matters, or what becomes different. |
| Non-trigger without predecessor | The event appears by authorial convenience rather than an established condition. |
| Cyclic event cause | The design contains an impossible causal loop. |
| Visibility used as event type | Narrative function and reader access can contradict one another. |
| Unsupported event invention | The skill silently replaces PRD facts instead of routing an amendment. |

## Traceability

Every event row must cite source refs, its provisional artifact 01 `Inventory id`, and its cause refs.

Provisional inventory refs from artifact 01 may be used before reconciliation. `artifact 10 finalizes inventory`; do not require final `inventory:INV-xx` ids in artifact 06.

## Acceptance

Pass only when all required event inventory rows have exact artifact 06 coverage; every event has a concrete action, causal role, consequence, resolved cause refs, and acyclic causal-chain closure; participants and environments resolve; every environment transition is exact; every ready artifact 02 support row assigned to this artifact is consumed; and the artifact is ready for time/information design. Artifact 11/12 Source Map and event-closure integration are later package-level gates, not an artifact 06 pass condition.

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
