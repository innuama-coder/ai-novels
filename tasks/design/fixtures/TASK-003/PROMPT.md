# Detailed Design Task Prompt: TASK-003 Global workflow spec and legacy HLD writer migration design

This fixture file is the spec-executor 2.0 `PROMPT.md` for domain task `DP-HLD-003`.

You are working on a single documentation-only detailed design task for the novel workflow engineering plan. The repository is a Markdown/Python workflow repository, so Rust-specific design expectations are adapted to explicit module/file boundaries, data contracts, validator functions, error diagnostics, state files, and verification commands.

Do not implement code. Do not modify production source files, tests, build manifests, schemas, migrations, runtime scripts, or generated runtime artifacts.

## Mission

Complete only `TASK-003` / `DP-HLD-003`: `Global workflow spec and legacy HLD writer migration design`.

Your only deliverable is the detailed design document named below:

- `docs/design/DP-HLD-003-global-spec-migration-design.md`

## Read First

- PRD/HLD refs: `docs/superpowers/plans/2026-07-07-novel-hld-workflow-refactor.md`, `docs/superpowers/specs/2026-07-05-novel-harness-workflows-and-skills-design.md`, `docs/superpowers/specs/2026-07-05-novel-creation-workflow-design.md`, `skills/novel-hld-writer/SKILL.md`
- Planning JSON: `tasks/design/design-planning.json`
- Overall design record: `docs/design/rust-implementation-design.md`
- Task fixture: `tasks/design/fixtures/TASK-003/`
- spec-executor task spec: `tasks/design/fixtures/TASK-003/spec.yaml`
- quality validator: `tasks/design/validate_design_doc_quality.py`

## Scope

Allowed scope:

- design global spec updates
- design legacy writer demotion
- design stale authority checks

Forbidden scope:

- implementation code
- story fact changes
- HLD business artifact generation

## Expected Outputs

- docs/design/DP-HLD-003-global-spec-migration-design.md

The document must be saved exactly at `docs/design/DP-HLD-003-global-spec-migration-design.md`. Any additional detailed design document created or updated while completing this task must also be saved under `docs/design/`.

## Document Review Checks

- tasks/design/validate_design_doc_quality.py with design-planning.json

The document must explicitly cover source refs, scope boundary, control flow, data flow, interface/type contracts, state and persistence, error handling and diagnostics, security and permissions, observability, verification, risks, and handoff. It must address these acceptance items:

- two global specs are covered
- legacy writer is covered
- single HLD authority is preserved

## Stop Conditions

- global specs require unresolved workflow decision

Stop instead of continuing if the task would require HLD business artifact generation, PRD fact rewriting, or implementation changes outside a design document.

## Handoff Expectations

Report the detailed design document path, task ID, domain task ID, review checks performed, unresolved design risks, and any design mismatch that requires updating `tasks/design/design-planning.json` or `docs/design/`. Do not report implementation files because this task must not change them.
