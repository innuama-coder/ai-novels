---
name: novel-intake-boundary-ledger-builder
description: Use when a novel proposal task needs the intake brief converted into enforceable constraints and open-question boundaries.
---

# novel-intake-boundary-ledger-builder

## Responsibility

Convert the intake brief into a boundary ledger and readiness verdict for proposal work.

## Input

- Intake brief path and version
- Original idea
- `KEEP-*`, `AVOID-*`, `CONFLICT-*`, reference objects, `OPEN-*`
- Confirmation and handoff status

## Output

Produce a boundary ledger:

| Field | Meaning |
|---|---|
| Intake source | Path, version, status |
| Frozen constraints | `KEEP-*` and `AVOID-*` copied verbatim |
| Conflict seeds | `CONFLICT-*` copied verbatim and marked as proposal story drivers |
| Reference rules | What may be borrowed and what must be avoided |
| Open questions | `OPEN-*` items proposal must answer |
| Non-frozen material | Notes, drafts, old PRD/HLD/LLD/writing not binding |
| Readiness verdict | `pass` or `reopen_intake` |
| Gate result | `pass` only when readiness verdict is `pass`; otherwise `blocked` |
| Readiness evidence | The exact intake rows proving original idea, hard boundary, human motive seed, and external pressure or suspense seed |
| Reopen triggers | Missing or contradictory intake items |

## Rules

- Copy frozen constraints exactly; do not paraphrase into stronger or weaker claims.
- Copy conflict seeds exactly; do not replace human motives with abstract themes.
- Mark all non-intake material as optional reference, never as boundary.
- If an `OPEN-*` item is direction-critical, require proposal to answer it.
- If conflict seeds are missing, create a reopen request instead of letting proposal invent the central conflict.
- `ready_with_open_questions` may defer refinements, but must not defer the existence of a human motive seed plus at least one external pressure or suspense seed.
- Do not expand, interpret, or improve weak conflict material. Judge only whether the intake contains enough explicit seed material for proposal to design from.
- Return `reopen_intake` if the intake lacks original idea, hard boundary, human motive seed, or both external pressure and suspense seed.

## Boundary

- Do not design story content, reader promise, core concept, roles, world premise, or ending.
- Do not repair an under-specified intake by inventing conflict seeds.
- Do not turn old PRD/HLD/LLD/writing material into intake constraints.
- Do not decide whether a future storyline is good; only decide whether proposal has enough explicit seed material to start.

## References

Good boundary ledger:

- Lets every downstream proposal skill see what is frozen, what is open, and what is non-binding.
- Preserves the user's words for `KEEP-*`, `AVOID-*`, `CONFLICT-*`, and `OPEN-*`.
- Names the exact evidence for readiness instead of inferring hidden intent.
- Keeps later-stage drafts out of the boundary.

Bad boundary ledger:

- Paraphrases constraints into stronger or weaker claims.
- Turns notes, old drafts, or proposal decisions into intake facts.
- Says readiness passes without citing human motive and pressure/suspense seeds.

## Traceability

Every ledger row must trace to the intake brief path/version or be marked as a reopen trigger. No row may trace to proposal invention.

## Acceptance

The ledger passes only if every proposal skill can tell what it must obey, what story pressure it must develop, what it may decide, what it must not import from later-stage drafts, and whether proposal may proceed or must reopen intake.
