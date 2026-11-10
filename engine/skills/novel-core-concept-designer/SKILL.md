---
name: novel-core-concept-designer
description: Use when a novel proposal needs a logline, core question, central hook, or concept card.
---

# novel-core-concept-designer

## Responsibility

Design the proposal-level core concept. Before the storyline is accepted, produce only a concept hypothesis. After the storyline is accepted, produce the final concept card.

## Input

- Intake boundary ledger
- Conflict seeds and open questions
- Mode: `pre_story_hypothesis` or `final_concept`
- Accepted storyline and storyline quality report, required only for `final_concept`

## Output

| Field | Requirement |
|---|---|
| Mode | `pre_story_hypothesis` or `final_concept` |
| Logline | One sentence; focal pressure, conflict, stakes or change. In `pre_story_hypothesis`, label as provisional |
| Core question | The story problem the proposal will explore |
| Hook | What makes this story materially distinct |
| Human motive anchor | The private motive or emotional pressure that makes the concept human |
| Compatibility status | In `final_concept`, `draft_complete_pending_consistency` until the independent consistency checker passes |
| Compatibility note | In `final_concept`, what the final reader promise must honestly deliver or verify |
| Constraint trace | Intake constraints, conflict seeds, and open questions used |

## Rules

- In `pre_story_hypothesis`, produce a provisional concept only.
- In `final_concept`, derive logline, hook, question, and human motive from the accepted storyline.
- Keep the logline one sentence and proposal-level.
- Identify the human motive anchor explicitly.

## Boundary

- Do not rewrite the original idea.
- Do not violate `KEEP-*` or `AVOID-*`.
- Do not turn the logline into a full synopsis.
- When answering an `OPEN-*`, label it as proposal design.
- Do not make the hook depend only on abstract ethics, setting novelty, or grand stakes.
- In `pre_story_hypothesis`, do not freeze focal character, terminal agency, final stakes, or irreversible outcome beyond intake.
- In `final_concept`, do not contradict the accepted storyline or storyline quality report.
- In `final_concept`, do not define a hook or core question that the final reader promise cannot honestly deliver. If the final reader promise is not yet available, label the compatibility as `draft_complete_pending_consistency` for `novel-final-promise-concept-consistency-checker`.

## References

Good core concept:

- Makes focal pressure, conflict, stakes/change, hook, and human motive visible quickly.
- Could not be swapped with a generic premise without losing the story's private motive.
- Gives storyline design a direction without becoming a full synopsis.

Bad core concept:

- Is only a setting premise, theme sentence, or technology idea.
- Explains the decisive turn through abstract ethics instead of human motive.
- Requires a different accepted storyline to work.

## Traceability

Each final concept field must trace to intake, conflict seeds, open-question answers, or accepted storyline evidence. Compatibility with reader promise is reported as pending until the independent checker passes.

## Acceptance

The pre-story hypothesis passes only if it helps storyline design without replacing it. The final concept passes only if it is traceable to intake plus the accepted storyline, can be reconciled with the final reader promise before expansion, and could not be swapped with a generic version without losing the intake idea or its human motive anchor.
