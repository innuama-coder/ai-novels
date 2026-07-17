# HLD Workflow Engineering Design Overview

## Source Refs

- `tasks/design/hld/2026-07-07-duanxian-hld-design-planning/design-task-package.md`
- `docs/superpowers/plans/2026-07-07-novel-hld-workflow-refactor.md`
- `docs/superpowers/runs/prd/2026-07-07-duanxian-prd-workflow/artifacts/final-prd-package.md`

## Scope Boundary

This document is the top-level design record required by the design-planning harness. The target repository is a Markdown/Python workflow repository rather than a Rust crate, so Rust crate boundaries are not applicable. The design scope is limited to HLD workflow engineering artifacts: workflow contracts, validators, skill contracts, global workflow specifications, fixtures, and acceptance checks. It does not generate HLD business artifacts such as world rules, character systems, environments, events, threads, style, POV, or final HLD package content.

## Control Flow

The control flow starts with the PRD HLD entry gate. While the PRD risk report states `blocked_pending_human_review`, the HLD workflow may only create planning, contract, validator, skill, and fixture engineering artifacts. After human PRD confirmation, `novel-hld-workflow` may dispatch artifact owners in the fixed topology, collect skill verdicts, send unresolved P0/P1 issues to the convergence log, and package final HLD only from integrator and integrity checker outputs.

## Data Flow

Source data flows from proposal claims, PRD scenes, PRD freeze boundaries, HLD expansion requirements, and story logic boundaries into the HLD contract and support ledgers. The design task package maps those sources to HLD engineering tasks and artifact owners. The design-planning JSON maps the same obligations to executable documentation task packages, and each fixture points to one detailed design document under `docs/design/`.

## Interface Contracts

The key interfaces are Markdown tables, JSON planning records, Python validator functions, and spec-executor 2.0 task fixtures. `validate_design_tasks.py` checks the HLD design task package. `validate_hld_contract.py` is a planned deliverable that will check the implemented HLD workflow, skills, contract, Source Map, risk verdict, and convergence semantics.

## State And Persistence

Persistent state is file based. The canonical planning state is `tasks/design/design-planning.json`. HLD design task state is preserved in `tasks/design/hld/2026-07-07-duanxian-hld-design-planning/`. Future HLD run state must live under `docs/superpowers/runs/hld/...` and must not overwrite PRD or proposal artifacts.

## Error Handling And Diagnostics

Validators must fail closed. Missing source refs, weakened PRD handoff facts, missing HLD topology dependencies, missing fixtures, or unresolved P0/P1 risks must produce explicit diagnostics. The convergence protocol records stable issue id, root cause, fix hypothesis, regression proof, attempt count, rerun target, and status.

## Security And Permissions

The task packages are documentation-only. They must not modify production source, tests, manifests, schemas, migrations, runtime scripts, or generated runtime artifacts unless a later user request explicitly changes the phase. No secrets, external services, or privileged commands are required.

## Observability

Observability is provided by deterministic validator output and task fixture verification commands. The primary checks are `scripts/validate_design_tasks.py`, `tests/test_validate_design_tasks.py`, and the design-planning validator under `/Users/royzuo/.codex/skills/design-planning/validators/validate_design_planning.py`.

## Verification

Verification consists of running the local design task validator, the local tests, PRD/proposal contract regressions, and the design-planning structural validator. Each fixture also includes a `validate_design_doc_quality.py` command for its target design document.

## Risks

The main risk is confusing planning artifacts with HLD business artifacts. The guardrail is explicit planning-only status while PRD human review is pending. Another risk is reintroducing old monolithic HLD writer authority; this is handled by requiring global spec updates and a legacy writer downgrade task.

## Handoff

The handoff is `tasks/design/design-planning.json` plus task fixtures under `tasks/design/fixtures/`. Spec-executor receives one task directory at a time and writes only the exact design document listed in that task's `spec.yaml`.
