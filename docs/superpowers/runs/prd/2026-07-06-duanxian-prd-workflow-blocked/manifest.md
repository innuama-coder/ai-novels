# PRD workflow artifact run

Run id: `2026-07-06-duanxian-prd-workflow-blocked`

Harness: `novel-prd-workflow`

Producer: Codex, using repository PRD workflow contract.

Input proposal: `docs/superpowers/specs/2026-07-05-duanxian-proposal.md`

Upstream proposal Risk Report: `docs/superpowers/runs/proposal/2026-07-05-duanxian-proposal-workflow/artifacts/14-proposal-risk-checker.md`

Execution status: blocked before PRD business dispatch.

Blocking verdict: `blocked_pending_human_confirmation`

Business artifacts generated: none. PRD scope, trunk scenes, freeze boundaries, HLD requirements, integration, and risk checking were not dispatched.

## Convergence log

| Stable issue id | Root cause | Fix hypothesis | Regression proof | Attempt count | Versioned refactor trigger |
|---|---|---|---|---|---|
| PRD-BLOCKED-UPSTREAM-CONFIRMATION | Upstream proposal Risk Report has `PRD entry verdict = blocked_pending_human_confirmation`, so PRD cannot legally start. | Do not dispatch PRD business skills until human/intake confirmation changes the upstream proposal verdict to `pass_to_prd`. | `scripts/validate_prd_contract.py` validates this blocked run against the upstream proposal risk report. | 1 | If this remains after three confirmation attempts, reopen proposal/intake acceptance rather than patching PRD. |
