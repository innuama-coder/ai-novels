# Design Brief

## Date

2026-06-07

## Target Dev Root

`skills/novel-hld-writer`

## Target Skill Source Path

`skills/novel-hld-writer/SKILL.md`

## Dominant Skill Type

`thinking`

HLD is reasoning-heavy: it systematically constructs narrative architecture from a PRD. It does not own deterministic transformation, runtime adapters, release packages, or multi-agent orchestration.

## Mission

Create and review novel HLDs that systemically construct PRD-defined roles, routes, plot functions, setting, time, pacing, POV, style, and key scene functions into an architecture consumable by LLD.

## Responsibilities

- Confirm PRD inheritance.
- Build role hierarchy, relationships, and arc types.
- Build route/thread architecture.
- Build plot structure and key scene function table.
- Build space, time, pacing, and POV architecture.
- Convert PRD style constraints into HLD-level style rules.
- Produce an HLD-to-LLD handoff package.

## Non-Responsibilities

- Does not redefine PRD direction, constraints, or standards.
- Does not elaborate scene visuals, action, dialogue, sensory detail, or materials.
- Does not write prose.
- Does not create a multi-stage workflow.

## Input Contract

Required:

- PRD or equivalent content-requirements packet
- core role requirements
- route and plot requirements
- setting and style constraints

Missing required inputs cause `fail`.

## Execution Contract

1. Confirm inherited PRD constraints.
2. Construct role architecture.
3. Construct route/thread architecture.
4. Construct plot structure and key scene functions.
5. Construct space, time, pacing, and POV architecture.
6. Define HLD-level style rules.
7. Produce LLD handoff and semantic verdict.

## Output Contract

Canonical output:

- PRD trace
- role architecture
- route/thread architecture
- plot and key scene functions
- space architecture
- time architecture
- pacing architecture
- POV architecture
- style rules
- HLD-to-LLD handoff
- risks and open questions

## Validator And Semantic Review Plan

- Objective check: `scripts/validate_hld_structure.py <artifact> --json`.
- Subjective review: HLD rubric in `docs/evaluation-spec.md`.

## Done Criteria

- `SKILL.md` contains hard contracts and frontmatter.
- Lifecycle docs exist.
- Validator passes positive fixture and fails negative/boundary fixtures.
- References map methods to HLD fields, not to LLD details.

## Layout Compatibility

The runtime skill is discovered at `skills/novel-hld-writer/SKILL.md`; docs, scripts, tests, and references live beside it under the same dev root.

## Risks

- Some existing HLD workflow sections are detailed; future refactors may move more methodology into references for stronger progressive disclosure.
