---
name: novel-storyline-designer
description: Use when a novel proposal needs main, secondary, hidden, emotional, or thematic storyline design.
---

# novel-storyline-designer

## Responsibility

Design proposal-level storylines. The primary output is not a theme list or a structural table; it is a readable complete story at proposal granularity.

## Input

- Intake boundary ledger
- `KEEP-*`, `AVOID-*`, `CONFLICT-*`, and `OPEN-*` items from the ledger
- Reference rules and non-frozen material boundaries
- Pre-story reader promise hypothesis, explicitly non-binding
- Pre-story core concept hypothesis, explicitly non-binding

If the input lacks a human motive seed plus at least one external pressure or suspense seed, do not design the storyline. Return an intake reopen request.

## Output

| Field | Requirement |
|---|---|
| Complete story synopsis | A continuous narrative summary with beginning, middle, and ending that lets a reader understand what happens |
| Critical business claims | A table of decisive proposal facts using `Claim ID`, complete `Claim`, `Constraint role`, `Evidence quote`, and `Source within artifact` |
| Focal character and POV rule | Who the reader primarily follows, what that character can know, and which major information should not be shown directly |
| Terminal agency map | Identify focal character, thematic subject, information holder, emotional carrier, final decision owner, final executor, and irreversible consequence bearer when they differ |
| Main story chain | The central sequence of narrative pressure, from trigger to irreversible terminal outcome |
| Story driver | Who wants what, why it matters, what blocks it, and what worsens if it fails |
| Suspense and conflict layers | External suspense, interpersonal conflict, institutional/ethical conflict, and internal contradiction as needed |
| Human motive anchor | The private desire, fear, guilt, love, protection, shame, or weakness that makes the plot matter as human story |
| Turning logic | The key reversals or discoveries that change the focal character's understanding, the thematic subject's agency, or the terminal action path |
| Terminal choice and outcome | Who decides, who executes, who pays the emotional cost, and why the irreversible outcome cannot be avoided |
| Auxiliary storyline list | Secondary, hidden, emotional, thematic as needed |
| Each auxiliary line | Question, start state, change direction, end state |
| Intersections | High-level relationship between lines |
| Constraint trace | Intake constraints, conflict seeds, and open questions used |

## Rules

- Deliver a complete readable story before any tables can pass.
- Declare Critical business claims after the complete synopsis and before downstream tables. Include only claims whose removal or alteration would change PRD/HLD constraints.
- Each Critical business claim must be a complete proposition, not a short keyword. It must state the actor or subject, action/change, and story constraint being preserved.
- Each Critical business claim must have a stable `CLAIM-##` id, a constraint role, an evidence quote copied from the complete story synopsis, and a source pointer to the synopsis paragraph.
- Develop every conflict seed or explicitly reopen intake.
- Keep decisive turns rooted in private human motive.
- Declare focal character and information access before using hidden motives.
- If focal character, thematic subject, information holder, emotional carrier, final decision owner, final executor, or irreversible consequence bearer differ, declare the split before the main story chain can pass.

## Boundary

- Do not write scenes, chapters, or event-by-event plot.
- Do not solve PRD trunk scenes, but do define proposal-level causal story progression.
- Do not create storylines that require violating `AVOID-*`.
- Do not substitute abstract theme movement for story movement.
- Do not substitute tables, labels, or design categories for a complete story synopsis.
- Do not use Critical business claims to introduce facts absent from the complete story synopsis.
- Do not leave the PRD to invent the story's central desire, opposition, escalation, terminal agency split, or irreversible outcome.
- Do not rely on a single conflict if the premise naturally supports layered suspense.
- Do not mix focal characters, agency owners, or access to private motives without declaring a POV rule and Terminal agency map.
- Do not replace character motive with abstract ethics, grand good/evil, or theme statements.
- Do not ignore or overwrite `CONFLICT-*` seeds from intake.

## References

Good storyline:

- Can be read continuously as one story with beginning, middle, and ending.
- Has desire, obstacle, escalation, reversal, terminal agency, and final irreversible outcome.
- Names its decisive business claims as complete propositions with stable ids, constraint roles, exact synopsis evidence, and source pointers.
- Uses auxiliary lines to intensify the same main story.
- Lets hidden causes, terminal choices, and irreversible outcomes emerge from human motive.

Bad storyline:

- Is a table of labels without story movement.
- Leaves PRD to invent central desire, opposition, or ending.
- Uses theme, institution, or technology as a substitute for human choice.

## Traceability

Every major turn, conflict layer, critical business claim, terminal agency role, terminal choice, and irreversible outcome must trace to intake conflict seeds, open-question answers, pre-story hypotheses, or explicit proposal design labels.

## Acceptance

Pass only if:

- The main story chain can answer: who wants what, what resists them, what changes, and why the ending follows.
- The complete story synopsis can be read by a human as one coherent story without needing to inspect the tables.
- Critical business claims are present, use the required schema, are all supported by exact evidence quotes in the complete story synopsis, and cover decisive facts needed by integration and PRD handoff.
- The focal character and POV rule are explicit enough to prevent downstream perspective drift.
- The Terminal agency map explicitly names focal character, thematic subject, information holder, emotional carrier, final decision owner, final executor, and irreversible consequence bearer when any of them differ.
- At least one external pressure and one internal pressure are present.
- The story contains enough conflict layers to sustain the promised genre experience.
- The central hidden cause or decisive turn is rooted in human motive, not only in ideas or institutions.
- Every `CONFLICT-*` seed is developed, deferred with reason, or reopened.
- The terminal choice and irreversible outcome are caused by prior story pressure, not appended as a theme statement.
- Auxiliary storylines support the main chain rather than replacing it.
- The output remains above scene level: no scene numbers, chapter plan, prose, or full PRD trunk scene table.
