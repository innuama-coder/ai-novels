# Claude Task Instructions: TASK-004

Claude must follow these instructions when working on this single task fixture from the novel workflow engineering design plan. Domain task alias: `DP-HLD-004`.

## Role

You are a senior workflow-design collaborator assigned to `TASK-004`: `HLD blocked/pass fixture and acceptance design`. Use PRD/HLD under `docs/`, planning JSON under `tasks/design/design-planning.json`, the overall design record under `docs/design/rust-implementation-design.md`, and this fixture directory as the source of truth.

Your only deliverable is the named detailed design document: `docs/design/DP-HLD-004-fixtures-acceptance-design.md`. Do not implement code.

## Fixed Input And Output Paths

- Input planning JSON: `tasks/design/design-planning.json`
- Input task fixture: `tasks/design/fixtures/TASK-004/`
- Input spec: `tasks/design/fixtures/TASK-004/spec.yaml`
- Output detailed design document: `docs/design/DP-HLD-004-fixtures-acceptance-design.md`
- Required output root for any design document: `docs/design/`

## Required Reading

Before writing the detailed design document:

1. Read relevant PRD/HLD source refs: `docs/superpowers/runs/prd/2026-07-07-duanxian-prd-workflow/artifacts/09-prd-risk-report.md`, `tasks/design/hld/2026-07-07-duanxian-hld-design-planning/design-task-package.md`.
2. Read `tasks/design/design-planning.json`.
3. Read `docs/design/rust-implementation-design.md`.
4. Read `tasks/design/fixtures/TASK-004/PROMPT.md`, `AGENTS.md`, and `spec.yaml`.
5. Inspect repository files only as read-only context when needed to verify local workflow conventions.

## Detailed Design Checklist

Because this is not a Rust crate, apply the Rust detailed-design checklist by analogy: specify file/module ownership, structured document schemas, callable validator interfaces, data contracts, error diagnostics, state/persistence files, deterministic behavior, observability, and verification commands. Mark Rust-only concerns as not applicable with a reason instead of inventing a Rust stack.

## Task Boundary Rules

- Stay inside `TASK-004` / `DP-HLD-004`.
- Allowed scope: design blocked fixture, design pass fixture, design acceptance evidence.
- Forbidden scope: implementation code, actual HLD business run, PRD review bypass.
- Do not write HLD business content, PRD rewrites, prose, or implementation code.
- Do not modify production source files, tests, build manifests, schemas, migrations, runtime scripts, or generated runtime artifacts.
- If a gap appears, state the blocker in the design document and request or make a design-document/planning update before continuing.

## Consistency With AGENTS.md

Follow `AGENTS.md` in this fixture. If these instructions and `AGENTS.md` differ, preserve the stricter boundary and record the mismatch in the handoff.

## Final Response

Summarize the task ID addressed, domain task ID, detailed design document path, review checks performed, and remaining design risks. Do not report implementation files because this task must not change them.
