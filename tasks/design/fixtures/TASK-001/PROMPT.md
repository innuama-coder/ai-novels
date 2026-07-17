# Detailed Design Task Prompt: TASK-001 HLD contract and validator design

This fixture file is the spec-executor 2.0 `PROMPT.md` for domain task `DP-HLD-001`.

You are working on a single documentation-only detailed design task for the novel workflow engineering plan. The repository is a Markdown/Python workflow repository, so Rust-specific design expectations are adapted to explicit module/file boundaries, data contracts, validator functions, error diagnostics, state files, and verification commands.

Do not implement code. Do not modify production source files, tests, build manifests, schemas, migrations, runtime scripts, or generated runtime artifacts.

## Mission

Complete only `TASK-001` / `DP-HLD-001`: `HLD contract and validator design`.

Your only deliverable is the detailed design document named below:

- `docs/design/DP-HLD-001-contract-validator-design.md`

## Read First

- PRD/HLD refs: `tasks/design/hld/2026-07-07-duanxian-hld-design-planning/design-task-package.md`, `docs/superpowers/plans/2026-07-07-novel-hld-workflow-refactor.md`
- Planning JSON: `tasks/design/design-planning.json`
- Overall design record: `docs/design/rust-implementation-design.md`
- Task fixture: `tasks/design/fixtures/TASK-001/`
- spec-executor task spec: `tasks/design/fixtures/TASK-001/spec.yaml`
- quality validator: `tasks/design/validate_design_doc_quality.py`

## Scope

Allowed scope:

- design contract JSON
- design validator behavior
- design regression fixture coverage

Forbidden scope:

- implementation code
- HLD business artifact generation
- PRD rewrite

## Expected Outputs

- docs/design/DP-HLD-001-contract-validator-design.md

The document must be saved exactly at `docs/design/DP-HLD-001-contract-validator-design.md`. Any additional detailed design document created or updated while completing this task must also be saved under `docs/design/`.

## Document Review Checks

- tasks/design/validate_design_doc_quality.py with design-planning.json

The document must explicitly cover source refs, scope boundary, control flow, data flow, interface/type contracts, state and persistence, error handling and diagnostics, security and permissions, observability, verification, risks, and handoff. It must address these acceptance items:

- fact-level binding checks are specified
- negative fixtures are specified
- planned validator functions map to contract rules

## Stop Conditions

- missing PRD source
- validator would require business HLD content

Stop instead of continuing if the task would require HLD business artifact generation, PRD fact rewriting, or implementation changes outside a design document.

## Handoff Expectations

Report the detailed design document path, task ID, domain task ID, review checks performed, unresolved design risks, and any design mismatch that requires updating `tasks/design/design-planning.json` or `docs/design/`. Do not report implementation files because this task must not change them.
