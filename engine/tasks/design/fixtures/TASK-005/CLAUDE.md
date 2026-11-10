# Claude Task Instructions: TASK-005

Claude must follow these instructions when working on this single task fixture from the novel workflow engineering design plan. Domain task alias: `DP-HLD-ACCEPT`.

## Role

You are a senior workflow-design collaborator assigned to `TASK-005`: `Final design acceptance review`. Use PRD/HLD under `docs/`, planning JSON under `tasks/design/design-planning.json`, the overall design record under `docs/design/rust-implementation-design.md`, and this fixture directory as the source of truth.

Your only deliverable is the named detailed design document: `docs/design/DP-HLD-ACCEPT-design-acceptance-review.md`. Do not implement code.

## Fixed Input And Output Paths

- Input planning JSON: `tasks/design/design-planning.json`
- Input task fixture: `tasks/design/fixtures/TASK-005/`
- Input spec: `tasks/design/fixtures/TASK-005/spec.yaml`
- Output detailed design document: `docs/design/DP-HLD-ACCEPT-design-acceptance-review.md`
- Required output root for any design document: `docs/design/`

## Required Reading

Before writing the detailed design document:

1. Read relevant PRD/HLD source refs: `tasks/design/design-planning.json`, `docs/design/rust-implementation-design.md`.
2. Read `tasks/design/design-planning.json`.
3. Read `docs/design/rust-implementation-design.md`.
4. Read `tasks/design/fixtures/TASK-005/PROMPT.md`, `AGENTS.md`, and `spec.yaml`.
5. Read every dependency design document and fixture:
   - `TASK-001 -> DP-HLD-001`: `docs/design/DP-HLD-001-contract-validator-design.md`; fixture `tasks/design/fixtures/TASK-001`
   - `TASK-002 -> DP-HLD-002`: `docs/design/DP-HLD-002-harness-skills-design.md`; fixture `tasks/design/fixtures/TASK-002`
   - `TASK-003 -> DP-HLD-003`: `docs/design/DP-HLD-003-global-spec-migration-design.md`; fixture `tasks/design/fixtures/TASK-003`
   - `TASK-004 -> DP-HLD-004`: `docs/design/DP-HLD-004-fixtures-acceptance-design.md`; fixture `tasks/design/fixtures/TASK-004`
6. Inspect repository files only as read-only context when needed to verify local workflow conventions.

## Detailed Design Checklist

Because this is not a Rust crate, apply the Rust detailed-design checklist by analogy: specify file/module ownership, structured document schemas, callable validator interfaces, data contracts, error diagnostics, state/persistence files, deterministic behavior, observability, and verification commands. Mark Rust-only concerns as not applicable with a reason instead of inventing a Rust stack.

## Task Boundary Rules

- Stay inside `TASK-005` / `DP-HLD-ACCEPT`.
- Allowed scope: review traceability, review DAG, review fixtures, review verification.
- Forbidden scope: implementation code, HLD business artifact generation, PRD fact rewrite.
- Do not write HLD business content, PRD rewrites, prose, or implementation code.
- Do not modify production source files, tests, build manifests, schemas, migrations, runtime scripts, or generated runtime artifacts.
- If a gap appears, state the blocker in the design document and request or make a design-document/planning update before continuing.
- The final document must include `Acceptance Dependency Mapping` with each dependency row written as `TASK-* -> DP-HLD-*`, the exact `docs/design/*.md` deliverable, and the exact `tasks/design/fixtures/TASK-*` fixture directory.

## Consistency With AGENTS.md

Follow `AGENTS.md` in this fixture. If these instructions and `AGENTS.md` differ, preserve the stricter boundary and record the mismatch in the handoff.

## Final Response

Summarize the task ID addressed, domain task ID, detailed design document path, review checks performed, and remaining design risks. Do not report implementation files because this task must not change them.
