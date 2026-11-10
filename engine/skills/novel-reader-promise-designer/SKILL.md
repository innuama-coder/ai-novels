---
name: novel-reader-promise-designer
description: Use when a novel proposal needs a reader promise, genre signal, audience hypothesis, or reading-experience target.
---

# novel-reader-promise-designer

## Responsibility

Design the proposal-level reader promise under the intake boundary ledger. Before the storyline is accepted, produce only a promise hypothesis. After the storyline is accepted, produce the final reader promise.

## Input

- Intake boundary ledger
- Conflict seeds and open questions
- Mode: `pre_story_hypothesis` or `final_promise`
- Accepted storyline and storyline quality report, required only for `final_promise`

## Output

| Field | Requirement |
|---|---|
| Mode | `pre_story_hypothesis` or `final_promise` |
| Genre signal | Derived from intake or marked as proposal design |
| Reader promise | What experience the story offers |
| Audience hypothesis | Who may want this, if not already confirmed |
| Conflict promise | What tension, suspense, or emotional pressure the reader is promised |
| Compatibility status | In `final_promise`, `draft_complete_pending_consistency` until the independent consistency checker passes |
| Compatibility note | In `final_promise`, what the final core concept must support or verify |
| Boundary trace | Which `KEEP-*`, `AVOID-*`, `CONFLICT-*`, and `OPEN-*` items are used |

## Rules

- In `pre_story_hypothesis`, produce orientation only; do not freeze story facts.
- In `final_promise`, derive the reading experience from the accepted storyline.
- Distinguish intake-confirmed facts from proposal design decisions.
- Name the conflict or suspense experience the reader is promised.

## Boundary

- Do not claim the user confirmed a target reader unless intake says so.
- Do not add market positioning that violates the original idea.
- Do not use reference works as copy targets.
- Do not promise a generic theme experience while ignoring intake conflict seeds.
- In `pre_story_hypothesis`, do not freeze genre, target audience, or reading promise beyond intake.
- In `final_promise`, do not contradict the accepted storyline or storyline quality report.
- In `final_promise`, do not define a reading experience that the final core concept cannot support. If the final core concept is not yet available, label the compatibility as `draft_complete_pending_consistency` for `novel-final-promise-concept-consistency-checker`.

## References

Good reader promise:

- Names a concrete reading experience, tension, and emotional pressure.
- Can be delivered by the accepted storyline rather than by genre labels alone.
- Keeps audience/genre assumptions provisional unless intake confirms them.

Bad reader promise:

- Promises a generic theme, mood, or market category without story pressure.
- Sells a different focal pressure, conflict center, or ending than the accepted storyline.
- Treats proposal taste as user-confirmed demand.

## Traceability

Every final promise claim must trace to intake, conflict seeds, open-question answers, or accepted storyline evidence. Compatibility claims must be left to the independent consistency checker.

## Acceptance

The pre-story promise passes only if it helps storyline design without replacing it. The final promise passes only if it guides downstream choices while making clear which parts are intake constraints, conflict seeds, accepted storyline, and proposal design, and can be reconciled with the final core concept before expansion.
