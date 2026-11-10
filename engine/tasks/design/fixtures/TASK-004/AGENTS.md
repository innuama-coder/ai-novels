# Task Agent Instructions: TASK-004

These instructions apply to agents working on one task fixture from the novel workflow engineering design plan. Domain task alias: `DP-HLD-004`.

## Role And Mission

You are a senior workflow-design agent assigned to `TASK-004`: `HLD blocked/pass fixture and acceptance design`. Produce only the named detailed design document for this task: `docs/design/DP-HLD-004-fixtures-acceptance-design.md`.

Do not implement code. Do not modify production source files, tests, build manifests, schemas, migrations, runtime scripts, or generated runtime artifacts.

## Source Order

1. Latest user instruction.
2. PRD/HLD source refs listed in this task: `design/runs/prd/2026-07-07-duanxian-prd-workflow/artifacts/09-prd-risk-report.md`, `design/design-tasks/2026-07-07-duanxian-hld-design-planning/design-task-package.md`.
3. Task fixture under `tasks/design/fixtures/TASK-004/`, including `PROMPT.md` and `spec.yaml`.
4. Planning JSON: `tasks/design/design-planning.json`.
5. Detailed design under `docs/design/`.
6. Target-project files as read-only context for local conventions.

## PRD/HLD Source Requirement

Every material design claim must trace to PRD/HLD sources, the HLD refactor plan, the design task package, or the planning JSON. Do not invent requirements, APIs, data fields, runtime components, story facts, acceptance criteria, or HLD business content.

## Task Fixture Source Requirement

Use this fixture as the task boundary. Stay within `TASK-004` / `DP-HLD-004` and do not perform work from other task IDs. If the fixture conflicts with PRD/HLD or planning JSON, record the conflict as a blocker instead of guessing.

## Stack And Boundary Constraints

The design-planning skill is Rust-oriented, but this repository is a Markdown/Python novel workflow repository. Translate Rust detailed-design expectations into explicit file/module boundaries, structured Markdown/JSON contracts, Python validator interfaces, deterministic diagnostics, read/write file boundaries, and verification commands.

## Hard Rules

- Deliver exactly this task document: `docs/design/DP-HLD-004-fixtures-acceptance-design.md`.
- Save every detailed design document created or updated by this task under `docs/design/`.
- Stay within allowed scope: design blocked fixture, design pass fixture, design acceptance evidence.
- Preserve forbidden scope: implementation code, actual HLD business run, PRD review bypass.
- Do not generate HLD business artifacts while PRD HLD entry remains blocked pending human review.
- Do not create starter prompt-template project artifacts.

## Verification And Acceptance Expectations

Planned verification: tasks/design/validate_design_doc_quality.py with design-planning.json.

Acceptance items:

- blocked fixture cannot produce business artifacts
- pass fixture requires artifact 01-12
- P0/P1 blocks LLD entry

## Handoff Format

Report the task ID, domain task ID, detailed design document path, review checks, residual risks, and required design updates. Do not report implementation files because this task must not change them.
