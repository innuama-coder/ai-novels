---
name: novel-proposal-workflow
description: Use when an accepted or reviewable novel intake brief must become a proposal document before PRD work begins.
---

# novel-proposal-workflow

## Role

This is the proposal node harness. It orchestrates independent proposal skills and packages their outputs into a proposal document. It must not invent story content itself.

## Hard Boundary

The intake brief is the highest constraint for proposal. Proposal may expand open questions into design decisions, but must not rewrite the intake idea, `KEEP-*`, `AVOID-*`, `CONFLICT-*`, reference usage, or confirmation status.

The harness may validate the intake source path and declared status, but the business readiness judgment belongs to `novel-intake-boundary-ledger-builder`. If that skill returns `reopen_intake` or a blocked gate result, stop and return to intake. If it returns `pass` for a `ready_with_open_questions` intake, proposal may proceed only by answering `OPEN-*` items explicitly.

## Harness Flow

| Step | Harness Action | Business Owner |
|---|---|---|
| 1 | Validate intake source path and declared status | harness |
| 2 | Build the intake boundary ledger and readiness verdict | `novel-intake-boundary-ledger-builder` |
| 3 | Dispatch pre-story reader promise and core concept hypotheses with the ledger attached | `novel-reader-promise-designer`, `novel-core-concept-designer` |
| 4 | Dispatch storyline design, then evaluate storyline quality against references | `novel-storyline-designer`, `novel-storyline-quality-evaluator` |
| 5 | Dispatch final reader promise and final core concept using the accepted storyline | `novel-reader-promise-designer`, `novel-core-concept-designer` |
| 6 | Dispatch final promise/concept consistency checking | `novel-final-promise-concept-consistency-checker` |
| 7 | Dispatch macro, character, world, and ending skills using the accepted storyline plus final promise/concept | `novel-macro-structure-designer`, `novel-core-character-framer`, `novel-world-premise-framer`, `novel-ending-direction-designer` |
| 8 | Dispatch integration after all upstream business outputs are accepted | `novel-proposal-integrator` |
| 9 | Dispatch final risk checking after Integration Verdict exists | `novel-proposal-risk-checker` |
| 10 | Route integrator/risk verdicts, then package proposal, traceability, storyline quality report, gate verdicts, risks, and PRD handoff | harness |

## Dispatch Order

1. `novel-intake-boundary-ledger-builder`
2. `novel-reader-promise-designer` and `novel-core-concept-designer` in `pre_story_hypothesis` mode
3. `novel-storyline-designer`
4. `novel-storyline-quality-evaluator`
5. `novel-reader-promise-designer` in `final_promise` mode and `novel-core-concept-designer` in `final_concept` mode
6. `novel-final-promise-concept-consistency-checker`
7. `novel-macro-structure-designer`, `novel-core-character-framer`, `novel-world-premise-framer`, and `novel-ending-direction-designer`
8. `novel-proposal-integrator`
9. `novel-proposal-risk-checker`

Pre-story reader promise and core concept may run in parallel only after the boundary ledger readiness verdict is `pass`. They are hypotheses to help storyline design, not frozen proposal content. Step 5 may run in parallel only after the storyline quality evaluator has accepted the complete story synopsis and main story chain with reference evidence. Expansion may run only after final reader promise and final core concept are complete and `novel-final-promise-concept-consistency-checker` returns `pass`. Integration and risk checking must not run before every upstream business output is either accepted or explicitly reopened.

## Retry and Reopen Policy

| Failure | Harness action |
|---|---|
| Boundary ledger readiness verdict is `reopen_intake` or gate result is `blocked` | Stop and use the ledger's reopen request |
| A business skill reports that its own output cannot satisfy `KEEP-*`, `AVOID-*`, `CONFLICT-*`, or accepted storyline constraints | Rerun only the reporting skill with its own violation report attached |
| Storyline quality evaluator returns `revise_storyline` | Rerun `novel-storyline-designer`; do not dispatch finalization or expansion skills |
| Storyline quality evaluator returns `reopen_intake` | Stop proposal and create an intake reopen request |
| Storyline quality report lacks reference evidence for the good-story judgment | Reject the report and rerun `novel-storyline-quality-evaluator`; do not dispatch finalization or expansion skills |
| Final promise/concept consistency report returns `revise_final_promise`, `revise_final_concept`, `revise_both`, or `reopen_storyline` | Follow the report verdict; rerun the named finalization skill output or reopen storyline |
| Final promise/concept consistency report is missing | Stop expansion and dispatch `novel-final-promise-concept-consistency-checker` |
| Integrator reports a missing source, untraceable content, or cross-output inconsistency | Rerun the named source skill or reopen the named upstream artifact; integrator must not invent the content |
| Risk checker reports unresolved P0 or P1 | Do not mark agent quality accepted; rerun the responsible skill or reopen intake according to the risk report |
| Risk checker returns PRD entry `blocked_pending_human_confirmation` | Package as reviewable proposal only; do not freeze for PRD |

## Convergence Protocol

Every retry caused by a P0/P1 finding must be recorded by the harness before rerun. The harness records routing facts only; it must not decide the business fix.

| Field | Requirement |
|---|---|
| Stable issue id | Keep the same id across review/fix/review cycles for the same defect |
| Root cause | Quote the independent checker's root-cause statement or mark missing root cause as a rerun blocker |
| Fix hypothesis | Name the skill output expected to change and why that skill owns the fix |
| Regression proof | Name the validator, artifact row, or independent report that must fail before the fix and pass after the fix |
| Attempt count | Increment for the same Stable issue id whenever a rerun does not remove the P0/P1 |
| Versioned refactor trigger | If the same P0/P1 remains after three attempts, stop targeted reruns and propose a new workflow/skill-contract version instead of another patch |

The harness may dispatch the next retry only when Stable issue id, Root cause, Fix hypothesis, and Regression proof are present. If any field is missing, route back to the checker or integrator that reported the issue.

## Forbidden

- Do not write logline, structure, storylines, roles, world premise, or ending directly.
- Do not treat old PRD/HLD/LLD/writing docs as intake constraints.
- Do not turn design decisions into "user confirmed" facts.
- Do not write PRD trunk scenes, HLD world bible, LLD details, or prose.

## Output Package

The packaged proposal must include:

| Section | Source |
|---|---|
| Intake boundary ledger | boundary ledger skill |
| Intake readiness verdict | boundary ledger skill |
| Proposal document | integrator skill |
| Constraint traceability | every proposal skill |
| Answered `OPEN-*` items | relevant design skills |
| Developed `CONFLICT-*` seeds | relevant design skills |
| Complete story synopsis | `novel-storyline-designer` |
| Critical business claims | `novel-storyline-designer` |
| Storyline quality report | `novel-storyline-quality-evaluator` |
| Focal character and POV rule | `novel-storyline-designer` |
| Main story chain | `novel-storyline-designer` |
| Final reader promise | `novel-reader-promise-designer` in `final_promise` mode |
| Final core concept | `novel-core-concept-designer` in `final_concept` mode |
| Final promise/concept consistency report | `novel-final-promise-concept-consistency-checker` |
| Integration Verdict | `novel-proposal-integrator` |
| Claim Source Map | `novel-proposal-integrator` |
| Frozen proposal items | integrator skill |
| PRD suggested scope | integrator skill |
| Gate verdicts | risk checker |
| Risk report | risk checker |

## Routing Gate

The harness may package a proposal only by checking the presence and routing status of independent skill outputs. It must not independently judge story quality, conflict quality, character motive, promise/concept consistency, or PRD readiness.

Reject packaging or route a rerun only when an independent output says so:

- Boundary ledger readiness verdict is missing or not `pass`.
- Storyline quality report is missing, lacks reference evidence, or returns a non-pass verdict.
- Final promise/concept consistency report is missing or returns a non-pass verdict.
- Integrator reports a missing source, untraceable content, unauthorized new business content, or cross-output inconsistency.
- Integrator lacks a Claim Source Map for critical business claims in the final proposal.
- Risk checker reports unresolved P0/P1, non-pass agent quality, `reopen_intake`, or `blocked_revision_required`.
- Human/intake confirmation is pending; package as reviewable only and do not freeze for PRD.
