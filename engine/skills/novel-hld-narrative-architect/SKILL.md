---
name: novel-hld-narrative-architect
description: Build HA1's single macro narrative coordinate system from a current HB0 HLD baseline package. Use only when the novel-hld-autonomous harness issues an HA1 work order to choose a non-template structure, place existing major events and ending boundaries, and publish narrative-architecture.json. Do not use to revise conception facts, choreograph storylines, assign POV, design scenes, or write prose.
---

# Novel HLD Narrative Architect

## Mission

Create the one macro structure that every later HLD stage can reference. Treat
the baseline as authority and structure as an arrangement of existing
obligations, never as permission to invent story facts.

## Required reading

Read completely, in order:

1. [references/methodology.md](references/methodology.md)
2. [references/sop.md](references/sop.md)
3. [references/input-output-contract.md](references/input-output-contract.md)

Consult [references/sources.md](references/sources.md) only when auditing the
methodology provenance.

## Hard boundary

Own structural phases, narrative units, chapter shells, turning-point anchors,
entry/exit state contracts, scale ranges, and downstream structural
obligations. Do not own storyline content, character arcs, POV, information
release, pacing curves, scene actions, dialogue, sensory detail, or prose.

Do not default to three acts. Compare at least two materially different
structures unless only one structure is possible and the evidence rules out
alternatives. A candidate differs only when a canonical decision field and its
trade-off differ.

## Execute

1. Accept only the sealed HA1 work order and input gate.
2. Assess every projected unresolved source before generating a candidate.
3. If any HDD disposition is `required_now`, stop with
   `blocked/author_required`; do not form a canonical candidate.
4. Follow the five evidence steps and the stage SOP.
5. Write the draft directory with exactly:
   `canonical.json`, `generation-session.json`, and the five ordered files in
   `generation-evidence/`.
6. Run:

   ```powershell
   python scripts/run_skill.py <work-order.json> <draft-directory>
   ```

7. A zero exit and top-level `stage-result.result=ready` are both required.

The script proves contract truth and packages the result. It explicitly does
not prove that the chosen structure is artistically or semantically strong;
the self-review and downstream HQ1 own that judgment.

## Completion rule

Claim HA1 ready only when the published package contains the canonical model,
all ordered evidence, execution, preview, deterministic validation, manifest,
completion, and the single package-external result envelope. Any candidate
defect yields a durable local revise package. Any required author answer yields
a durable blocked package without candidate or completion.
