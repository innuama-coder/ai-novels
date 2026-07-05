---
name: novel-proposal-workflow
description: Use when an accepted or reviewable novel intake brief must become a proposal document before PRD work begins.
---

# novel-proposal-workflow

## Role

This is the proposal node harness. It orchestrates independent proposal skills and packages their outputs into a proposal document. It must not invent story content itself.

## Hard Boundary

The intake brief is the highest constraint for proposal. Proposal may expand open questions into design decisions, but must not rewrite the intake idea, `KEEP-*`, `AVOID-*`, reference usage, or confirmation status.

If the intake brief is `not_ready`, stop and return to intake. If it is `ready_with_open_questions`, proposal may proceed only by answering `OPEN-*` items explicitly.

## Harness Flow

| Step | Harness Action | Business Owner |
|---|---|---|
| 1 | Validate intake status and source path | harness |
| 2 | Build the intake boundary ledger | `novel-intake-boundary-ledger-builder` |
| 3 | Dispatch proposal design skills with the ledger attached | harness |
| 4 | Reject any skill output that violates `KEEP-*` or `AVOID-*` | harness |
| 5 | Dispatch integration and risk checking | `novel-proposal-integrator`, `novel-proposal-risk-checker` |
| 6 | Package proposal, traceability, risks, and PRD handoff | harness |

## Dispatch Order

1. `novel-intake-boundary-ledger-builder`
2. `novel-reader-promise-designer`
3. `novel-core-concept-designer`
4. `novel-macro-structure-designer`
5. `novel-storyline-designer`
6. `novel-core-character-framer`
7. `novel-world-premise-framer`
8. `novel-ending-direction-designer`
9. `novel-proposal-integrator`
10. `novel-proposal-risk-checker`

Parallelize steps 2-8 only after the boundary ledger exists.

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
| Proposal document | integrator skill |
| Constraint traceability | every proposal skill |
| Answered `OPEN-*` items | relevant design skills |
| Frozen proposal items | integrator skill |
| PRD suggested scope | integrator skill |
| Risk report | risk checker |

## Acceptance Gate

Reject the proposal if:

- Any `KEEP-*` is missing or weakened.
- Any `AVOID-*` is violated.
- Any `OPEN-*` is silently ignored or answered without traceability.
- Optional intake fields are backfilled as if user-confirmed.
- The proposal includes trunk scenes, chapter plan, full world bible, character dossier, or prose.
