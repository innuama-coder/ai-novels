# PRD workflow artifact run

Harness: `novel-prd-workflow`

Execution status: accepted for HLD dispatch after confirmed human PRD review.

Proposal source: `docs/superpowers/runs/proposal/2026-07-05-duanxian-proposal-workflow/artifacts/13-proposal-integrator.md`

Upstream proposal risk report: `docs/superpowers/runs/prd/2026-07-07-duanxian-prd-workflow/artifacts/00-proposal-risk-report-human-confirmed.md`

Final PRD package: `docs/superpowers/runs/prd/2026-07-07-duanxian-prd-workflow/artifacts/final-prd-package.md`

PRD Integration Verdict artifact: `docs/superpowers/runs/prd/2026-07-07-duanxian-prd-workflow/artifacts/08-prd-integrator.md`

PRD Risk Report artifact: `docs/superpowers/runs/prd/2026-07-07-duanxian-prd-workflow/artifacts/09-prd-risk-report.md`

Artifact order:

1. `novel-part-scope-selector`: `artifacts/01-part-scope.md`
2. `novel-part-goal-definer`: `artifacts/02-part-goal.md`
3. `novel-trunk-scene-designer`: `artifacts/03-trunk-scenes.md`
4. `novel-scene-conflict-value-designer`: `artifacts/04-conflict-value.md`
5. `novel-scene-information-flow-designer`: `artifacts/05-information-flow.md`
6. `novel-prd-freeze-boundary-writer`: `artifacts/06-freeze-boundaries.md`
7. `novel-hld-expansion-requirement-writer`: `artifacts/07-hld-expansion-requirements.md`
8. `novel-prd-integrator`: `artifacts/08-prd-integrator.md`
9. `novel-prd-causality-checker`: `artifacts/09-prd-risk-report.md`

## Convergence log

| Stable issue id | Root cause | Fix hypothesis | Regression proof | Attempt count | Versioned refactor trigger |
|---|---|---|---|---|---|
| PRD-RUN-BASELINE | No unresolved P0/P1 in this run; row records baseline validation path. | Package should remain pass unless artifact-level validators find drift. | `python3 scripts/validate_prd_contract.py` validates the run after contract registration. | 1 |  |
| PRD-PRE-EXTRACTION-SETUP | Proposal synopsis contained accident death and last-clue-in-memory facts, but the Claim Source Map and PRD trunk scene chain began at post-death reading, so the failed intelligence handoff scene was not mandatory. | Add CLAIM-10 as a fact-level upstream setup claim; require artifact 03 to include a pre-extraction causal setup scene before post-death memory reading; synchronize artifacts 01-09 and final package. | `test_validate_formal_prd_artifact_texts_requires_pre_extraction_causal_setup` fails without the setup scene and `python3 scripts/validate_prd_contract.py` validates the repaired run. | 1 |  |
| PRD-SCENE-GRANULARITY | Artifact validation required Scene content but did not require scene-level execution units, so a trunk scene could still summarize a whole functional block. | Add PRD-CONTRACT-18, require artifact 03 `Scene execution table`, and make every trunk scene carry at least two units with objective, on-page action, conflict turn, exit state, and proposal trace. | `test_validate_formal_prd_artifact_texts_requires_scene_execution_table` fails without the execution table and `python3 scripts/validate_prd_contract.py` validates the repaired run. | 1 |  |

## PRD package attestation

| Field | Value |
|---|---|
| Run id | 2026-07-07-duanxian-prd-workflow |
| Harness | novel-prd-workflow |
| Package state | accepted |

## Frozen artifact digest manifest

| Artifact id | Registered path | SHA-256 |
|---|---|---|
| upstream-proposal-risk-report | docs/superpowers/runs/prd/2026-07-07-duanxian-prd-workflow/artifacts/00-proposal-risk-report-human-confirmed.md | sha256:00f87f367fb827a0d3faf374ddde6f2541f633c3ddbb1cd731af24cb77c553d7 |
| 01 | docs/superpowers/runs/prd/2026-07-07-duanxian-prd-workflow/artifacts/01-part-scope.md | sha256:d111920340e3e2c4326ab29b02c238b145091588662cf302117fda907c7f5220 |
| 02 | docs/superpowers/runs/prd/2026-07-07-duanxian-prd-workflow/artifacts/02-part-goal.md | sha256:c9107d82865f514eb481cc11a254454f4e541a34dc7f8b4b5af73602ccda491d |
| 03 | docs/superpowers/runs/prd/2026-07-07-duanxian-prd-workflow/artifacts/03-trunk-scenes.md | sha256:43dbe9e09bf500fb2308101e5ef4c41a06b80cc4c2bd095abe39d2151ba02095 |
| 04 | docs/superpowers/runs/prd/2026-07-07-duanxian-prd-workflow/artifacts/04-conflict-value.md | sha256:af15f70ac6495ace1faa2436b5050acef15b0cf85895d6d14db207c9e70a745a |
| 05 | docs/superpowers/runs/prd/2026-07-07-duanxian-prd-workflow/artifacts/05-information-flow.md | sha256:7bdfce8a0b63a3a96c41692fdbe0d082700e341358832e125d5312f65899402a |
| 06 | docs/superpowers/runs/prd/2026-07-07-duanxian-prd-workflow/artifacts/06-freeze-boundaries.md | sha256:fa0ad52221db1519e3486b9686c8bee96cb23abcc880552158550acf5b74d318 |
| 07 | docs/superpowers/runs/prd/2026-07-07-duanxian-prd-workflow/artifacts/07-hld-expansion-requirements.md | sha256:317d1c9d0104c56d0a2d26a6d97ba651d406d2d95253682ca3ada70ac5a7c10c |
| 08 | docs/superpowers/runs/prd/2026-07-07-duanxian-prd-workflow/artifacts/08-prd-integrator.md | sha256:8479f66e7aa776142569cd6cc265b562de33c950b064376e18545f7c7ff91d37 |
| 09 | docs/superpowers/runs/prd/2026-07-07-duanxian-prd-workflow/artifacts/09-prd-risk-report.md | sha256:4cb0e693f7f41ad8d22ebb63846223a77393ded1498a3ac4876738e5023429e7 |
| final-prd-package | docs/superpowers/runs/prd/2026-07-07-duanxian-prd-workflow/artifacts/final-prd-package.md | sha256:5a7a007ddf7033734b606382827a6a52ae0a7034fedf84e1f04b90f8e3cf9c7c |
