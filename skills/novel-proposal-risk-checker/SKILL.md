---
name: novel-proposal-risk-checker
description: Use when a novel proposal needs constraint, completeness, boundary, or PRD-readiness checking.
---

# novel-proposal-risk-checker

## Responsibility

Check whether a proposal obeys the intake boundary and is ready for human review and PRD.

## Output

Produce a risk report:

| Field | Requirement |
|---|---|
| Constraint violations | Missing `KEEP-*`, violated `AVOID-*`, ignored references |
| Open question handling | Each `OPEN-*` answered, deferred, or reopened |
| Boundary risks | PRD/HLD/LLD/prose leakage |
| Completeness risks | Missing proposal sections |
| PRD readiness | Whether PRD can choose a controlled scope |

## Severity

| Level | Meaning |
|---|---|
| P0 | Violates intake boundary or rewrites user idea |
| P1 | Cannot enter PRD safely |
| P2 | Weakness that should be fixed before review |
| P3 | Note or downstream watch item |

## Acceptance

The proposal cannot pass with any unresolved P0 or P1.
