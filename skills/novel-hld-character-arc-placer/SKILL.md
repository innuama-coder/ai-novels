---
name: novel-hld-character-arc-placer
description: Build HC1's character and relationship arc placement from current HB0, HA1, and HS1 packages. Use only when novel-hld-autonomous issues an HC1 work order to place existing goals, beliefs, relationships, responsibilities, pressures, choices, costs, and consequences into authoritative story segments and events. Do not add character biography, appearance, abilities, information, feelings, relationships, scenes, or prose.
---

# Novel HLD Character Arc Placer

## Mission

Place already-authorized character and relationship change into the narrative
structure so later stages can reason about knowledge, continuity, and scene
functions without inventing motivation or agency.

## Required reading

Read completely, in order:

1. [references/methodology.md](references/methodology.md)
2. [references/sop.md](references/sop.md)
3. [references/input-output-contract.md](references/input-output-contract.md)

Use [references/sources.md](references/sources.md) only to audit provenance.

## Hard boundary

Own participation, arc state models, arc/relationship steps,
choice-cost-consequence links, event alignment, and
capability-information-permission checks. Place only character facts already
defined by conception authority. Do not complete missing appearance, biography,
social circle, relation, feeling, skill, knowledge, or new character slots.

Do not assume every character must transform. A flat or steadfast arc is legal
when authorized, but it still needs pressure, choice, cost, and an observable
effect on the story or other characters.

## Execute

1. Accept only a sealed HC1 input gate with ordered upstream
   `[HB0, HA1, HS1]`.
2. Assess all projected HDDs before forming arc candidates.
3. Stop with `blocked/author_required` when any item is `required_now`.
4. Follow the stage methodology and five evidence steps.
5. Write exactly `canonical.json`, `generation-session.json`, and the five
   ordered evidence files.
6. Run:

   ```powershell
   python scripts/run_skill.py <work-order.json> <draft-directory>
   ```

7. Require exit code zero and a top-level ready result.

The runtime checks contract facts, including core arc role coverage and
bilateral relationship states. It cannot prove psychological credibility;
adversarial review and HQ1 own that evidence-based judgment.

## Completion rule

Every core character has an authorized start -> pressure -> choice -> cost ->
result path, every change is tied to existing events and lines, relationships
show both parties' states, key results have responsible actors, and capability,
information, and permission support action. Candidate faults revise; missing
author authority blocks without candidate or completion.
