# DP-HLD-003 Global Spec And Legacy Migration Design

## Source Refs

- `engine/docs/superpowers/plans/2026-07-07-novel-hld-workflow-refactor.md`
- `engine/docs/superpowers/specs/2026-07-05-novel-harness-workflows-and-skills-design.md`
- `engine/docs/superpowers/specs/2026-07-05-novel-creation-workflow-design.md`
- `engine/skills/novel-hld-writer/SKILL.md`

## Scope Boundary

This task designs updates to global workflow specifications and the legacy HLD writer entry. It does not change novel story content and does not produce HLD business artifacts. It removes conflicting authority between old HLD descriptions and the new twelve-artifact workflow.

## Control Flow

The migration first updates the harness workflow specification, then updates the creation workflow HLD boundary, then downgrades `novel-hld-writer` into a legacy pointer. After each step, validator checks confirm that HLD has one active entry point and that global specs agree on output boundaries.

## Data Flow

The authoritative HLD topology flows from the refactor plan and design task package into both global specs. The legacy writer receives only a compatibility warning and redirect. No PRD, HLD, LLD, or writing legacy artifact becomes a frozen input.

## Interface Contracts

The harness spec must name `novel-hld-workflow`, twelve independent skills, artifact DAG, entry gate, optional HLD human review state machine, Source Map closure, and convergence protocol. The creation workflow spec must define HLD as world-system support for PRD trunk scenes, not as a key-scene outline.

## State And Persistence

All changes are Markdown skill/spec updates. The updated files are the two global specs and `engine/skills/novel-hld-writer/SKILL.md`. The migration state is captured by validator tests and revision tables where present.

## Error Handling And Diagnostics

If any global spec still asserts nine HLD skills, a monolithic HLD writer, or HLD as key-scene outline, validation fails. If the legacy writer can still be used as the active HLD entry point, validation fails.

## Security And Permissions

Do not implement code. Do not alter PRD/proposal story facts. Do not delete legacy material; demote it and route users to the active workflow.

## Observability

Search-based validator checks confirm the active HLD entry, skill count, artifact names, and legacy warning. Review output cites exact files and lines.

## Verification

Verification uses `scripts/validate_design_tasks.py`, planned HLD contract tests, and targeted text checks for the two global specs plus legacy writer.

## Task Acceptance Mapping

| Planned acceptance item | Design response |
|---|---|
| two global specs are covered | The migration explicitly updates `engine/docs/superpowers/specs/2026-07-05-novel-harness-workflows-and-skills-design.md` and `engine/docs/superpowers/specs/2026-07-05-novel-creation-workflow-design.md`. |
| legacy writer is covered | The migration explicitly downgrades `engine/skills/novel-hld-writer/SKILL.md` into a legacy pointer rather than leaving it as an active HLD authority. |
| single HLD authority is preserved | The target state leaves `novel-hld-workflow` as the only active HLD entry point and rejects monolithic writer or key-scene HLD authority. |

## Global Spec Migration Matrix

| File | Current risk | Required migration | Verification |
|---|---|---|---|
| `engine/docs/superpowers/specs/2026-07-05-novel-harness-workflows-and-skills-design.md` | May retain old HLD skill count or unclear harness authority. | Replace HLD node definition with entry gate, 12 artifacts, Source Map, risk verdict, and convergence protocol. | Search rejects old 9-skill/key-scene HLD authority and confirms artifact 01-12 ownership. |
| `engine/docs/superpowers/specs/2026-07-05-novel-creation-workflow-design.md` | May describe HLD as direct world-building rather than artifact expansion. | Define HLD as PRD-bound world-structure expansion whose business work is delegated to independent skills. | Contract validator confirms HLD entry gate and PRD freeze preservation. |
| `engine/skills/novel-hld-writer/SKILL.md` | Legacy skill may remain an active authoring entry. | Mark as legacy compatibility shim that refuses active HLD generation and redirects to `novel-hld-workflow`. | Regression checks active workflow entry list has one HLD authority. |

## Legacy Writer Downgrade Contract

| Rule | Required behavior |
|---|---|
| Invocation while PRD is blocked | Return blocked guidance and point to PRD human review requirement. |
| Invocation after PRD passes | Redirect to `novel-hld-workflow`; do not generate HLD artifacts directly. |
| Existing legacy docs | May be cited only as legacy reference, never as frozen fact source. |
| Skill description | Must state that active HLD authority is the harness plus independent skills. |

## Stale Authority Detection Matrix

| Stale pattern | Why it is unsafe | Required validator response |
|---|---|---|
| `novel-hld-writer` as active entry | Reintroduces monolithic HLD business generation. | Fail with active-authority conflict. |
| Nine-skill HLD topology | Omits reconciler, integrator, or integrity checker obligations. | Fail with topology mismatch. |
| HLD key-scene design authority | Collapses PRD and HLD boundaries. | Fail with obsolete node definition. |
| Final HLD without Source Map | Allows unsupported or rewritten facts. | Fail final schema coverage. |

## Risks

The main risk is split authority. The mitigation is to make the two global specs and the active skill entry point agree on the same harness and artifact topology.

## Handoff

The developer receives exact files to update, terms that must be present, stale claims that must disappear, and validation commands to run.
