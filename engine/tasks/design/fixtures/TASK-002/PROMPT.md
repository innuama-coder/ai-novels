# Detailed Design Task Prompt: TASK-002 HLD harness and independent skills design

This fixture file is the spec-executor 2.0 `PROMPT.md` for domain task `DP-HLD-002`.

You are working on a single documentation-only detailed design task for the novel workflow engineering plan. The repository is a Markdown/Python workflow repository, so Rust-specific design expectations are adapted to explicit module/file boundaries, data contracts, validator functions, error diagnostics, state files, and verification commands.

Do not implement code. Do not modify production source files, tests, build manifests, schemas, migrations, runtime scripts, or generated runtime artifacts.

## Mission

Complete only `TASK-002` / `DP-HLD-002`: `HLD harness and independent skills design`.

Your only deliverable is the detailed design document named below:

- `docs/design/DP-HLD-002-harness-skills-design.md`

## Read First

- PRD/HLD refs: `engine/docs/superpowers/plans/2026-07-07-novel-hld-workflow-refactor.md`, `design/design-tasks/2026-07-07-duanxian-hld-design-planning/design-task-package.md`
- Planning JSON: `tasks/design/design-planning.json`
- Overall design record: `docs/design/rust-implementation-design.md`
- Task fixture: `tasks/design/fixtures/TASK-002/`
- spec-executor task spec: `tasks/design/fixtures/TASK-002/spec.yaml`
- quality validator: `tasks/design/validate_design_doc_quality.py`

## Scope

Allowed scope:

- design pure harness
- design twelve independent skill contracts
- design artifact DAG

Forbidden scope:

- implementation code
- business HLD content
- monolithic HLD writer authority

## Expected Outputs

- docs/design/DP-HLD-002-harness-skills-design.md

The document must be saved exactly at `docs/design/DP-HLD-002-harness-skills-design.md`. Any additional detailed design document created or updated while completing this task must also be saved under `docs/design/`.

## Document Review Checks

- tasks/design/validate_design_doc_quality.py with design-planning.json

The document must explicitly cover source refs, scope boundary, control flow, data flow, interface/type contracts, state and persistence, error handling and diagnostics, security and permissions, observability, verification, risks, and handoff. It must address these acceptance items:

- harness writes no business facts
- each skill owns one artifact
- blocked PRD gate is preserved

## Stop Conditions

- skill ownership conflict
- harness business leakage

Stop instead of continuing if the task would require HLD business artifact generation, PRD fact rewriting, or implementation changes outside a design document.

## Handoff Expectations

Report the detailed design document path, task ID, domain task ID, review checks performed, unresolved design risks, and any design mismatch that requires updating `tasks/design/design-planning.json` or `docs/design/`. Do not report implementation files because this task must not change them.
