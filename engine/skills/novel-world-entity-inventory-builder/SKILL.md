---
name: novel-world-entity-inventory-builder
description: Use when HLD artifact 01 must identify the complete initial world entity inventory required by proposal, PRD, freeze boundaries, HLD requirements, and story logic.
---

# novel-world-entity-inventory-builder

## Responsibility

Own HLD artifact 01 only: identify every entity that must exist before HLD system design can proceed.

## Inputs

- Accepted proposal claims and Claim Source Map
- Final PRD package, PRD scenes, PRD freeze boundaries, HLD expansion requirements, story-logic boundaries
- Mandatory upstream `## Upstream required HLD entities` table with `Upstream fact id`, `Source fact field`, `Upstream fact atom`, `Required HLD entity`, `Required entity type`, and `Source refs`
- HLD methodology reference: `engine/docs/superpowers/references/2026-07-08-hld-methodology-and-best-practices.md`

## Output Artifact

Produce `## Initial world entity inventory` with columns:

| Inventory id | Entity type | Entity name | Required HLD owner | Secondary HLD owners | Upstream evidence | Source | Initial status |
|---|---|---|---|---|---|---|---|

Allowed entity types: character, group, environment, event, rule, information object, time layer, thread, style/pov rule, unresolved amendment.

`Inventory id` must be unique within artifact 01.

Required owner routing:

| Entity type | Required HLD owner |
|---|---|
| rule | artifact 03 |
| character | artifact 04 |
| group | artifact 04 |
| environment | artifact 05 |
| event | artifact 06 |
| information object | artifact 07 |
| time layer | artifact 07 |
| thread | artifact 08 |
| style/pov rule | artifact 09 |
| unresolved amendment | artifact 10 |

## Artifact Metadata

Every output must include:

| Field | Value |
|---|---|
| Artifact id | `01` |
| Owner skill | `novel-world-entity-inventory-builder` |
| Run id | HLD run id |
| Upstream package | final PRD package and proposal package |
| Input artifacts | PRD scenes, freeze boundaries, HLD requirements, story-logic boundaries, proposal claims |
| Output path | artifact path assigned by harness |
| Version | artifact version |

## HLD Fact Trace

Every inventory decision must include:

| Fact trace id | Upstream fact id | Upstream fact atom | HLD fact atom | Source refs | Expansion mode | Support mechanism | Preservation status |
|---|---|---|---|---|---|---|---|

For artifact 01, `HLD fact atom` is the required entity existence claim and must bind entity type, entity name, required owner, secondary owners when non-`none`, upstream evidence, and initial status. `Expansion mode` is usually `support` or `handoff`.

Every `Inventory id` in the main table must have exactly one matching `Fact trace id`. `Fact trace id` must be unique within `## HLD Fact Trace`.

## SOP

1. Start from the mandatory structured `Upstream required HLD entities` table. Every row must include a permitted `Source fact field`, and every row must become at least one inventory row with the same upstream fact id and exact upstream fact atom in HLD Fact Trace. If the table is missing or uses a legacy field set, fail with `Downstream readiness = reopen_upstream:PRD`.
2. Then scan PRD scenes and freeze/HLD/story-logic rows for required entities by type: character, group, environment, event, rule, information object, time layer, thread, and style/pov rule. Include abstract entities such as permissions, locked information, protocols, authority boundaries, and POV limits when they carry action, knowledge, pressure, permission, or consequence.
3. Convert each required entity into one inventory row with a unique `Inventory id` and the owner required by the entity-type routing matrix. Put cross-domain handoff owners in `Secondary HLD owners` or `none`; every non-`none` secondary owner is a downstream support obligation for artifact 02 and must remain tied to this row's `Inventory id` and exact same source refs.
4. Use source refs only from the allowed grammar.
5. Use `Initial status = active` for normal rows. Mark gaps only as `Initial status = amendment_needed:HLD-AMEND-xx:<reason>`, set `Entity type = unresolved amendment`, and set `Required HLD owner = artifact 10`. Do not use free-text status.

## Secondary scan checklist

After importing every structured upstream required entity, run these passes over PRD scenes, freeze boundaries, HLD expansion requirements, story-logic boundaries, and proposal claims. Add only missing required entities; do not replace or redesign upstream rows.

| Pass | Required check | Entity types to add when missing |
|---|---|---|
| Actor and group pass | Identify every actor, collective actor, institution, review body, authority holder, or knowledge holder that acts, pressures, decides, permits, withholds, observes, or is protected. | character, group |
| Place and interface pass | Identify every place, enclosure, channel, interface, report surface, system boundary, or spatial transition that constrains action, access, visibility, or logistics. | environment |
| Event and process pass | Identify every visible, hidden, background, implied, trigger, reversal, revelation, consequence, authorization, handoff, extraction, or termination process required for later HLD design. | event |
| Rule and authority pass | Identify every protocol, permission boundary, institutional limit, technology limit, ethical/legal rule, security rule, authority boundary, or no-change constraint that controls what can happen. | rule |
| Information and memory pass | Identify every report, clue, memory fragment, locked information, usable intelligence, complete cause, identity secret, log, source record, or knowledge state that changes action or pressure. | information object |
| Time and reveal pass | Identify every countdown, action window, preservation window, memory layer, review period, sequence dependency, reveal timing, or before/after state required to keep causality stable. | time layer |
| Thread and POV pass | Identify every main, hidden, emotional, institutional, identity, theme, or POV/information-access constraint that must be tracked by later thread or style/POV artifacts. | thread, style/pov rule |
| Amendment pass | If an input requires an entity but its type, source, or owner cannot be structured without inventing facts, add one routeable unresolved amendment row instead of guessing. | unresolved amendment |

## Boundary

Do not design the entity. Do not decide motivations, mechanics, rules, or causal consequences. Do not merge distinct entities merely because they look similar.

## Rules

- Every PRD scene, freeze item, HLD requirement, story-logic boundary, and proposal claim that requires HLD support must have at least one inventory row.
- Upstream source coverage is source-ref level: every `scene:`, `freeze:`, `hldreq:`, `claim:`, and `storylogic:` ref extracted from the PRD/proposal source inventory must appear in at least one inventory row `Source`.
- Upstream entity coverage is fact/entity level: every structured upstream required entity must match an inventory row by upstream fact id, exact upstream fact atom, entity name, entity type, and source refs. Missing upstream required entity table blocks HLD entry and reopens PRD.
- Required HLD owner and every non-`none` Secondary HLD owners entry must be one of artifacts 03-09, or artifact 10 for amendments.
- Required HLD owner must match the entity-type routing matrix; do not route entities by convenience or downstream workload.
- `Inventory id` and `Fact trace id` must be one-to-one and unique; duplicate ids block artifact 01 even if table content looks identical.
- Every non-`none` Secondary HLD owners entry declares an artifact 02 support obligation bound to this row's `Inventory id` and exact same source refs; partial source overlap is not valid binding.
- `Initial status` must be `active` or `amendment_needed:HLD-AMEND-xx:<reason>`.
- Amendment rows must use `Initial status = amendment_needed:HLD-AMEND-xx:<reason>` and must be closed by artifact 10.
- The Secondary scan checklist must be completed after upstream import; if any pass cannot be completed from structured sources, emit a routeable amendment row rather than silently omitting the entity.
- Block if any required entity type is missing or source cannot be structured.

## References

Good inventory is complete, sparse, source-backed, and owner-routed. Bad inventory hides design decisions in entity names or misses critical entities such as protected person, digital life, organization, accident/death context, memory closure, major event, lab, enclosure, information object, and POV limit.

## Traceability

Every row must include `Source` using `scene:`, `freeze:`, `hldreq:`, `claim:`, or `storylogic:`. Inventory ids are provisional until artifact 10 finalizes inventory. HLD Fact Trace must preserve the upstream fact id for every structured upstream required entity.

## Acceptance

Pass only when the inventory covers all upstream support needs, all upstream source refs, and every structured upstream required entity; contains no invented design facts; routes every entity to one primary HLD owner; records secondary HLD owner obligations when cross-domain handoff is required; and emits only routeable amendment ids and allowed initial statuses.

## Skill Verdict

| Field | Value |
|---|---|
| Skill quality verdict | `pass`, `pass_with_p2`, or `fail` |
| Source closure | `closed` or `open:<reason>` |
| Inventory coverage | `closed` or `open:<reason>` |
| Boundary obedience | `pass` or `violation:<source ref>` |
| Downstream readiness | `ready`, `blocked:<reason>`, or `reopen_upstream:<target>` |
| Blocking issue | `none` or stable issue ids |
| Rerun target | `none` or artifact/skill id |
