# DP-HLD-004 HLD Fixtures And Acceptance Design

## Source Refs

- `tasks/design/hld/2026-07-07-duanxian-hld-design-planning/design-task-package.md`
- `engine/docs/superpowers/plans/2026-07-07-novel-hld-workflow-refactor.md`
- `duanxian/design/runs/prd/2026-07-07-duanxian-prd-workflow/artifacts/09-prd-risk-report.md`

## Scope Boundary

This task designs blocked/pass HLD workflow fixtures and the acceptance route for HLD workflow implementation. It is documentation-only and does not execute HLD generation. Fixtures may represent expected manifests, reports, and minimal structural artifacts, but must not invent world-system facts.

## Control Flow

The blocked fixture starts from PRD `blocked_pending_human_review` and proves that only a blocked manifest can be produced. The pass fixture starts from a controlled PRD confirmation state and proves that artifact 01-12 are required before packaging. Acceptance runs validators, fixture checks, and risk/verdict consistency checks.

## Data Flow

Fixture inputs include PRD risk verdict, PRD final package, contract JSON, workflow skill, and independent skill files. Fixture outputs are expected manifests, expected error reports, and validator evidence. No business fact flows into blocked-run outputs.

## Interface Contracts

Each fixture has source files, expected outputs, expected validator command, and expected failure or pass condition. The final acceptance task depends on contract, harness, global spec migration, and fixture design tasks.

## State And Persistence

Fixtures live under `duanxian/design/runs/hld/...` or test fixture directories. Acceptance reports live under `docs/design/` when produced by design-planning. Runtime state is not required.

## Error Handling And Diagnostics

If blocked PRD entry produces business artifacts, the fixture fails. If pass-state packaging skips any artifact, Source Map, risk report, or LLD handoff, the fixture fails. If P0/P1 does not block LLD entry, acceptance fails.

## Security And Permissions

Do not implement code. Do not modify source PRD/proposal documents. Do not create final HLD business content while PRD is pending human review.

## Observability

Acceptance output records validator command, fixture id, expected state, actual state, and any failed gate. It also records whether spec-executor task packages are local-only or published.

## Verification

Verification uses design-planning quality checks, `scripts/validate_design_tasks.py`, planned `validate_hld_contract.py`, and planned fixture-specific pytest cases.

## Task Acceptance Mapping

| Planned acceptance item | Design response |
|---|---|
| blocked fixture cannot produce business artifacts | The blocked fixture starts from `blocked_pending_human_review` and accepts only a blocked manifest plus gate report, with no HLD world-system artifacts. |
| pass fixture requires artifact 01-12 | The pass fixture requires artifact 01 through artifact 12 before final packaging and fails if any artifact, Source Map, risk report, or LLD handoff is skipped. |
| P0/P1 blocks LLD entry | Acceptance requires unresolved P0/P1 findings to force `Agent quality verdict = fail` and `LLD entry verdict = blocked_revision_required`. |

## Blocked Fixture Contract

| Fixture field | Required value | Failure caught |
|---|---|---|
| PRD HLD entry verdict | `blocked_pending_human_review` | Workflow bypasses human review. |
| Allowed outputs | Blocked manifest and gate report only | Business artifact appears too early. |
| Artifact index | Empty for artifact 01-12 | Partial HLD generation during blocked state. |
| Verdict | `blocked` or `not_ready_for_hld_business_run` | False readiness claim. |

## Pass Fixture Contract

| Fixture field | Required value | Failure caught |
|---|---|---|
| PRD HLD entry verdict | `pass_to_hld` with human review evidence | Pass state without human approval. |
| Artifact set | Artifact 01 through artifact 12 plus final HLD package | Missing skill output or skipped topology step. |
| Source Map | Every PRD/freeze/story fact has upstream atom and HLD atom | Same-source rewrite or unsupported fact. |
| Risk report | P0/P1 closed or blocking verdict emitted | LLD entry allowed with open blocker. |
| Convergence log | Stable issue id, root cause, fix hypothesis, regression proof, attempt count, rerun target, status | Non-convergent repeated fixes. |

## Acceptance Evidence Matrix

| Evidence | Source | Acceptance use |
|---|---|---|
| Fixture file list | `duanxian/design/runs/hld/...` | Confirms blocked/pass output shape. |
| Validator report | `scripts/validate_hld_contract.py` output | Confirms contract rules are executable. |
| Regression test report | `pytest tests/test_validate_hld_contract.py -q` | Confirms negative fixtures fail for the right reason. |
| Final HLD Source Map | Artifact 11 | Confirms fact-level closure. |
| Risk verdict matrix | Artifact 12 | Confirms P0/P1 and LLD entry verdict consistency. |

## Risks

The main risk is fixture drift from real workflow behavior. The mitigation is to keep fixtures minimal, structural, and validator-backed instead of prose-only.

## Handoff

The developer receives fixture ids, input states, expected outputs, acceptance commands, and stop conditions for unresolved PRD review or unresolved P0/P1 issues.
