# Detailed Design Task Prompt: TASK-005 Final design acceptance review

This fixture file is the spec-executor 2.0 `PROMPT.md` for domain task `DP-HLD-ACCEPT`.

You are working on a single documentation-only detailed design task for the novel workflow engineering plan. The repository is a Markdown/Python workflow repository, so Rust-specific design expectations are adapted to explicit module/file boundaries, data contracts, validator functions, error diagnostics, state files, and verification commands.

Do not implement code. Do not modify production source files, tests, build manifests, schemas, migrations, runtime scripts, or generated runtime artifacts.

## Mission

Complete only `TASK-005` / `DP-HLD-ACCEPT`: `Final design acceptance review`.

Your only deliverable is the detailed design document named below:

- `docs/design/DP-HLD-ACCEPT-design-acceptance-review.md`

## Read First

- PRD/HLD refs: `tasks/design/design-planning.json`, `docs/design/rust-implementation-design.md`
- Planning JSON: `tasks/design/design-planning.json`
- Overall design record: `docs/design/rust-implementation-design.md`
- Dependency design documents and fixtures:
  - `TASK-001 -> DP-HLD-001`: `docs/design/DP-HLD-001-contract-validator-design.md`; fixture `tasks/design/fixtures/TASK-001`
  - `TASK-002 -> DP-HLD-002`: `docs/design/DP-HLD-002-harness-skills-design.md`; fixture `tasks/design/fixtures/TASK-002`
  - `TASK-003 -> DP-HLD-003`: `docs/design/DP-HLD-003-global-spec-migration-design.md`; fixture `tasks/design/fixtures/TASK-003`
  - `TASK-004 -> DP-HLD-004`: `docs/design/DP-HLD-004-fixtures-acceptance-design.md`; fixture `tasks/design/fixtures/TASK-004`
- Task fixture: `tasks/design/fixtures/TASK-005/`
- spec-executor task spec: `tasks/design/fixtures/TASK-005/spec.yaml`
- quality validator: `tasks/design/validate_design_doc_quality.py`

## Scope

Allowed scope:

- review traceability
- review DAG
- review fixtures
- review verification

Forbidden scope:

- implementation code
- HLD business artifact generation
- PRD fact rewrite

## Expected Outputs

- docs/design/DP-HLD-ACCEPT-design-acceptance-review.md

The document must be saved exactly at `docs/design/DP-HLD-ACCEPT-design-acceptance-review.md`. Any additional detailed design document created or updated while completing this task must also be saved under `docs/design/`.

## Document Review Checks

- tasks/design/validate_design_doc_quality.py with --acceptance

The document must explicitly cover source refs, scope boundary, control flow, data flow, interface/type contracts, state and persistence, error handling and diagnostics, security and permissions, observability, verification, risks, and handoff. It must address these acceptance items:

- every detailed task is reviewed
- fixture readiness is checked
- no-code boundary is preserved

It must include an `Acceptance Dependency Mapping` table that maps each dependency as `TASK-* -> DP-HLD-*`, and names the exact dependency design document and fixture directory.

## Stop Conditions

- missing detailed design document
- missing fixture
- unresolved P0/P1 planning defect

Stop instead of continuing if the task would require HLD business artifact generation, PRD fact rewriting, or implementation changes outside a design document.

## Handoff Expectations

Report the detailed design document path, task ID, domain task ID, review checks performed, unresolved design risks, and any design mismatch that requires updating `tasks/design/design-planning.json` or `docs/design/`. Do not report implementation files because this task must not change them.
