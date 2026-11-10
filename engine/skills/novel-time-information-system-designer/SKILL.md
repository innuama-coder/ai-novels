---
name: novel-time-information-system-designer
description: Use when HLD artifact 07 must design story time, narrative time, information objects, knowledge distribution, concealment, and reveal conditions.
---

# novel-time-information-system-designer

## Responsibility

Own HLD artifact 07 only: design source-backed time layers, knowledge states, and information-flow mechanics.

## Inputs

- Artifacts 01-06
- Authenticated PRD information-boundary contract: text-identical artifact 05, artifact 08, and final-package `## HLD information boundary table`
- Methodology reference: `engine/docs/superpowers/references/2026-07-08-hld-methodology-and-best-practices.md`

## Output Artifact

Produce `## Time and information table` with columns:

| Info id | Inventory id | Entity type | Entity name | PRD information boundary id | Freeze refs | Story anchor event ref | Time layer | Narrative reveal phase | Disclosure tier | Information object | Known by | Hidden from | Reveal predecessor refs | Reveal event ref | Reveal action | Reveal condition type | Reveal condition refs | Reveal condition | Supports | Source | LLD handoff | Amendment request |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

## Artifact Metadata

Every output must include:

| Field | Value |
|---|---|
| Artifact id | `07` |
| Owner skill | `novel-time-information-system-designer` |
| Run id | HLD run id |
| Upstream package | final PRD package |
| Input artifacts | artifacts 01-06 |
| Output path | artifact path assigned by harness |
| Version | artifact version |

## HLD Fact Trace

Every time/information fact must include:

| Fact trace id | Upstream fact id | Upstream fact atom | HLD fact atom | Source refs | Expansion mode | Support mechanism | Preservation status |
|---|---|---|---|---|---|---|---|

Information facts must preserve PRD reveal boundaries and explicitly separate usable intelligence from complete cause where required.

Every `Info id` in the main table must have a matching `Fact trace id`.

`HLD fact atom` must bind `Inventory id`, `Entity type`, `Entity name`, `PRD information boundary id`, `Freeze refs`, story anchor, time layer, narrative reveal phase, disclosure tier, knowledge state, reveal predecessor, reveal event, exact reveal action, condition type and refs, reveal condition, `Supports`, LLD handoff, and every non-`none` amendment request.

## SOP

1. Select every artifact 01 `information object` inventory row assigned to artifact 07 and its one PRD information-boundary row. Create exactly one row with the same `Inventory id`, `Entity type`, `Entity name`, `Source`, canonical upstream fact evidence, boundary id, and freeze refs.
2. Consume every ready artifact 02 support row assigned to artifact 07. Resolve one artifact 06 `Story anchor event ref`, then assign the information object to one `Time layer`: `story_chronology`, `narrative_reveal`, `memory`, `digital_interaction`, or `organizational_decision`.
3. Assign a contiguous `Narrative reveal phase` in `REVEAL-xx` format and resolved `Reveal predecessor refs` to form an acyclic reader-access graph. The story anchor records when the fact exists in story time; the phase records when the reader receives it.
4. Assign one `Disclosure tier`: `operational_intelligence`, `partial_cause`, `complete_cause`, `protected_memory`, `institutional_assessment`, or `private_motive`. Define who knows and who is hidden from the object without overlap.
5. Resolve exactly one `Reveal event ref` to artifact 06 and copy that event's exact `Event action` into `Reveal action`. Classify the reveal condition as `action`, `permission`, `access`, or `evidence_change`, resolve its one typed reference, and copy its executable fact: action repeats the reveal action, permission repeats the participant's `Information permission`, access repeats the reveal-event environment realization, and evidence change repeats the referenced event consequence.
6. Preserve the split between operational intelligence and complete cause when both tiers are present: every complete-cause object must descend from operational intelligence through `Reveal predecessor refs`.

## Boundary

Do not decide prose POV style, write revelation scenes, or change PRD event outcomes, frozen visibility, or frozen reveal order. Do not make all hidden information omnisciently available.

## Rules

- Each information object must have one exact inventory identity, one resolved story-anchor event, a valid time layer, contiguous narrative reveal phase, disclosure tier, non-overlapping known-by/hidden-from state, resolved reveal predecessor refs, one reveal event, the event's exact reveal action, typed condition refs, and a non-placeholder reveal condition.
- Artifact 07 must consume every ready artifact 02 support row assigned to this artifact through `Supports`; block instead of leaving assigned support unused.
- Every artifact 01 `information object` inventory row assigned to artifact 07 must have exactly one artifact 07 row with exact inventory identity, source refs, canonical upstream fact id/atom, and HLD Fact Trace.
- Convert each PRD `entity:<name>` knowledge reference only to the artifact 04 character/group row with the same `Entity name`; preserve `reader` exactly. Do not introduce generic knowledge labels such as `organization` or `public`.
- Story-anchor event, reveal event, condition refs, and knowledge holders must resolve to their owning artifact ids. The reveal action must exactly equal the referenced artifact 06 event action; no condition may introduce an unreferenced actor, place, permission, or evidence event.
- Time layer must be one of story_chronology, narrative_reveal, memory, digital_interaction, or organizational_decision. Disclosure tier must be one of operational_intelligence, partial_cause, complete_cause, protected_memory, institutional_assessment, or private_motive.
- Block if narrative reveal phases are skipped, predecessor refs cycle or reverse phase order, usable intelligence and complete cause collapse into one tier, or complete cause lacks an operational-intelligence predecessor.

## References

Good information design controls what can be known, when, by whom, and at what cost. Bad information design dumps truth early or hides truth without a mechanism.

### Good delivery standards

| Dimension | Standard |
|---|---|
| Inventory closure | Every required information object is bound to one artifact 01 identity and the same upstream fact. |
| Time layer and structure | The row explicitly distinguishes a time layer while the story anchor identifies when the fact exists; the contiguous narrative reveal phase and predecessor graph identify when and after what the reader receives it. |
| Disclosure tier | The design distinguishes operational intelligence, partial or complete cause, protected memory, institutional assessment, and private motive where required. |
| Knowledge state | Known-by and hidden-from make each actor's permitted knowledge legible without omniscience. |
| Reveal event and mechanism | Every reveal resolves to one artifact 06 event and repeats its exact action, so the change can occur through named participants and environment. |
| Reveal condition | The condition uses a controlled type and a resolved action, permission, access, or evidence reference; it does not introduce authorial convenience. |
| LLD handoff | The handoff gives LLD the knowledge holders, concealment, reveal trigger, and changed reader access to stage. |
| Source-backed design | Information design remains bounded by PRD scenes, freeze boundaries, story logic, proposal claims, inventory, and assigned support. |

### Blocking anti-patterns

| Anti-pattern | Why it blocks |
|---|---|
| Information without one inventory identity | Required secrets or intelligence can be silently replaced, duplicated, or contradicted. |
| Missing anchor, phase, or predecessor | LLD cannot distinguish story chronology from reader revelation or stage the disclosure order. |
| Reveal action not equal to event action | The truth appears by authorial convenience instead of through a designed event. |
| Omniscient knowledge distribution | Suspense and POV constraints collapse. |
| Operational intelligence equals complete cause | The PRD mystery resolves before its human cause can exert pressure. |
| Unsupported concealment | A secret is withheld without a source-backed mechanism. |

## Traceability

Every row cites allowed source refs, its provisional artifact 01 `Inventory id`, resolved story-anchor/reveal events, predecessor information ids, condition refs, and exact event action.

Provisional inventory refs from artifact 01 may be used before reconciliation. `artifact 10 finalizes inventory`; do not require final `inventory:INV-xx` ids in artifact 07.

## Acceptance

Pass only when all required information-object inventory rows have exactly one canonical artifact 07 row; each row has source-backed story and narrative time, a contiguous acyclic reveal graph, resolved knowledge holders, a reveal event with the exact event action, typed condition refs, and a concrete reveal condition; information access preserves the authenticated PRD frozen reader visibility, actor knowledge state, and reveal order; and every ready artifact 02 support row assigned to this artifact is consumed. Artifact 11/12 Source Map and information-closure integration are later package-level gates, not an artifact 07 pass condition.

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
