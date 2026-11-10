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
choice-cost-consequence links, event alignment,
capability-information-permission checks, and one explicit character-agency
contract for every HA1 chapter shell. Each chapter contract separates legal
focal characters, named decision makers, source-bound institutional decision
makers, cost bearers, unavailable characters, and
the information paths available to each focal character. Place only character facts already
defined by conception authority. Do not complete missing appearance, biography,
social circle, relation, feeling, skill, knowledge, or new character slots.
Participation `responsibilities[]` states only what a role is responsible for,
as a natural-Chinese duty sentence beginning with `负责` that an author can read
directly. It must not contain
unexplained English prose or restate death, survival, consciousness, recovery,
or other lifecycle status. Single-letter story names such as C, M, and R-07
remain legal. Chapter availability and lifecycle limits belong only in the
ordered chapter-agency contracts, where current HA1/HS1 structure can govern
them without stale baseline prose leaking back into the design.
Each duty is stated from inside the story world: what the person or institution
must do, protect, decide, verify, prevent, or deliver. Never substitute an
out-of-world narrative function such as moving the plot, creating suspense,
maintaining conflict, preserving a failure path, or paying off a setup.
For a return-resolution work order, the sealed return binding is the exact
coverage contract. A participation target group contains only
`HAS-PARTICIPATION-*` IDs; every affected ID appears once, in the sealed order,
and keeps its exact `CHR-*` identity. A chapter-agency target group contains
only `HAS-AGENCY-*` IDs; every affected contract must exist once and appear in
the sealed chapter order. When one upstream defect spans a chapter's
information authority and the character-arc step that uses it, HC1 also
accepts one narrowly defined combined group: ordered `HAS-AGENCY-*` targets
followed by ordered `HAS-ARC-*` targets. The combined form requires a sealed
accepted HC1 return base, and only those exact semantic objects may change.
The authority partition stays exact. Derivation-claim count, order, stable ID,
and target locator also stay exact; only a claim already targeting
`/chapter_agency_contracts` or `/arc_steps` may refresh its source refs and
value hash to prove the changed target collection, and the public source/hash
checks still apply. Every other derivation claim remains exact.
Participation mixed with any other family, reverse family order, missing,
renamed, reordered, duplicated, or unknown targets fail before output. Never
replace a requested stable object with a convenient role or a different
chapter contract.
When an HC1 package was previously accepted, the return work order also seals
that package as the return base. Only the affected target objects may change;
every unaffected chapter agency contract and every unrelated semantic array
must remain byte-for-value equivalent to that accepted base. A first-attempt
local revision has no accepted base and therefore carries no return-base refs;
a partial base is always invalid.
The deterministic gate checks this duty form and explicit lifecycle wording;
fresh semantic review must still reject euphemisms, hidden state claims, or a
duty that smuggles in design language or contradicts current HA1/HS1 authority.
Producer validation alone is not semantic acceptance.

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
information, and permission support action. Every HA1 chapter has one ordered
agency contract. A public-service, professional, or collective action may use
an institutional actor only when its role, responsibility, authority limit,
and chapter-local source refs are explicit. It must never be coerced into an
unrelated named character. An unconscious or absent character cannot be listed
as a focal character or decision maker. Candidate faults revise; missing
author authority blocks without candidate or completion.
