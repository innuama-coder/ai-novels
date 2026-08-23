# Design Brief

## Date

2026-06-07

## Target Dev Root

`skills/novel-lld-writer`

## Target Skill Source Path

`skills/novel-lld-writer/SKILL.md`

## Dominant Skill Type

`thinking`

LLD is reasoning-heavy: it turns an approved HLD into detailed, writing-ready settings. It does not own PRD direction, HLD architecture, final prose, runtime adapters, release packages, or multi-agent orchestration.

## Mission

Create and review novel LLDs that detail HLD-defined roles, spaces, route nodes, key scene functions, sensory/callback materials, and writing handoff rules into a package consumable by the Writing Agent.

## Responsibilities

- Confirm HLD inheritance and PRD constraint awareness.
- Detail character behavior, language, motivation, and scenario markers.
- Detail spaces through sensory state, objects, constraints, and character-space interaction.
- Materialize route nodes into usable writing material.
- Convert HLD key scene functions into scene blueprints.
- Prepare reusable sensory, callback, and continuity materials.
- Produce a Writing Agent handoff package.

## Non-Responsibilities

- Does not redefine PRD direction, constraints, standards, route, or style baseline.
- Does not redefine HLD character arcs, route architecture, or key scene functions.
- Does not write final prose, full dialogue, or chapter text.
- Does not create a multi-stage workflow.

## Input Contract

Required:

- HLD or equivalent architecture packet
- PRD constraint summary
- core character list
- core space list
- key scene function table

Missing required inputs cause `fail`.

## Execution Contract

1. Confirm inherited HLD architecture and PRD constraints.
2. Detail character design.
3. Detail space design.
4. Materialize route nodes.
5. Blueprint key scenes.
6. Prepare sensory/callback materials.
7. Produce Writing Agent handoff and semantic verdict.

## Output Contract

Canonical output:

- HLD trace
- detailed character design
- detailed space design
- route-node materialization
- key scene blueprint
- sensory and callback materials
- writing guidance and forbidden items
- Writing Agent handoff package
- risks and open questions

## Validator And Semantic Review Plan

- Objective check: `scripts/validate_lld_structure.py <artifact> --json`.
- Subjective review: LLD rubric in `docs/evaluation-spec.md`.

## Done Criteria

- `SKILL.md` contains hard contracts and frontmatter.
- Lifecycle docs exist.
- Validator passes positive fixture and fails negative/boundary fixtures.
- References map methods to LLD fields, not to HLD architecture or prose writing.

## Layout Compatibility

The runtime skill is discovered at `skills/novel-lld-writer/SKILL.md`; docs, scripts, tests, and references live beside it under the same dev root.

## Risks

- LLD can easily drift into prose. The validator and semantic rubric both treat prose, full dialogue, and chapter text as boundary failures.
