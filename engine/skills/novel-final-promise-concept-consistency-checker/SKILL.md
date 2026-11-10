---
name: novel-final-promise-concept-consistency-checker
description: Use when final proposal reader promise and final core concept must be checked for mutual consistency before expansion or delivery.
---

# novel-final-promise-concept-consistency-checker

## Responsibility

Check whether the final reader promise and final core concept describe the same novel direction and can both be supported by the accepted storyline. This is an independent business checker, not a harness action.

## Input

- Intake boundary ledger
- Accepted storyline and storyline quality report
- Final reader promise
- Final core concept

## Output

Produce a final promise/concept consistency report:

| Field | Requirement |
|---|---|
| Verdict | `pass`, `revise_final_promise`, `revise_final_concept`, `revise_both`, or `reopen_storyline` |
| Gate result | `pass` only when the promise and concept are mutually supportive; otherwise `blocked` |
| Compatibility status | `consistent`, `tension_requires_revision`, or `blocked` |
| Evidence | Specific reader-promise and core-concept phrases checked against the accepted storyline |
| Conflict findings | Contradictions, missing support, or mismatched reader expectations |
| Terminal agency findings | Whether final reader promise and final core concept preserve the accepted Terminal agency map |
| Revision target | Which upstream finalization output must rerun |
| Trace | Accepted storyline, storyline quality report, `CONFLICT-*`, and `OPEN-*` items checked |

## Rules

- Do not rewrite the final reader promise or final core concept.
- Do not judge by taste alone; name the exact promise/concept dimension being checked.
- Treat as blocking if the reader promise offers an experience the core concept cannot deliver.
- Treat as blocking if the core concept centers a hook, question, or focal pressure absent from the reader promise.
- Treat as blocking if either final output contradicts the accepted storyline, focal character rule, Terminal agency map, human motive anchor, or terminal outcome.
- If both final outputs are individually plausible but imply different novels, return `revise_both`.
- If consistency cannot be achieved without changing the accepted storyline, return `reopen_storyline`.

## Boundary

- Do not rewrite the final reader promise, final core concept, accepted storyline, or storyline quality report.
- Do not judge broad proposal quality, PRD readiness, macro structure, character frame, world premise, or ending direction.
- Do not pass two separately good outputs when they imply different focal characters, Terminal agency maps, conflict centers, reader experiences, or terminal outcomes.
- Do not repair inconsistency by inventing bridging content; return the appropriate revision verdict.

## References

Good final alignment:

- Reader promise names the experience the accepted storyline actually creates.
- Core concept names the hook, question, and human motive that make that experience possible.
- Both preserve the same focal pressure, information path, Terminal agency map, conflict center, and final irreversible outcome.
- Neither turns a proposal design decision into user-confirmed intake.

Bad final alignment:

- The promise sells genre pleasure that the concept does not structurally support.
- The concept highlights a theme or hook that the promise never prepares the reader to value.
- The promise frames one focal character while the concept depends on another character's hidden interiority.
- The concept changes the decisive human motive into abstract ethics after the promise centers private emotion.
- The promise implies one role owns the final decision while the concept depends on a different final executor or emotional bearer without acknowledging the split.

## Traceability

Every consistency finding must quote or identify the final reader promise field, final core concept field, accepted storyline element, Terminal agency map role, and intake/open-question source it checked.

## Acceptance

Pass only if:

- Final reader promise and final core concept both follow the accepted storyline.
- The reader experience can be delivered by the concept's hook, question, conflict, and human motive anchor.
- The concept does not require a different focal character, Terminal agency map, terminal outcome, or conflict center.
- The report includes concrete evidence from both final outputs and the accepted storyline.
