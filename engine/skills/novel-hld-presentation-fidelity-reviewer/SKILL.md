---
name: novel-hld-presentation-fidelity-reviewer
description: Independently review a sealed HH1-A human-review report against its bound HP1 HLD package for omission, weakening, enhancement, misattribution, visual-data drift, twenty-four-minute budget, and fixed decision retrieval. Use only from an HH1-B work order with a different task identity from the assembler. This skill never edits the report, judges story quality, reads HTML, or certifies rendering accessibility.
---

# Novel HLD Presentation Fidelity Reviewer

Operate as the bounded HH1-B thinking reviewer. HP1 is the semantic baseline; the sealed HH1-A report is the candidate. The harness owns routing and composite publication.

## Required reading

Read [input-output-contract.md](references/input-output-contract.md), [runtime-contract.json](references/runtime-contract.json), [sop.md](references/sop.md), [methodology.md](references/methodology.md), and [semantic-rubric.md](references/semantic-rubric.md) completely before review. Use [sources.md](references/sources.md) for method provenance.

## Execution

1. Admit only exact HH1-B ownership, the exact ordered allowlist in `runtime-contract.json`, a sealed HH1-A report/manifest/session/work-order, current HP1 package, matching HP1 hash, and a reviewer task ID different from the HH1-A producer task ID.
2. Create only `canonical.json` and `review-session.json`; record declared and actual reads as the complete ordered allowlist.
3. Read only current HP1, the sealed HH1-A report, its manifest, and HH1 operational state. Do not read conception, design-stage packages, chat, old reports, HTML, or renderer assets.
4. Follow the SOP: enumerate report elements; resolve bindings; compare facts, structures, relations, order, values, status, authority and open-item strength; reverse-check HP1 and sealed conception world/character/place definition coverage; verify visual model data; recompute the budget; answer ten fixed retrieval questions using report elements only; challenge cognitive overload.
5. Invoke the sole public entrypoint: `python scripts/run_skill.py <work-order.json> <draft-directory>`. It re-admits all bindings, checks verdict algebra and evidence, reproduces the package twice, and seals it atomically.
6. Exit `0` means ready, `2` means durable blocked/revise, and `1` means a runtime failure. Every ready result remains `composite_internal`, has a non-null internal manifest, and never contains a completion.

## Hard boundaries

- Do not modify, rewrite, compress, or repair the report or HP1.
- Do not fail different wording when its meaning, modality, attribution, and scope are unchanged.
- Do not judge whether the HLD is artistically good, dramatic enough, marketable, realistic, or faithful to raw conception.
- Do not let the assembler review its own work.
- Do not accept deletion of material controls as a budget remedy.
- Reject a nominal multi-city setting when any city lacks a distinct story function, concrete environment, key event, connected travel/information route, or ordinary-person portrait.
- Do not read or generate HTML/SVG/CSS/DOM/HUI data. HH1-C owns rendering and implementation accessibility.
- Do not read or review sample chapters or novel prose. HH1-B compares the HLD control report with HP1, not the later prose realization.
- Do not self-route, choose a final owner, write run-state, or publish HH1 completion.

## Done

Pass requires bidirectional material coverage; exactly five macro world-environment scopes covering every sealed author-locked world source; a connected network of at least four concrete cities, ordinary-person portraits covering every city, and a concrete season profile; exact one-card-per-source character and concrete-place definition coverage; exact one-card-per-chapter design coverage; zero material-drift and cognitive-overload findings; valid visual data; deterministic budget at or below twenty-four minutes; and ten report-only retrieval tests with resolvable HRE/HVG/source locators. Otherwise emit the correct internal non-ready result and evidence.
