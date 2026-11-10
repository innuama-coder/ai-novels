---
name: novel-hld-integrity-checker
description: Use when HLD artifact 12 must check final HLD consistency, source closure, risk severity, convergence, and LLD entry verdict.
---

# novel-hld-integrity-checker

## Responsibility

Own HLD artifact 12 only: independently check HLD package quality and route readiness.

## Inputs

- Artifacts 01-11 and their Skill Verdicts
- HLD Source Map and LLD handoff index from artifact 11
- Methodology reference: `engine/docs/superpowers/references/2026-07-08-hld-methodology-and-best-practices.md`

## Output Artifact

Produce these sections:

`## Artifact Metadata`

| Field | Value |
|---|---|
| Artifact id | `12` |
| Owner skill | `novel-hld-integrity-checker` |
| Run id | HLD run id |
| Upstream package | final PRD package and artifact 11 |
| Input artifacts | artifacts 01-11 |
| Output path | artifact path assigned by harness |
| Version | artifact version |

`## HLD Fact Trace`

| Fact trace id | Upstream fact id | Upstream fact atom | HLD fact atom | Source refs | Expansion mode | Support mechanism | Preservation status |
|---|---|---|---|---|---|---|---|

For artifact 12, fact trace rows point to checked facts or risk findings rather than adding new HLD facts.

Every non-`none` `Risk` id in `## Risks` must have a matching `Fact trace id`; every unresolved P0/P1 risk must also have a convergence row.

`## Output`

| Field | Value |
|---|---|

`## Risks`

| Risk | Severity | Source refs | Owner artifact | Rerun target | Handling | Blocking verdict effect |
|---|---|---|---|---|---|---|

`## Verdict consistency matrix`

| Verdict | Required condition | Actual evidence | Resolved value | Consistency |
|---|---|---|---|---|

`## Artifact rubric coverage`

| Artifact | Good delivery evidence | Blocking failure check | Coverage verdict |
|---|---|---|---|

`## Reconciliation closure checks`

| Initial inventory id | Request id | Decision | Canonical subject id | Final inventory id | Origin artifact | Origin source refs | Origin fact trace id | Evidence | Verdict |
|---|---|---|---|---|---|---|---|---|---|

`## Environment closure checks`

| Environment id | Inventory id | State change id | State change dimension | State before | State after | Event ids | Event state transition refs | Event state realization refs | Source Map HLD fact id | Evidence | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|

`## Event closure checks`

| Event id | Inventory id | Cause refs | Event action | Causal role | Consequences | Environment state change refs | Event fact id | Event closure evidence | Verdict |
|---|---|---|---|---|---|---|---|---|---|

`## Information closure checks`

| Info id | Inventory id | PRD information boundary id | Freeze refs | Story anchor event ref | Time layer | Narrative reveal phase | Disclosure tier | Known by | Hidden from | Reveal predecessor refs | Reveal event ref | Reveal action | Reveal condition type | Reveal condition refs | Reveal condition | Information fact id | Information closure evidence | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

`## Thread closure checks`

| Thread id | Thread type | Thread function | Thread anchor refs | Required pressure refs | Thread progression | Crossover | Closure outcome | Evidence | Verdict |
|---|---|---|---|---|---|---|---|---|---|

`## Style/POV closure checks`

| Style/POV id | Rule type | Access policy | Information refs | Thread refs | Reader disclosure mode | Language profile | Design fact | POV permission | Prohibited expression | LLD handoff | Evidence | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|

`## HLD Convergence Log`

| Stable issue id | Severity | Root cause | Fix hypothesis | Regression proof | Attempt count | Rerun target | Status |
|---|---|---|---|---|---|---|---|

## SOP

1. Check artifact presence, schema, Skill Verdicts, and DAG order.
2. Check source grammar, source closure, inventory coverage, Source Map preservation, and the one-to-one Source Map / LLD handoff-index closure.
3. Check business consistency across world rules, characters, environments, events, time/information, threads, and style/POV.
4. Assign P0/P1/P2/P3 severity and route each issue to the owning artifact with source refs and rerun target.
5. Fill `Artifact rubric coverage` for artifacts 01-12 using the methodology reference rubric.
6. For every artifact 05 environment, produce one `Environment closure checks` row that cites its inventory id, state-change id and dimension, exact state before/after tokens, exact artifact 06 event ids, exact event-state transition and realization refs, exact artifact 11 Source Map fact id, and evidence. Assess whether function, spatial relation, the state transition, and the event realization make the declared change consequential; block when any reference is missing, mismatched, reversed, or semantically unsupported.
7. For every artifact 06 event, produce one `Event closure checks` row that cites its inventory id, exact cause refs, action, causal role, consequences, environment state-change refs, and artifact 11 Source Map fact id. Assess whether the predecessor chain, action, role, consequence, visibility, and environment realization make a consequential event rather than a chronological placeholder; block when evidence is missing, mismatched, cyclic, or semantically unsupported.
8. For every artifact 07 information object, produce one `Information closure checks` row that cites exact inventory identity, PRD information-boundary id, freeze refs, story anchor, time layer, narrative reveal phase, disclosure tier, knowledge state, reveal predecessor, reveal event, exact reveal action, condition type/refs, reveal condition, and the exact artifact 11 Source Map fact id. Block if the information object, its canonical source atom, PRD boundary/freeze alignment, source-mapped fact id, time/reveal graph, knowledge distribution, or reveal mechanics do not resolve exactly.
9. For every required artifact 08 core thread, produce one `Thread closure checks` row that exactly repeats its type, function, resolved anchors, pressure refs, ordered progression, crossover, and closure outcome. Assess whether the progression changes the stated question through its type-specific function rather than attaching a label; block missing, mismatched, stateless, or unsupported entries.
10. For every artifact 09 rule, produce one `Style/POV closure checks` row that exactly repeats its type, access policy, information refs, thread refs, reader disclosure mode, language profile, design fact, POV permission, prohibited expression, and LLD handoff. Assess whether all eight types are covered; `Design fact`, `POV permission`, and `Prohibited expression` use their required three-part execution structures and type-specific behavior; scope/target/evidence resolve to the same row's permitted information or thread refs; trigger equals the reader disclosure mode; focalizer resolves to artifact 04; the language-style row defines mode/limit, sentence/variation, prefer/avoid, and pace/shift; no field uses a vague style adjective or padded atomic name; and the referenced information/thread boundary makes permission and prohibition operational. Block missing, malformed, mismatched, vague, unbound, or unbounded entries.
11. Produce exactly one `Reconciliation closure checks` row for every artifact 10 subject, copying its request, decision, canonical subject, final id, origin artifact/source, and fact trace id. Independently verify artifact 10: every subject comes from the reconstructed inventory/amendment register; entity, owner, source, and fact trace bind to its origin; every merge names an accepted canonical subject; every accepted inventory row has one final id; amendments never mint ids; and a continuity input preserves prior resolved ids.
12. Independently check artifact 11: every accepted artifact 03-09 fact trace has exactly one Source Map row; each row preserves the trace's source facts and owner, uses a reconciled final inventory id only for inventory-bound facts, and has exactly one `ready` LLD handoff-index row with the same handoff target and fact-level fields.
13. Set `Resolved value` in each Verdict consistency matrix row to the identical authoritative value from `## Output`.
14. Apply verdict consistency: unresolved P0/P1 cannot coexist with pass readiness.
15. Record exactly one `open` or `blocked` convergence row for every unresolved P0/P1, with the same stable issue id, severity, and rerun target as its Risk row.

## Boundary

Do not rewrite HLD facts, fix tables, or add missing design content. This skill reports and routes only.

## Rules

- `Agent quality verdict = pass` requires all required checks pass and no unresolved P0/P1.
- `LLD entry verdict = pass_to_lld` requires Agent quality pass plus human review state `confirmed` or `not_required`.
- `LLD entry verdict = blocked_pending_human_review` requires human review state `pending_required`.
- `LLD entry verdict = blocked_revision_required` is required for unresolved P0/P1, non-pass Agent quality, or `reopen_hld`.
- Block if P0/P1 coexists with pass verdict or convergence row is malformed.
- `## Output` must contain exactly Agent quality verdict (`pass|fail`), HLD human review state (`confirmed|not_required|pending_required|reopen_hld`), and LLD entry verdict (`pass_to_lld|blocked_pending_human_review|blocked_revision_required`).
- `## Verdict consistency matrix` must contain exactly one row for each Output field; `Resolved value` must equal the corresponding Output value.
- Each non-`none` Risk must have exactly one complete `HLD Fact Trace` row with a valid `UPF-...` upstream fact id, valid expansion mode, matching source refs, `Preservation status = risk_reported`, and an exact upstream id/atom/source match in artifacts 01-11.
- `## HLD Convergence Log` must use its declared columns. Every non-`none` log row must map to one Risk with the same stable issue id, severity, and rerun target. Every unresolved P0/P1 Risk must have exactly one same-id, same-severity, same-rerun-target row with status `open` or `blocked`; a `fixed` or `closed` row cannot stand in for an unresolved risk.
- Unresolved P0/P1, `Agent quality verdict = fail`, and `HLD human review state = reopen_hld` take precedence over `pending_required` and require `LLD entry verdict = blocked_revision_required`.
- Block if any artifact rubric coverage row is `fail` or `blocked`.
- Artifact 04 rubric coverage must explicitly check concrete motive pressure and the digital-life identity boundary; generic "character system checked" evidence is insufficient.
- Artifact 05 rubric coverage must explicitly check environment inventory coverage, spatial relation, state-change dimension, state transition, event state realization, and Source Map trace closure; generic "environment system checked" evidence is insufficient.
- `Environment closure checks` must contain exactly one passing row per artifact 05 environment; each row must resolve to the actual artifact 05 state-change id, dimension, and before/after tokens, artifact 06 event references, transitions, and realizations, and artifact 11 Source Map fact id. Evidence must explain the checked function, spatial relation, transition, and realized consequence; a bare identifier list is insufficient.
- Artifact 06 rubric coverage must explicitly check event inventory coverage, causal-chain closure, concrete event action, consequence, visibility, environment integration, and Source Map trace closure; generic "event system checked" evidence is insufficient.
- `Event closure checks` must contain exactly one passing row per artifact 06 event; each row must resolve to the actual inventory id, cause refs, action, causal role, consequences, environment state-change refs, and artifact 11 Source Map fact id. Event closure evidence must explain the checked cause, action, role, consequence, and environment realization; a bare identifier list is insufficient.
- Artifact 07 rubric coverage must explicitly check information inventory coverage, story anchor, time layer, narrative reveal phase, reveal predecessor, disclosure tier, knowledge state, reveal event/action, condition type/refs, and Source Map trace closure; generic "information system checked" evidence is insufficient.
- `Information closure checks` must contain exactly one passing row per artifact 07 information object; each row must resolve to the actual inventory id, story anchor, time layer, narrative reveal phase, disclosure tier, knowledge state, reveal predecessor, reveal event/action, condition type/refs, reveal condition, and artifact 11 Source Map fact id. Information closure evidence must explain the checked anchor, layer, phase, tier, knowledge distribution, predecessor, reveal action, and condition; a bare identifier list is insufficient.
- Artifact 08 rubric coverage must explicitly check main, hidden, emotional, theme, institutional, and identity threads, their Thread function, Required pressure refs, Thread progression, crossover, and closure outcome; generic "thread system checked" evidence is insufficient.
- `Thread closure checks` must contain exactly one passing row per required core thread and exactly match artifact 08 function, anchors, pressure, progression, crossover, and closure outcome. Evidence must explain function, anchors, pressure, progression, crossover, and closure; a bare identifier list is insufficient.
- Artifact 09 rubric coverage must explicitly check POV, narrative distance, information access, digital-life interiority, dialogue, image system, prohibited expression, language style, access policy, reader disclosure mode, information refs, thread refs, type-specific behavior, vague-expression rejection, execution-reference closure, focalizer resolution, structured execution fields, language directives, and LLD handoff; generic "style system checked" evidence is insufficient.
- `Style/POV closure checks` must contain exactly one passing row per artifact 09 rule and exactly match its type, access policy, information refs, thread refs, reader disclosure mode, language profile, design fact, POV permission, prohibited expression, and LLD handoff. Evidence must explain policy, information, thread, reader, language, design, permission, prohibition, and handoff; a bare identifier list is insufficient.
- Artifact 10 rubric coverage must explicitly check the reconciliation subject register, origin binding, canonical merge target, single final inventory id, amendment blocking, and continuity. A generic claim that reconciliation was checked is insufficient.
- Artifact 11 rubric coverage must explicitly check fact-level Source Map closure for artifact 03-09 and one-to-one `ready` LLD handoff-index closure. A generic claim that integration was checked is insufficient.

## References

Good checking is adversarial, source-specific, and routeable. Bad checking says "mostly consistent" without severity, owner, root cause, and regression proof.

## Traceability

Every non-`none` risk must name source refs, owner artifact, rerun target, matching `Fact trace id`, and handling state. Every artifact 01-12 must have one rubric coverage row.

## Acceptance

Pass only when the report can deterministically block, pass, or route the HLD without hidden reviewer judgment.

## Skill Verdict

| Field | Value |
|---|---|
| Skill quality verdict | `pass`, `pass_with_p2`, or `fail` |
| Source closure | `closed` or `open:<reason>` |
| Inventory coverage | `closed`, `not_applicable`, or `open:<reason>` |
| Boundary obedience | `pass` or `violation:<source ref>` |
| Downstream readiness | `ready`, `blocked:<reason>`, or `reopen_upstream:<target>` |
| Blocking issue | `none` or stable issue ids |
| Rerun target | `none` or artifact/skill id |
