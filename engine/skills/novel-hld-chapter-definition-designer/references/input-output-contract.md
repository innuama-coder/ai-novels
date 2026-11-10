# HD1 Input and Output Contract

## Input gate

Accept only a Harness-signed work order for `stage=HD1`, exact owner `novel-hld-chapter-definition-designer`, and `mode=forward|return_resolution`. Ordered upstream is exactly `[HB0,HA1,HS1,HC1,HI1,HR1,HK1]`.

The stage reads only the sealed allowlist. HA1 supplies chapter shells and parent units. HS1 supplies chapter-level storyline roles. HC1 supplies character choices, costs, and arc states. HI1 supplies POV, knowledge, reveal, withholding, and suspense controls. HR1 supplies time, place, pace, tension, and continuity. HK1 supplies key-scene functions and downstream work requirements. HB0 remains the sole conception authority.

## Canonical output

`chapter-definition-architecture.json` is the only HD1 content authority. It contains:

- `chapter_definitions[]`: one `HDF-*` contract for every `HCH-*` shell;
- `chapter_chain[]`: exact consecutive entry/exit continuity and next-chapter necessity;
- `coverage_summary`: complete shell, storyline, character, environment, event, and key-function coverage;
- standard governance, authority, decision, derivation, unresolved, and downstream fields.

HD1 preserves upstream IDs. It owns only `HDF-*` chapter definitions and `HDC-*` chain links. A chapter definition does not own scenes and does not replace an HS1 `HCD-*` storyline assignment.

## Ready conditions

- Chapter numbers are contiguous and every HA1 shell is represented exactly once.
- Identity and storyline roles equal the current HA1/HS1 values.
- Every chapter contains a non-generic purpose, concrete entry and exit states, exact `hi1_assignment_id`, goal, opposition, escalation, consequential choice, explicit `choice_actor_ids`, exact `institutional_choice_actors`, explicit `cost_bearer_ids`, consequence, information change, and end pull. At least one named or institutional choice actor is required. POV exact-binds HI1 and the same HC1 chapter-agency contract; named choice actors and cost bearers must be subsets of HC1 roles, while institutional actors must exactly preserve HC1's role, source, responsibility, and authority limit. The focal character, decision maker, and affected character are not assumed to be the same person.
- Every chapter records required characters, environments, events, key functions, and LLD acceptance.
- Every adjacent pair has one `HDC-*` continuity link whose first exit makes the second entry possible or necessary.
- A memory chapter uses the full memory contract; a non-memory chapter sets `memory_design` to null.
- No LLD realization or prose leaks into HD1.

## Non-ready routing

Local incompleteness or duplication is `revise`. A contradiction in sealed structure, line assignment, character arc, information timing, continuity, or key functions is an upstream defect. An unresolved author-owned choice is blocked and must not be guessed.
