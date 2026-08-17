# Agent Contract

## Mission

Run a review-gated DAG that turns an author's idea into a complete conception
evidence set: intent, subject, world, characters, causality and narrative
contract. It must remain generic: no current novel, genre or setting is built
into the contracts.

## Roles and boundaries

- The harness owns stage order, evidence locations, exact interview plans,
  return packages, validation gates and human approvals.
- `novel-intent-facilitator` (I0), `novel-subject-designer` (I1),
  `novel-world-interviewer` (I2), `novel-character-interviewer` (I3),
  `novel-causality-architect` (I4), and `novel-narrative-contract-designer`
  (I5) own only their creative interviewing and design judgment.
- `novel-interview-integrity-auditor` owns the semantic audit, not the
  deterministic verdict. `validate_session.py` and
  `validate_stage_completion.py` own deterministic structural verdicts.
- `novel-interview-brief-generator` owns only the HTML review brief. It cannot
  promote an unvalidated session. The author owns approval and all value
  choices.

## Operating defaults

Before each interview, announce the exact question total and planned duration,
write versioned `plan.v1.json`, and ask only its planned questions. Record each
question, answer, recap and decision immediately in `events.ndjson`; render the
complete report after every append. A new question or changed budget requires a
new plan revision, an explicit author-approval decision record, and fresh
hash-bound downstream evidence.

This release uses `self_recorded`. A self-recorded log is useful evidence but must never be
described as an event-backed transcript.

## Completion criteria

The harness is complete only when I0–I5 each have a `ready` completion packet,
V1 has passed deterministic and semantic integrity checks, the author has
approved V2's HTML brief, and the resulting hash-bound approval is admissible
as B0 input to the autonomous conception workflow. Every return must be
resolved and recorded with its corrected target completion. D1/R1 are legacy
artifacts and are not completion criteria. A structured `blocked` packet is
completion for a blocked run; pretending a missing answer is confirmed is not.
