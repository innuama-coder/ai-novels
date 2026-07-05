---
name: novel-intake-boundary-ledger-builder
description: Use when a novel proposal task needs the intake brief converted into enforceable constraints and open-question boundaries.
---

# novel-intake-boundary-ledger-builder

## Responsibility

Convert the intake brief into a boundary ledger for proposal work.

## Input

- Intake brief path and version
- Original idea
- `KEEP-*`, `AVOID-*`, reference objects, `OPEN-*`
- Confirmation and handoff status

## Output

Produce a boundary ledger:

| Field | Meaning |
|---|---|
| Intake source | Path, version, status |
| Frozen constraints | `KEEP-*` and `AVOID-*` copied verbatim |
| Reference rules | What may be borrowed and what must be avoided |
| Open questions | `OPEN-*` items proposal must answer |
| Non-frozen material | Notes, drafts, old PRD/HLD/LLD/writing not binding |
| Reopen triggers | Missing or contradictory intake items |

## Rules

- Copy frozen constraints exactly; do not paraphrase into stronger or weaker claims.
- Mark all non-intake material as optional reference, never as boundary.
- If an `OPEN-*` item is direction-critical, require proposal to answer it.
- If a needed boundary is absent, create a reopen request instead of inventing it.

## Acceptance

The ledger passes only if every proposal skill can tell what it must obey, what it may decide, and what it must not import from later-stage drafts.
