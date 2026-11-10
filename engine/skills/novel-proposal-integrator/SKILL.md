---
name: novel-proposal-integrator
description: Use when independent proposal skill outputs need to be assembled into one proposal document.
---

# novel-proposal-integrator

## Responsibility

Integrate proposal skill outputs into one proposal document without adding new business content.

## Input

- Intake boundary ledger with readiness verdict
- Pre-story reader promise and core concept hypotheses, for trace only
- Accepted storyline: complete story synopsis, Critical business claims, focal character and POV rule, Terminal agency map, main story chain, and auxiliary storylines
- Storyline quality report with reference evidence and passing gate result
- Final reader promise
- Final core concept
- Final promise/concept consistency report with passing gate result
- All proposal expansion outputs: macro structure, core character frame, world premise, and ending direction
- Source paths, versions, and status for all upstream artifacts

## Output

Proposal document with:

| Section | Source |
|---|---|
| Boundary ledger | `novel-intake-boundary-ledger-builder` |
| Conflict seed ledger | `novel-intake-boundary-ledger-builder` |
| Final reader promise | `novel-reader-promise-designer` in `final_promise` mode |
| Final core concept | `novel-core-concept-designer` in `final_concept` mode |
| Final promise/concept consistency report | `novel-final-promise-concept-consistency-checker` |
| Macro structure | `novel-macro-structure-designer` |
| Complete story synopsis, Critical business claims, main story chain, and auxiliary storylines | `novel-storyline-designer` |
| Storyline quality report | `novel-storyline-quality-evaluator` |
| Focal character and POV rule | `novel-storyline-designer` |
| Terminal agency map | `novel-storyline-designer` |
| Core character frame | `novel-core-character-framer` |
| World premise | `novel-world-premise-framer` |
| Ending direction | `novel-ending-direction-designer` |
| Integration verdict | Integrator's source-completeness, traceability, and no-new-business-content verdict |
| Claim Source Map | Critical business claims mapped by stable `Claim ID`, complete claim text, constraint role, and exact upstream artifacts/sections |
| PRD handoff | Derived from prior outputs only |

## Rules

- Assemble only named source outputs.
- Keep gate reports and evidence visible in the proposal.
- Normalize wording without adding new business content.
- Report contradictions or missing sources instead of smoothing them over.
- Use the storyline designer's Critical business claims as the minimum Claim Source Map set. Preserve `Claim ID`, complete claim text, and constraint role. Add rows only when the final proposal contains additional critical claims from other accepted artifacts.
- For every critical business claim in the final proposal, provide a Claim Source Map row naming `Claim ID`, complete claim text, upstream artifact, source section, and constraint role.

## Boundary

- Do not invent missing logline, roles, structure, world premise, or ending.
- Do not smooth over contradictions; report them.
- Do not promote optional design decisions to intake constraints.
- Do not drop or rename `CONFLICT-*` seeds during assembly.
- Do not accept a theme-line table as a substitute for the main story chain.
- Do not accept any proposal that lacks a readable complete story synopsis.
- Do not accept any proposal that lacks a storyline quality report with a passing gate result and concrete reference evidence.
- Do not accept any proposal that lacks a final promise/concept consistency report with a passing gate result.
- Do not accept a proposal whose focal character, thematic subject, and information access are blurred.
- Do not accept a proposal whose Terminal agency map is missing or contradicted by character, ending, promise, or concept outputs.
- Do not accept a proposal whose key conflict is explained only by abstract ethics or grand good/evil instead of character motive.
- Do not accept a proposal whose final reader promise and final core concept contradict each other.
- Do not pass Integration Verdict when a critical claim appears in the final proposal but not in an upstream business artifact, or when a Claim Source Map row has only a keyword instead of a complete proposition.
- Do not convert the main story chain into PRD trunk scenes.

## References

Good proposal integration:

- Reads as one concise proposal while preserving source trace.
- Keeps complete story, reference evidence, consistency report, and risk gates visible.
- Keeps Integration Verdict visible as the proof that assembly did not invent or hide business content.
- Shows claim-level trace for decisive story facts by stable ids and complete propositions, not only section-level source labels or keywords.
- Makes PRD handoff possible without inventing missing plot.

Bad proposal integration:

- Hides missing or conflicting source outputs behind polished prose.
- Adds new concept, role, world rule, or ending during assembly.
- Drops reference evidence or gate verdicts.
- Uses a final risk report as a substitute for integrator's own Integration Verdict.
- Claims no-new-business-content while only providing coarse section-level trace.

## Traceability

Every proposal section must name its source skill or intake/open-question source. Every Critical business claims row from the storyline designer must appear in the Claim Source Map with the same `Claim ID`, complete claim text, and constraint role. Every final-proposal critical story claim must also appear in a Claim Source Map row that names the upstream artifact and section. Any wording normalization must preserve the upstream claim and gate status.

## Acceptance

The integrated proposal passes if:

- Every claim can trace to intake or one named proposal skill output.
- Every Critical business claims row from the storyline designer appears in the integrated proposal and in the integrator's Claim Source Map by `Claim ID`.
- Every critical business claim in the final proposal appears in an upstream artifact and in the integrator's Claim Source Map as a complete proposition, not a keyword.
- Every `CONFLICT-*` seed is visibly developed or explicitly reopened.
- The storyline quality report is included, has a passing gate result, includes concrete reference evidence, and has no unresolved P0/P1.
- The final promise/concept consistency report is included and has a passing gate result.
- The proposal contains a complete story synopsis readable as a story, not only as a design document.
- The final reader promise and final core concept are mutually consistent and both follow the accepted storyline.
- The proposal clearly distinguishes focal character, thematic subject, and major information access.
- The proposal includes Terminal agency map and preserves it across character, ending, promise, concept, and PRD handoff sections.
- The proposal contains a main story chain with narrative desire, opposition, escalation, turning logic, Terminal agency map, and irreversible outcome.
- The proposal contains enough suspense and conflict layers to sustain its reader promise.
- The decisive hidden cause or turn is anchored in human motive.
- Auxiliary storylines are clearly subordinate to the main story chain.
- PRD handoff receives enough story progression to design trunk scenes without inventing the whole plot.
