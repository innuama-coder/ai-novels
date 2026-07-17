---
name: novel-proposal-risk-checker
description: Use when a novel proposal needs constraint, completeness, boundary, or PRD-readiness checking.
---

# novel-proposal-risk-checker

## Responsibility

Check whether a proposal obeys the intake boundary and is ready for human review and PRD.

## Input

- Proposal assembly artifact from `novel-proposal-integrator`
- Intake boundary ledger with readiness verdict
- Accepted storyline: complete story synopsis, Critical business claims, focal character and POV rule, Terminal agency map, main story chain, and auxiliary storylines
- Storyline quality report with reference evidence and severity counts
- Final reader promise
- Final core concept
- Final promise/concept consistency report
- Integration Verdict from `novel-proposal-integrator`
- Macro structure, core character frame, world premise, and ending direction outputs
- Human/intake confirmation status

## Output

Produce a risk report:

| Field | Requirement |
|---|---|
| Constraint violations | Missing `KEEP-*`, violated `AVOID-*`, ignored references |
| Conflict seed handling | Each `CONFLICT-*` developed, deferred with reason, or reopened |
| Open question handling | Each `OPEN-*` answered, deferred, or reopened |
| Boundary risks | PRD/HLD/LLD/prose leakage |
| Completeness risks | Missing proposal sections |
| PRD readiness | Whether PRD can choose a controlled scope |
| Storyline quality | Whether the storyline quality report passed against references and includes concrete reference evidence |
| Final promise/concept consistency | Whether the consistency report passed and is included |
| Integration verdict | Whether integrator produced an independent pass verdict for source completeness, traceability, no-new-business-content, and Claim Source Map coverage |
| Claim Source Map coverage | Whether every storyline Critical business claims row appears by stable `Claim ID`, complete claim text, and constraint role in the proposal assembly artifact, Integration Verdict, and risk report |
| Agent quality verdict | `pass`, `revise_skill_output`, or `reopen_intake` |
| Human/intake confirmation verdict | `confirmed`, `pending`, or `reopen_intake` |
| PRD entry verdict | `pass_to_prd`, `blocked_pending_human_confirmation`, or `blocked_revision_required` |

## Severity

| Level | Meaning |
|---|---|
| P0 | Violates intake boundary or rewrites user idea |
| P1 | Cannot enter PRD safely |
| P2 | Non-blocking watch item that may enter human review if no P0/P1 remains, but must be explicitly tracked |
| P3 | Note or downstream watch item |

## Rules

- Check all required gate reports before assigning agent quality verdict.
- Do not infer pass from a missing report, missing evidence, or polished proposal text.
- Treat an Integration Verdict without Claim Source Map coverage as missing integration proof.
- Treat any storyline Critical business claims row missing by `Claim ID`, complete claim text, or constraint role from the proposal assembly artifact, Integration Verdict, or risk report as P1.
- Treat keyword-like Critical business claims as P1 because they cannot prove story-logic preservation.
- Keep Agent quality, Human/intake confirmation, and PRD entry verdicts separate.
- Treat unresolved P0/P1 as blocking regardless of prose quality.

## Boundary

- Do not rewrite proposal content, storyline, reader promise, core concept, structure, characters, world premise, or ending direction.
- Do not replace specialized gates; consume their reports and fail when required reports or evidence are missing.
- Do not collapse Agent quality, Human/intake confirmation, and PRD entry into one verdict.
- Do not mark PRD entry `pass_to_prd` while human/intake confirmation is pending.

## References

Good risk report:

- Separates quality pass from human confirmation and PRD entry.
- Gives every P2 a downstream owner or handling path.
- Cites the exact proposal section or gate report behind each risk.

Bad risk report:

- Collapses all gates into a single pass/fail.
- Lets a readable story bypass missing evidence or missing consistency reports.
- Marks PRD entry pass while intake/human confirmation is pending.

## Traceability

Every risk, severity, and verdict must trace to the proposal assembly artifact, intake boundary ledger, storyline quality report, final consistency report, or named expansion output.

## Acceptance

The agent quality verdict cannot pass with any unresolved P0 or P1. The agent quality verdict may pass with P2 only when every P2 is recorded as a non-blocking watch item with an owner or downstream handling path. The PRD entry verdict cannot be `pass_to_prd` unless agent quality passes and human/intake confirmation is `confirmed`.

Treat as P1:

- Missing intake conflict seeds.
- Missing, non-passing, or evidence-free storyline quality report.
- Missing or non-passing final promise/concept consistency report.
- Missing or non-passing Integration Verdict.
- Integration Verdict lacks Claim Source Map coverage for critical business claims in the final proposal.
- Risk report does not explicitly list Claim Source Map coverage for every storyline Critical business claims row by `Claim ID`.
- Storyline Critical business claims are short phrases rather than complete business propositions with evidence quotes and constraint roles.
- Any unresolved P0/P1 from the storyline quality report.
- Any `OPEN-*` is silently ignored or answered without traceability.
- Any proposal section is sourced from optional old PRD/HLD/LLD/writing material as if frozen.
- Final reader promise, final concept, macro structure, character frame, world premise, or ending direction contradicts the accepted storyline, final reader promise, or final core concept.
- Final reader promise and final core concept contradict each other, even if each separately follows the accepted storyline.
- Proposal lacks a clear focal character and POV rule.
- Proposal lacks a Terminal agency map when focal character, thematic subject, information holder, emotional carrier, final decision owner, final executor, or irreversible consequence bearer differ.
- Proposal lacks a main story chain with narrative desire, opposition, escalation, turning logic, Terminal agency map, and irreversible outcome.
- Proposal replaces human motive with abstract ethics, theme, or grand good/evil.
- Complete story synopsis is readable but lacks suspense, conflict escalation, or focal character control.
- Storyline quality evaluator returns `revise_storyline` or leaves any blocking reference issue.
- Proposal leaks into PRD trunk scenes, chapter plan, full HLD world bible, LLD character dossier, or prose.

Treat as P0:

- Proposal violates `KEEP-*` or `AVOID-*`.
- Proposal rewrites the original idea or turns proposal design into user-confirmed intake.
- Proposal proceeds despite intake lacking a human motive seed plus at least one external pressure or suspense seed.

Gate rules:

- If agent quality passes but intake or human confirmation is pending, set PRD entry verdict to `blocked_pending_human_confirmation`.
- If agent quality has unresolved P0/P1, set PRD entry verdict to `blocked_revision_required`.
- If intake must be changed to make the proposal coherent, set agent quality verdict to `reopen_intake`.
- If P2 items remain, do not call them blockers; include them in the risk report as watch items and explain why they do not invalidate human review or PRD readiness.
