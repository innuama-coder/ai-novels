# Design Brief

## Date

2026-06-07

## Target Dev Root

`skills/novel-prd-writer`

## Target Skill Source Path

`skills/novel-prd-writer/SKILL.md`

## Dominant Skill Type

`thinking`

The skill is reasoning-heavy: it extracts intent, defines content requirements, separates PRD/HLD/LLD ownership, and performs semantic review. It does not own deterministic transformation, release packaging, runtime adapters, or multi-agent orchestration.

## Prototype Paradigm

N/A - no additional paradigm selection required for this dominant type.

This is a bounded reusable thinking skill, not a harness workflow. It has no stage graph, approval gate, retry route, delegated agent role, runtime adapter, or parent-consumed gate artifact.

## Harness Class

N/A - bounded thinking skill.

## Mission

Create and review novel PRDs that define a novel's content direction, constraints, and standards. The skill must make core roles, routes, plot functions, setting rules, theme, and style constraints explicit enough for HLD to systematically build from them.

## Responsibilities

- Define concept requirements: logline, expanded summary, core conflict, content positioning.
- Define role requirements: core roles, narrative function, Identity / Goal / Need / Flaw / Motivation / Ghost.
- Define route requirements: main route, subplot route, character route, emotional route, theme route.
- Define plot requirements: required plot functions, genre promises, hard prohibitions.
- Define setting requirements: world rules, information boundaries, usable material, forbidden breaks.
- Define style requirements: tone, narrative posture, POV overview, language texture, imagery, forbidden expression.
- Define content acceptance standards for HLD, LLD, and Writing Agent.

## Non-Responsibilities

- Does not systemically construct narrative architecture. That belongs to HLD.
- Does not design scene order, key scene tables, route nodes, or character arc milestones.
- Does not elaborate scene visuals, action, sensory material, or dialogue direction. That belongs to LLD.
- Does not write novel prose.
- Does not evaluate market demand or commercial viability.

## Subproblem Ownership Map

| Subproblem | Owner |
|---|---|
| Direction, constraints, standards | PRD writer |
| Role system, route graph, plot architecture, POV architecture | HLD writer |
| Character dossiers, space matrices, scene blueprints | LLD writer |
| Final prose | Writing Agent / writer skill |

## Input Contract

Required:

- project name or temporary stable code name
- raw novel idea, old draft, concept note, or user intent

Optional but extractable:

- genre or subject inclination
- core role candidates
- core conflict
- setting rules
- style preference
- known prohibitions

Missing optional items must be marked `待定`; the skill must not silently invent them as facts.

## Execution Contract

1. Extract facts, assumptions, and unknowns.
2. Convert the idea into content requirements.
3. Mark Must / Should / Could / Won't.
4. Keep HLD/LLD/Writing responsibilities out of the PRD.
5. Define content acceptance standards.
6. Run semantic review with pass/revise/fail.

## Output Contract

Canonical PRD output must include:

- summary
- core concept
- role requirements
- setting requirements
- route and plot constraints
- theme, style, and narrative constraints
- optional series planning
- content acceptance matrix
- risks and open questions

## Lifecycle Plan

- Design stage outputs: this design brief, file plan, evaluation spec.
- Implementation stage outputs: updated `SKILL.md` hard contract and references.
- Testing stage outputs: test plan with positive, negative, and boundary cases.
- Release stage outputs or checks: no release package currently required.

## Self-Improving Loop Contract

N/A - not a self-improving workflow.

The skill can revise its output when semantic review fails, but it does not own a staged retry loop or persistent feedback packet.

## Validator And Semantic Review Plan

No deterministic validator can fully judge a novel PRD because acceptance is semantic. The skill uses a two-layer review:

- objective checks: `scripts/validate_prd_structure.py <artifact> --json` verifies required sections, Must/Won't constraints, and obvious forbidden drift.
- subjective checks: clarity, constraint strength, downstream consumability, method-to-field traceability.

## Done Criteria

- `SKILL.md` contains hard contracts.
- Required lifecycle docs exist.
- Evaluation spec defines positive, negative, and boundary cases.
- Test plan defines how an agent should exercise the skill.
- Structure validator passes positive fixture and fails negative/boundary fixtures for expected reasons.
- References map to PRD fields, constraints, or review rules.

## Trigger Design

Trigger when the user asks to create, harden, review, or revise a novel PRD, or asks to define novel content requirements before HLD/LLD.

Do not trigger for direct prose writing, detailed scene design, HLD architecture, or workflow packaging.

## Boundary With skill-creator

No conflict. This work is not generic skill scaffolding; it is architecture and hardening of an existing domain thinking skill under harness engineering standards.

## Encoding Hygiene Plan

All files are UTF-8 Markdown with simplified Chinese content in runtime instructions. Avoid mojibake and platform-default encoding assumptions.

## Composition Notes

The skill composes with:

- `novel-hld-writer`: consumes PRD requirements.
- `novel-lld-writer`: consumes HLD output and PRD constraints.
- writer skills: consume LLD and PRD style constraints.

## Risks Or Open Questions

- The current repo skill layout is flatter than the harness standard `skill/SKILL.md` package layout. This is accepted as an explicit compatibility contract: the runtime skill is discovered at `skills/novel-prd-writer/SKILL.md`, while lifecycle docs, references, scripts, and tests live beside it under the same dev root.
- No automated semantic evaluator exists yet; subjective review remains required.
