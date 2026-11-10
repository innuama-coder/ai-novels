# HLD Methodology And Best Practices Reference

## Purpose

This reference supports the first version of the novel HLD independent skills. It turns public novel-writing methodology into operational SOP rules for HLD artifacts. It is not a story source and must not override proposal, PRD, freeze boundaries, or PRD story-logic rows.

## Methodology Summary

| Area | Best-practice conclusion | HLD implication |
|---|---|---|
| Story structure | A story becomes readable when causality, escalation, and turning points are explicit. | HLD must preserve PRD scene order and explain support mechanics instead of replacing scene facts. |
| Conflict | Conflict must be concrete, layered, and tied to character desire, risk, and opposition. | Character, event, thread, and information artifacts must show pressure, obstruction, consequence, and closure. |
| Character | Characters are defined by function, motivation, relationships, decision pressure, and arc. | HLD character design must explain why each actor exists and what information/action permission they have. |
| Worldbuilding | A believable world is constrained: institutions, rules, technologies, and social norms create story pressure. | HLD world rules must constrain action and support PRD scenes; decorative lore is rejected. |
| Setting | Setting is not a backdrop; it shapes action, mood, logistics, and available choices. | Environment rows must include function, spatial relation, and state change. |
| POV | POV controls information access, distance, reliability, and reader knowledge. | Style/POV rules must define permissions and prohibitions, especially around digital-life interiority. |
| Synopsis discipline | A usable design synopsis foregrounds the main chain, stakes, causality, and ending direction. | HLD integration must remain fact-level and source-backed, not a polished but untraceable rewrite. |

## Shared SOP

1. Start from the canonical upstream facts: PRD scenes, PRD freeze boundaries, HLD requirements, proposal claims, PRD story-logic boundaries, and reconciled inventory.
2. Convert each upstream requirement into an HLD support question before inventing any design fact.
3. Add only facts that explain, constrain, support, sequence, permission, exclude, or hand off upstream facts.
4. Treat character motive, relationship pressure, hidden information, and concrete risk as primary story drivers.
5. Reject decorative lore, moral abstraction, and theme-only explanation when it does not change action, knowledge, permission, or consequence.
6. Preserve source closure with structured refs only: `scene:PRD-Sxx`, `freeze:PRD-FREEZE-xx`, `hldreq:HLD-REQ-xx`, `claim:CLAIM-xx`, `storylogic:PRD-LOGIC-xx`, `inventory:INV-xx`.
7. Declare unresolved gaps as amendment requests or blocking issues; do not silently repair proposal or PRD facts.
8. Every artifact ends with a structured `## Skill Verdict`; the harness routes from verdicts and must not infer pass/fail from prose.

## HLD Quality References

Good HLD output has these traits:

| Trait | Standard |
|---|---|
| Causal | Every added fact changes what can happen, who can know it, or why a later scene becomes possible. |
| Bounded | Every fact has an allowed source and expansion mode. |
| Human-centered | Institutional and technical logic must ultimately pressure human motives, fear, desire, attachment, or self-protection. |
| Complete enough for LLD | The artifact gives LLD designers stable entities, permissions, constraints, event roles, and handoff targets. |
| Independently checkable | A reviewer can accept or reject the artifact without reading other artifact bodies except declared inputs. |

Bad HLD output has these traits:

| Anti-pattern | Rejection reason |
|---|---|
| Abstract theme replaces motive | It cannot drive scenes or decisions. |
| World lore expands without PRD support | It violates top-down control. |
| Same source id with changed fact | It breaks fact-level traceability. |
| Hidden information and usable intelligence collapse | It removes suspense and destroys PRD logic. |
| Digital life becomes the dead person resurrected | It violates the required identity boundary. |
| Integrator invents bridging facts | It hides missing business design inside assembly. |

## Artifact Rubrics

| Artifact | Good delivery standard | Blocking failure |
|---|---|---|
| Artifact 01 | Inventory covers every PRD scene, freeze, HLD requirement, story-logic boundary, proposal claim, and necessary entity with one provisional owner. | Missing required entity type, invented entity without source, or hidden design decision in entity name. |
| Artifact 02 | Support matrix turns every upstream fact into a precise required answer and owner without answering it early. | PRD scene/freeze/HLD/story-logic item lacks support row or owner is ambiguous. |
| Artifact 03 | World rules constrain action, authority, technology, institutions, and social pressure in ways that support PRD facts. | Rule is decorative lore, abstract morality, or rewrites PRD story logic. |
| Artifact 04 | Character system defines entity identity, function, concrete motive pressure, relationship pressure, information permission, and digital-life identity boundary for every required actor/group. | Character motive is replaced by theme/good-evil, or digital life is treated as the dead senior's resurrection. |
| Artifact 05 | Environment system defines source-backed inventory identity, spatial function, relation, state-change dimension, distinct before/after state tokens, and state change for every required place; later events explicitly record the exact state transition and a matching realization. | Accident, lab, organization, or digital enclosure lacks causal function, trace closure, state-transition or state-realization evidence, or event integration. |
| Artifact 06 | Event system binds every required event inventory identity to a concrete action, distinct narrative-function and visibility axes, source-backed cause refs, an acyclic predecessor chain, participants, environment state realization, and a changed consequence. | Event lacks inventory identity, action, causal role, consequence, predecessor closure, exact environment realization, or the major-event mechanics bypass the researcher/digital-life interaction required by PRD. |
| Artifact 07 | Time/information system gives every information object one inventory identity and canonical source fact, a story anchor, contiguous narrative reveal phase, acyclic predecessor graph, controlled disclosure tier and knowledge state, event action-bound reveal condition, and exact Source Map trace closure. | Information is duplicated, source atom is rewritten, story/reveal time is unspecified or cyclic, the reveal action differs from its event, condition refs are unresolved, the Source Map fact is missing or substituted, or usable intelligence and complete cause collapse into one reveal layer. |
| Artifact 08 | Thread system gives each main, hidden, emotional, institutional, identity, and theme line a type-specific function, resolved HLD design anchors, independently traced pressure, a substantive question, an ordered state-changing progression across HLD event/information nodes, connected structured crossover, and closure outcome. | Any core line is absent, has duplicate question/shared-only pressure, uses PRD scenes as HLD nodes, lacks resolved anchors or state-changing progression, is one-node/disconnected, is reduced to a label/enum, or invents a new plotline. |
| Artifact 09 | Style/POV rules cover POV, narrative distance, information access, digital-life interiority, dialogue, image system, prohibited expression, and language style; each uses a type-specific access policy, reader disclosure mode, resolved information/thread boundaries, type-specific behavior in structured `rule`/`scope`/`effect`, `focalizer`/`permitted`/`evidence`, and `forbidden`/`target`/`trigger` fields. Scope/target/evidence must resolve to the same row's declared boundaries, trigger must equal its disclosure mode, and focalizer must resolve to artifact 04; the language-style row defines `mode`/`limit`, `sentence`/`variation`, `prefer`/`avoid`, and `pace`/`shift` directives. | A required rule type is absent, a policy or disclosure mode is unbounded, execution fields cite a different or nonexistent information/thread/character fact, an execution field is free-form or behavior-generic, a language directive is incomplete or vague, POV enters unrestricted digital-life interiority, or concise Chinese atomic fields are padded into unreadable prose. |
| Artifact 10 | Reconciler reconstructs its subject register from inventory and declared amendments, binds every row to origin identity/source/fact trace, gives an accepted inventory entity one final id, resolves merges through a canonical accepted subject, blocks amendment minting, and preserves prior resolved ids on rerun. | A phantom subject, identity/source/owner drift, unbound merge, multi-id mint, amendment mint, rejected/unresolved amendment use, or final-id renumbering reaches integration. |
| Artifact 11 | Integrator emits fact-level HLD Source Map preserving upstream fact atom, HLD expansion, owner, inventory id, expansion mode, support mechanism, and LLD target. | Same source id rewrites upstream fact, or integrator adds unsupported business facts. |
| Artifact 12 | Integrity checker reports schema/source/business/verdict risks with severity, owner, rerun target, convergence row, and closed LLD entry state. | P0/P1 coexists with pass verdict or blocking risk lacks convergence coverage. |

## References

| Ref id | Source | Article | Method used |
|---|---|---|---|
| REF-01 | Reedsy | [Point of View: The Ultimate Guide to Writing POV (+ Examples)](https://reedsy.com/blog/guide/point-of-view/) | POV permission, distance, information access. |
| REF-02 | Reedsy | [Worldbuilding: Create Brave New Worlds [+Template]](https://reedsy.com/blog/worldbuilding-guide/) | Rule-bound worldbuilding and constrained fictional systems. |
| REF-03 | Reedsy | [Character Development: How to Create Fan-Favorite Characters in 5 Steps](https://reedsy.com/blog/character-development/) | Character motive, development, and reader investment. |
| REF-04 | Reedsy | [Story Structure: 7 Types All Writers Should Know](https://reedsy.com/blog/story-structure/) | Structural causality and turning-point awareness. |
| REF-05 | Reedsy | [How to Write a Novel: A Bestselling Author's Guide](https://reedsy.com/blog/how-to-write-a-novel/) | Planning discipline and end-to-end novel construction. |
| REF-06 | Reedsy | [7 Types of Conflict in Literature: A Writer's Guide](https://reedsy.com/blog/guide/conflict/types-of-conflict/) | Conflict categories and escalation design. |
| REF-07 | Reedsy | [How to Create the Ultimate Character Profile [+ Template]](https://reedsy.com/blog/character-profile/) | Character inventory fields and consistency checks. |
| REF-08 | Reedsy | [What is a Character Arc? 3 Common Types and Examples from Fiction](https://reedsy.com/blog/character-arc/) | Arc logic, change, stasis, and fall patterns. |
| REF-09 | Reedsy | [Narrative Structure: Definition, Examples, and Writing Tips](https://reedsy.com/blog/narrative-structure/) | Narrative order and structural framing. |
| REF-10 | Reedsy | [What Is the Setting of a Story? How to Write 3 Types of Settings](https://reedsy.com/blog/setting-of-a-story/) | Setting as action constraint and atmosphere/function system. |
| REF-11 | Jane Friedman | [How to Write a Novel or Memoir Synopsis](https://janefriedman.com/how-to-write-a-novel-synopsis/) | Concise causal synopsis and source-backed story presentation. |
