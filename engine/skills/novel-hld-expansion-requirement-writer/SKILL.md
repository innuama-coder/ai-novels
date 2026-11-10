---
name: novel-hld-expansion-requirement-writer
description: Use when a PRD needs explicit HLD expansion requirements and upstream HLD entity handoff for world, role, environment, event, style, and POV design.
---

# novel-hld-expansion-requirement-writer

## Responsibility

List what HLD must expand so the PRD trunk scenes can run, and declare the upstream entities HLD artifact 01 must inventory.

## Input

- Accepted proposal
- Specified part scope and goal
- Trunk scene table
- Story logic boundary table, when artifact 03 contains one
- Conflict/value and information-flow tables
- PRD freeze boundary list

## Output

Produce markdown section `## HLD expansion requirement list` with:

| Field | Requirement |
|---|---|
| Requirement id | Stable id such as `HLD-REQ-01` |
| Required expansion | World, role, environment, event, information, style, or POV item |
| Supports scene ids | Trunk scene ids needing this expansion |
| Information boundary refs | `none` or resolved `PRD-INFO-xx` ids whose `HLD obligation` this requirement must answer |
| Inherited HLD obligations | `none` or the exact artifact 05 obligation text for every cited information boundary |
| Required answer | What HLD must decide |
| Boundary | What HLD cannot change while answering |
| Source | Structured source refs, such as `scene:PRD-S01` or `claim:CLAIM-01` |

Also produce markdown section `## Upstream required HLD entities` with:

| Field | Requirement |
|---|---|
| Upstream fact id | Stable id such as `UPF-PRD-S01-01` |
| Source fact field | One canonical artifact 03 field: `Entry state`, `Roles`, `Environment`, `Event`, `Causal output`, `Scene content`, `Previous dependency`, `Next pressure`, or `Indispensability proof` |
| Upstream fact atom | The complete, byte-for-byte value of the named source fact field; HLD may expand it but may not rewrite it |
| Required HLD entity | Entity name HLD must inventory |
| Required entity type | One of character, group, environment, event, rule, information object, time layer, thread, style/pov rule, unresolved amendment |
| Source refs | Structured source refs, such as `scene:PRD-S01` or `claim:CLAIM-01` |

When artifact 03 contains a Story logic boundary table, also produce `## Story logic requirement coverage`:

| Field | Requirement |
|---|---|
| Boundary id | One existing `PRD-LOGIC-nn` id |
| HLD requirement id | One existing requirement that expands this boundary |
| Inherited frozen answer | The exact artifact 03 `Frozen answer` for that boundary |

## Rules

- Requirements must expose hidden assumptions in the PRD.
- Every requirement must support at least one trunk scene or freeze item.
- Every `PRD-INFO-xx` HLD obligation from artifact 05 must be cited by at least one requirement. For every cited boundary, the requirement's `Supports scene ids` and `Source` must each include the boundary's story-anchor or narrative-reveal scene, and `Inherited HLD obligations` must reproduce the exact `HLD obligation`. `none` is permitted only when the requirement consumes no information-boundary obligation.
- `Requirement id` must match `HLD-REQ-nn` and be unique within the artifact. It is the stable identifier consumed by downstream `hldreq:` refs.
- `Supports scene ids` may cite only scene ids already present in the PRD trunk scene table. The complete set must exactly equal the `scene:PRD-Sxx` refs in that row's `Source`; proposal claims may be additional evidence but cannot stand in for a supported scene.
- `Source` may cite only canonical PRD scene facts as `scene:PRD-Sxx` or upstream proposal claims as `claim:CLAIM-xx`.
- `Upstream required HLD entities` must include every entity that HLD artifact 01 needs before world inventory can begin: roles, groups, environments, events, rules, information objects, time layers, threads, and style/POV rules implied by PRD scenes, freeze boundaries, and HLD requirements.
- Each upstream required entity must be sparse and factual. `Upstream fact atom` must preserve the complete named PRD field, while the entity name must not hide later HLD design, motivation, mechanics, or causal explanation.
- `Upstream fact id` must follow `UPF-PRD-Sxx-nn` and cite that exact `scene:PRD-Sxx`. `Source fact field` must name one allowed canonical artifact 03 field. `Upstream fact atom` must equal that field's entire value exactly, and `Required HLD entity` must occur verbatim in the atom; an ID and source reference without this four-way binding is not a fact-level handoff.
- Every `entity:<名称>` named in artifact 05's frozen knowledge state must resolve to at least one `character` or `group` fact row. The same entity may need multiple fact rows when distinct PRD scenes establish its role; do not defer an unregistered knowledge holder to HLD.
- Every artifact 03 Story logic boundary must have exactly one coverage row. Its cited requirement must support and source at least one logic-boundary scene, and its `Inherited frozen answer` must equal the boundary's `Frozen answer` exactly.
- Every artifact 03 `Required HLD entity refs` value must resolve to at least one `character` or `group` fact row in `Upstream required HLD entities` whose `Upstream fact id` scene is one of that logic boundary's `Source` scenes. Additional `Source refs` cannot substitute for this fact-id anchor. A scene-level row alone cannot substitute for a named logic-boundary entity.
- The final PRD package must reproduce both this table and the complete `HLD expansion requirement list` exactly; a changed fact field, fact atom, entity name, type, source, requirement, inherited obligation, or boundary is trace drift and blocks packaging.
- Every canonical trunk scene must have at least one upstream required HLD entity row.
- Free text source labels, raw `PRD-Sxx`, and raw `CLAIM-xx` are not valid source closure.
- HLD can choose implementation details only within the stated boundary.
- If artifact 03 contains `Story logic boundary table`, HLD requirements must preserve each frozen causal answer and define only the allowed expansion room.

## Boundary

- Do not write HLD world bible content.
- Do not define all characters, locations, events, or prose style.
- Do not let HLD requirements rewrite PRD trunk order or proposal facts.

## References

Good HLD requirement: names the missing world/role/environment/event decision and the PRD scene it supports.

Good upstream required HLD entity: `UPF-PRD-S01-01 | 情报员抵达接应点前试图传递压缩情报包。 | 情报员 | character | scene:PRD-S01, claim:CLAIM-10`. When a logic boundary depends on the same person in another scene, add a separate fact row anchored to that scene rather than attaching an unrelated scene ref.

Bad HLD requirement: broad wish such as "make the organization believable" without support scene or boundary.

Bad upstream required HLD entity: "复杂的组织阴谋" when the PRD only requires an organization group and an authority boundary; that hides HLD design in an entity name.

## Traceability

Every requirement and upstream required HLD entity must trace through structured `Source` refs to proposal claims or canonical PRD trunk scene facts.

## Acceptance

Pass only when HLD receives explicit, source-backed expansion tasks, complete story-logic inheritance, and a structured upstream HLD entity table without having to reinvent the PRD trunk.

## Skill Verdict

Produce markdown section `## Skill Verdict` with:

| Field | Requirement |
|---|---|
| Skill quality verdict | `pass`, `revise_own_output`, or `reopen_upstream` |
| Source closure | `pass` only when every requirement and upstream required HLD entity supports existing PRD scene ids and valid source references |
| Boundary obedience | `pass` only when requirements ask HLD to expand, not rewrite, PRD/proposal facts |
| Downstream readiness | `pass` only when HLD can build world, role, environment, event, information, style, and POV support from the list and artifact 01 can start from `Upstream required HLD entities` |
| Blocking issue | `none` or stable issue id |
| Rerun target | `none`, this skill, an upstream PRD skill, or `proposal` |
