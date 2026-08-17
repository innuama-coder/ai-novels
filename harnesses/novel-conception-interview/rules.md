# Harness Rules

## Authority order

1. This file and `workflow.md` define canonical orchestration.
2. JSON schemas and validator verdicts define structural truth.
3. A stage's leaf skill defines its creative method within its assigned stage.
4. Legacy documents under `docs/ai-novel-workflow/` explain compatibility only;
   they cannot alter the stage graph or gates.
5. An author's explicit decision controls artistic values and approvals.

## Evidence and file rules

- Create `plan.v1.json` before asking the first substantive question. It states
  the exact total question budget, per-group allocation, duration estimate,
  output artifact and transcript assurance mode.
- `plan.vN.json` files must not be overwritten. A changed plan is a new version
  linked to an `author_approved_plan_revision` decision event; completion files
  bind the report, design artifact and validation evidence by SHA-256 so later
  edits invalidate their handoff.
- The first event presents plan revision 1 to the author. Every question names
  the currently active `plan_revision`; a revision event must first record the
  author's approval reference and announce its exact revised question budget
  and duration. An early close must likewise name the active revision and an
  explicit approval reference. A later plan may not retroactively legitimise a
  question that was asked under another revision.
- Append one JSON object per event to `events.ndjson`; never rewrite prior
  events. Regenerate, do not hand-edit, `report.md` from the log.
- Run `validate_session.py` after every append and before a stage completion;
  downstream stages accept only `validation.json` verdict `ready`.
- Every completion must hash-bind `run-state.json`; every upstream completion
  reference is `{path, sha256}`. An active return package blocks every stage
  except its named target. That target must hash-bind the package in
  `return_resolution`; the next run state records both the package and that
  corrected completion in `resolved_returns`. Downstream handoffs must consume
  the corrected completion, never a stale pre-return packet.
- After a completion is validated, the controller writes the next run state with
  that I-stage packet as the current completion. Resolving a return clears every
  affected downstream current reference; regenerated stages must consume the
  corrected target packet before becoming current. A third return from one
  origin stage is blocked pending explicit author direction.
- Every new I0–I5 completion is contract version `2.0`, hash-binds exactly one
  canonical `control-projection.json`, and binds that projection to the same
  run, stage, session and design-artifact bytes. Control IDs use the stage-owned
  prefixes `INT-`, `SUB-`, `WLD-`, `CHR-`, `CAU-`, and `NAR-`; IDs are stable
  within a run. Every control binds exactly one complete H2/H3 Markdown
  section: `heading` reproduces that section heading and string `value`
  reproduces its non-blank body after newline normalization. A matching line
  hash without this lossless heading/body match is invalid.
- V1 revalidates all six current interview completions, uses contract version
  `2.0`, and hash-binds `fact-dependency-register.json`. Each dependency is
  explicitly `adopted`, non-blocking `open`, or `not_applicable`; missing
  research evidence is never silently converted into a fictional fact.
- All unresolved facts are recorded as `open`, `provisional`, `inference`, or
  `blocked`; never upgrade them to `confirmed` merely to pass a gate.
- A factual research claim, if needed, must carry claim text, source URL/title,
  retrieval date, scope, confidence, and adoption decision. Research is
  evidence, not a hard-coded fictional fact.

## Transcript assurance

This release supports only `self_recorded`. A future runtime may add
`event_backed` only with an adapter-specific verifier that resolves immutable
event IDs against that runtime; a string supplied by the agent is never proof.
A rendered self-recorded report must visibly say it is a reconstructed record
and cannot claim verbatim or externally event-backed provenance.

## Human approval rules

The author must explicitly approve a plan revision, early close, V2 review
brief, and any third return round. Record V2 approval as an external
`author-approval.json` conforming to `author-approval.schema.json` and hash-bind
it to the exact reviewed HTML. The V2 generator may prepare the review surface
but cannot create, infer, or self-record the author's decision. Agents may
propose choices but cannot manufacture any approval.

V1 must emit a hash-bound semantic-review packet with evidence for all six
control areas and a valid fact-dependency register. V2 consumes only a V1
packet whose semantic verdict is `pass`. Autonomous B0 consumes the exact
current I0–I5, V1, V2 and external V2 approval chain under the autonomous
contract; this harness does not produce D1, R1, a development map, a conception
review, P1, or H1.

## Done rule

Do not state that the interview chain is complete or ready for B0 unless all
current I0–I5 projections, V1 validation/semantic/fact evidence, the current V2
brief, and its external author approval are present and hash-bound. This verdict
means only that interview evidence is admissible to B0; it does not claim that
the novel conception or any autonomous deliverable is complete.
