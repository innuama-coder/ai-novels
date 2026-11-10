---
name: novel-storyline-quality-evaluator
description: Use when a proposal storyline, complete story synopsis, or main story chain needs subjective quality evaluation before proposal delivery.
---

# novel-storyline-quality-evaluator

## Responsibility

Evaluate whether the storyline is good enough to deliver. This is a business skill, not a harness action: it judges the story against references for good storylines and reports pass, revise, or reopen.

## Input

- Intake boundary ledger
- Pre-story reader promise and core concept hypotheses, explicitly non-binding
- Complete story synopsis
- Critical business claims
- Focal character and POV rule
- Terminal agency map
- Main story chain and auxiliary storylines

## Output

Produce a storyline quality report:

| Field | Requirement |
|---|---|
| Verdict | `pass`, `revise_storyline`, or `reopen_intake` |
| Gate result | `pass` only when all pass conditions are satisfied; otherwise `blocked` |
| Severity counts | Count of P0, P1, P2, and P3 findings |
| Pass conditions checked | Checklist for the acceptance bullets below |
| Reference assessment | Good-story references applied to the synopsis and story lines |
| Reference evidence | For each reference dimension judged pass/fail, cite the specific synopsis or story-chain evidence and explain why it satisfies or fails the reference |
| Critical business claims assessment | Whether every claim has `Claim ID`, complete `Claim`, `Constraint role`, exact synopsis `Evidence quote`, and is suitable as the minimum integration Claim Source Map set |
| Terminal agency assessment | Whether focal character, thematic subject, information holder, emotional carrier, final decision owner, final executor, and irreversible consequence bearer are explicit and coherent |
| Blocking issues | P0/P1 issues that prevent delivery |
| Revision targets | Concrete storyline parts to rerun, not prose edits |
| Strengths | What already works and should be preserved |
| Trace | Which intake constraints and `CONFLICT-*` seeds were checked |

## Rules

- Do not rewrite the story, synopsis, or story chain.
- Do not reject a stronger storyline merely because it improves on a pre-story hypothesis. Treat pre-story reader promise and core concept as orientation, not frozen constraints.
- Do not evaluate by personal taste alone; every judgment must name a reference dimension below.
- Treat lack of human motive anchor as P1 even if the plot is structurally complete.
- Treat focal character drift as P1 when it changes what the reader knows or feels.
- Treat missing, synopsis-unsupported, materially incomplete, keyword-like, or schema-incomplete Critical business claims as P1 because integration cannot prove no-new-business-content without them.
- Treat missing or blurred Terminal agency map as P1 when focal character, thematic subject, final decision owner, final executor, or emotional carrier differ.
- Treat abstract ethics, institutions, or grand good/evil as insufficient if they replace private human motive at the decisive turn.
- Treat unresolved P0/P1 as blocking. A proposal with blocking issues cannot be marked accepted.
- If the intake does not provide enough conflict seed material to judge the story, request intake reopen instead of asking proposal to invent it.
- Verdict, gate result, severity counts, and blocking issues must be internally consistent. `pass` is forbidden when any P0/P1 count is nonzero or any blocking issue remains.
- Do not mark `pass` unless the reference assessment includes concrete evidence from the complete story synopsis or main story chain. A checklist without evidence is not a quality evaluation.
- P2 findings are non-blocking only when they are framed as watch items whose risk does not invalidate the good-story references.

## Boundary

- Do not rewrite the storyline, complete story synopsis, main story chain, auxiliary lines, or POV rule.
- Do not invent new conflict seeds to make the story pass.
- Do not judge final reader promise, final core concept, macro structure, character frame, world premise, or ending direction except where they are required inputs to understand the storyline under review.
- Do not let a polished proposal bypass missing reference evidence; report `revise_storyline` or `reopen_intake` according to the source of the problem.
- Do not let a readable synopsis pass when Critical business claims omit decisive facts that downstream PRD/HLD must preserve, or when claims are only short phrases rather than complete propositions.

## References

Good complete story synopsis:

- Can be read continuously without tables.
- Shows a concrete character or focal subject under pressure, not only a premise.
- Contains desire, obstacle, escalation, reversal, terminal agency, and final irreversible outcome.
- Makes the hidden cause or decisive turn emerge from human motive: love, protection, guilt, shame, fear, weakness, longing, or private obligation.
- Lets the ending feel caused by prior pressure rather than appended as a theme statement.
- Controls information through a clear focal character or declared POV rule.
- Separates focal character, thematic subject, information holder, emotional carrier, final decision owner, final executor, and irreversible consequence bearer when the story uses split agency.

Good story line:

- Has a dramatic question, start state, change path, terminal state, and relationship to the main chain.
- Makes auxiliary lines serve the main story instead of replacing it.
- Uses conflict layers to intensify the same central story, not to create unrelated noise.
- Keeps suspense alive by changing what the focal character and reader understand.
- Keeps suspense alive by changing what the focal character and reader understand, even when another role owns the terminal decision.

Bad storyline delivery:

- Theme labels without events.
- A setting premise with no human choice.
- A complete plot whose key turn depends on abstract ethics instead of a private motive.
- A table that looks organized but cannot be read as a story.
- A finale that would be identical if the Terminal agency map changed.
- A story where the stated focal character is not the character carrying information, pressure, or emotional cost.
- A story where one character decides, another executes, and another carries the emotional cost, but the proposal does not declare that agency split.

## Traceability

Every pass/fail judgment must cite the exact synopsis, main-chain, auxiliary-line, or intake-ledger evidence used. Findings must name the skill output that should be rerun.

## Acceptance

Pass only if:

- The complete story synopsis meets the good synopsis references.
- The main story chain meets the good story line references.
- Every `CONFLICT-*` seed is developed, deliberately deferred, or reopened.
- Human motive drives the decisive hidden cause or final turn.
- Focal character, thematic subject, information holder, and emotional carrier are distinct when they are not the same role.
- Terminal agency map names final decision owner, final executor, and irreversible consequence bearer when they are not the same role.
- Reference evidence shows why the story is readable, causal, suspenseful, human-motive anchored, and not merely a structured table.
- Critical business claims use stable ids, complete propositions, constraint roles, exact synopsis evidence quotes, and cover the decisive facts needed by integration and PRD handoff.
- No unresolved P0/P1 remains.
