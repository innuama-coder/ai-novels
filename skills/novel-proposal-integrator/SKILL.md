---
name: novel-proposal-integrator
description: Use when independent proposal skill outputs need to be assembled into one proposal document.
---

# novel-proposal-integrator

## Responsibility

Integrate proposal skill outputs into one proposal document without adding new business content.

## Output

Proposal document with:

| Section | Source |
|---|---|
| Boundary ledger | `novel-intake-boundary-ledger-builder` |
| Reader promise | `novel-reader-promise-designer` |
| Core concept | `novel-core-concept-designer` |
| Macro structure | `novel-macro-structure-designer` |
| Storylines | `novel-storyline-designer` |
| Core character frame | `novel-core-character-framer` |
| World premise | `novel-world-premise-framer` |
| Ending direction | `novel-ending-direction-designer` |
| PRD handoff | Derived from prior outputs only |

## Boundary

- Do not invent missing logline, roles, structure, world premise, or ending.
- Do not smooth over contradictions; report them.
- Do not promote optional design decisions to intake constraints.

## Acceptance

The integrated proposal passes if every claim can trace to intake or one named proposal skill output.
