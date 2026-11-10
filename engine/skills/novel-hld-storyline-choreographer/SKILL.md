---
name: novel-hld-storyline-choreographer
description: Build HS1's complete multi-storyline choreography from current HB0 and HA1 packages. Use only when novel-hld-autonomous issues an HS1 work order to identify authoritative storylines, segment and place them in HA1 units, define typed connections and activation dispositions, and prove the story subject can be reconstructed. Do not invent story facts, character arcs, POV, pacing, scenes, or prose.
---

# Novel HLD Storyline Choreographer

## Mission

Turn all authoritative story strands into one connected narrative network in
HA1's coordinate system. Preserve the identity and role of each line while
making its contribution, connection, and disposition explicit. Complete the
HLD chapter design by assigning every HA1 chapter shell a readable chapter
title, its core content, its storyline roles, and the change reached at the end.

## Required reading

Read completely, in order:

1. [references/methodology.md](references/methodology.md)
2. [references/sop.md](references/sop.md)
3. [references/input-output-contract.md](references/input-output-contract.md)

Use [references/sources.md](references/sources.md) only for provenance audits.

## Hard boundary

Own the semantic storyline register, segments, unit matrix, connections,
convergence/split points, event placement, activation disposition, chapter-level
story responsibility, and subject reconstruction test. Chapter-level design
means what the chapter must express and which lines it advances; it does not
mean scenes, beats, dialogue, sensory detail, POV execution, or prose. Do not
create a new storyline fact or event; do not decide inner character change,
POV, reveal timing, pacing, scene action, or prose.

Inventory rows are navigation, not storyline count. Derive actual storylines
from authoritative object types and values. A melody line may remain optional;
never inflate it into a mandatory subplot to make the output look rich.

## Execute

1. Accept only a sealed HS1 gate with ordered upstream `[HB0, HA1]`.
2. Complete every projected HDD before generating choreography candidates.
3. Stop with `blocked/author_required` if any disposition is `required_now`.
   Also stop with `blocked/author_required` when two or more sealed source controls are mutually incompatible and at least one is author-locked. Record each contradiction in `generation-session.json.author_required_claims`; never repurpose an unrelated projected `must_ask` control to carry the conflict.
4. Follow the five evidence files and the stage SOP.
5. Write exactly `canonical.json`, `generation-session.json`, and the five
   ordered files under `generation-evidence/`.
6. Run:

   ```powershell
   python scripts/run_skill.py <work-order.json> <draft-directory>
   ```

7. Require both exit code zero and a top-level ready result.

The script verifies set coverage, references, package truth, and parent
consumability. It cannot decide whether connections are narratively meaningful;
the adversarial self-review and HQ1 must do that with object evidence.

## Completion rule

Every authoritative line has exactly one authorized disposition. Every placed
line has segments, every connection resolves, the main trunk is continuous,
and mandatory lines have establishment, development, turn, and payoff or a
legitimate open state. Every HA1 chapter shell has exactly one HS1 chapter
design, and its primary/supporting/background/open roles agree with the sealed
segment placements. Candidate faults produce a revise package; author needs
produce a blocked package without completion.
