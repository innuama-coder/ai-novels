# Task Agent Instructions: TASK-003

These instructions apply to agents working on one task fixture from the novel workflow engineering design plan. Domain task alias: `DP-HLD-003`.

## Role And Mission

You are a senior workflow-design agent assigned to `TASK-003`: `Global workflow spec and legacy HLD writer migration design`. Produce only the named detailed design document for this task: `docs/design/DP-HLD-003-global-spec-migration-design.md`.

Do not implement code. Do not modify production source files, tests, build manifests, schemas, migrations, runtime scripts, or generated runtime artifacts.

## Source Order

1. Latest user instruction.
2. PRD/HLD source refs listed in this task: `docs/superpowers/plans/2026-07-07-novel-hld-workflow-refactor.md`, `docs/superpowers/specs/2026-07-05-novel-harness-workflows-and-skills-design.md`, `docs/superpowers/specs/2026-07-05-novel-creation-workflow-design.md`, `skills/novel-hld-writer/SKILL.md`.
3. Task fixture under `tasks/design/fixtures/TASK-003/`, including `PROMPT.md` and `spec.yaml`.
4. Planning JSON: `tasks/design/design-planning.json`.
5. Detailed design under `docs/design/`.
6. Target-project files as read-only context for local conventions.

## PRD/HLD Source Requirement

Every material design claim must trace to PRD/HLD sources, the HLD refactor plan, the design task package, or the planning JSON. Do not invent requirements, APIs, data fields, runtime components, story facts, acceptance criteria, or HLD business content.

## Task Fixture Source Requirement

Use this fixture as the task boundary. Stay within `TASK-003` / `DP-HLD-003` and do not perform work from other task IDs. If the fixture conflicts with PRD/HLD or planning JSON, record the conflict as a blocker instead of guessing.

## Stack And Boundary Constraints

The design-planning skill is Rust-oriented, but this repository is a Markdown/Python novel workflow repository. Translate Rust detailed-design expectations into explicit file/module boundaries, structured Markdown/JSON contracts, Python validator interfaces, deterministic diagnostics, read/write file boundaries, and verification commands.

## Hard Rules

- Deliver exactly this task document: `docs/design/DP-HLD-003-global-spec-migration-design.md`.
- Save every detailed design document created or updated by this task under `docs/design/`.
- Stay within allowed scope: design global spec updates, design legacy writer demotion, design stale authority checks.
- Preserve forbidden scope: implementation code, story fact changes, HLD business artifact generation.
- Do not generate HLD business artifacts while PRD HLD entry remains blocked pending human review.
- Do not create starter prompt-template project artifacts.

## Verification And Acceptance Expectations

Planned verification: tasks/design/validate_design_doc_quality.py with design-planning.json.

Acceptance items:

- two global specs are covered
- legacy writer is covered
- single HLD authority is preserved

## Handoff Format

Report the task ID, domain task ID, detailed design document path, review checks, residual risks, and required design updates. Do not report implementation files because this task must not change them.
