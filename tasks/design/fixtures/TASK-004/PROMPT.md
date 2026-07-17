# Detailed Design Task Prompt: TASK-004 HLD blocked/pass fixture and acceptance design

This fixture file is the spec-executor 2.0 `PROMPT.md` for domain task `DP-HLD-004`.

You are working on a single documentation-only detailed design task for the novel workflow engineering plan. The repository is a Markdown/Python workflow repository, so Rust-specific design expectations are adapted to explicit module/file boundaries, data contracts, validator functions, error diagnostics, state files, and verification commands.

Do not implement code. Do not modify production source files, tests, build manifests, schemas, migrations, runtime scripts, or generated runtime artifacts.

## Mission

Complete only `TASK-004` / `DP-HLD-004`: `HLD blocked/pass fixture and acceptance design`.

Your only deliverable is the detailed design document named below:

- `docs/design/DP-HLD-004-fixtures-acceptance-design.md`

## Read First

- PRD/HLD refs: `docs/superpowers/runs/prd/2026-07-07-duanxian-prd-workflow/artifacts/09-prd-risk-report.md`, `tasks/design/hld/2026-07-07-duanxian-hld-design-planning/design-task-package.md`
- Planning JSON: `tasks/design/design-planning.json`
- Overall design record: `docs/design/rust-implementation-design.md`
- Task fixture: `tasks/design/fixtures/TASK-004/`
- spec-executor task spec: `tasks/design/fixtures/TASK-004/spec.yaml`
- quality validator: `tasks/design/validate_design_doc_quality.py`

## Scope

Allowed scope:

- design blocked fixture
- design pass fixture
- design acceptance evidence

Forbidden scope:

- implementation code
- actual HLD business run
- PRD review bypass

## Expected Outputs

- docs/design/DP-HLD-004-fixtures-acceptance-design.md

The document must be saved exactly at `docs/design/DP-HLD-004-fixtures-acceptance-design.md`. Any additional detailed design document created or updated while completing this task must also be saved under `docs/design/`.

## Document Review Checks

- tasks/design/validate_design_doc_quality.py with design-planning.json

The document must explicitly cover source refs, scope boundary, control flow, data flow, interface/type contracts, state and persistence, error handling and diagnostics, security and permissions, observability, verification, risks, and handoff. It must address these acceptance items:

- blocked fixture cannot produce business artifacts
- pass fixture requires artifact 01-12
- P0/P1 blocks LLD entry

## Stop Conditions

- fixture requires invented HLD facts

Stop instead of continuing if the task would require HLD business artifact generation, PRD fact rewriting, or implementation changes outside a design document.

## Handoff Expectations

Report the detailed design document path, task ID, domain task ID, review checks performed, unresolved design risks, and any design mismatch that requires updating `tasks/design/design-planning.json` or `docs/design/`. Do not report implementation files because this task must not change them.
