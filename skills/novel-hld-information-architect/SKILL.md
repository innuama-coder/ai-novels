---
name: novel-hld-information-architect
description: Design the HI1 canonical POV, focalization, character and reader knowledge states, suspense chains, and reveal/payoff controls inside the novel HLD harness. Use only when a sealed HI1 work order supplies current HB0, HA1, HS1, and HC1 completions; block author-dependent questions, preserve source authority, and never write clue prose, dialogue, scene actions, or new story facts.
---

# Novel HLD Information Architect

Operate as the bounded HI1 thinking skill. The harness owns orchestration, state, return routing, author transactions, sealing, and parent consumption. This skill owns only the meaning of `narrative-information-architecture.json`.

## Required reading

Read these files completely before execution:

1. [input-output-contract.md](references/input-output-contract.md) for the hard package and field contract.
2. [sop.md](references/sop.md) for the mandatory reasoning sequence.
3. [methodology.md](references/methodology.md) for POV, knowledge, and suspense methods.
4. [semantic-rubric.md](references/semantic-rubric.md) for pass/revise/fail anchors.

Use [sources.md](references/sources.md) only when auditing why a method exists.

## Execution

1. Prepare an agent-authored draft directory containing exactly `canonical.json`, `generation-session.json`, and the five ordered files under `generation-evidence/`.
2. Execute `python scripts/run_skill.py <work-order.json> <draft-directory>`. The shared public Harness runtime validates the referenced input gate, exact owner, stage `HI1`, ordered upstream `[HB0,HA1,HS1,HC1]`, current bindings, exact allowlist, and `unresolved_projection[]` before semantic reads.
3. Execute the SOP in order. Form one deterministic `HDD-HI1-<source_id>` for every projected non-quality unresolved source before generating candidates. If any disposition is `required_now`, stop before creating a canonical candidate and emit the standard `blocked/author_required` package.
4. Generate only information-architecture decisions within actual `freedom`. Preserve `mandatory`, `open`, `must_ask`, `open_item`, upstream authority classes, and external resolution bindings.
5. Let the shared runtime publish the exact ready, local-revise, or author-required-blocked profile. Keep the single `stage-result.json` outside the content package.
6. The parent revalidates with the public `SchemaCatalog`, package profile, manifest/completion bindings, and result envelope; then apply the semantic rubric. Structural validation cannot prove POV legitimacy, knowledge provenance, fair inference, or suspense payoff.

## Hard boundaries

- Do not create or modify events, characters, relationships, environments, outcomes, or author-open answers.
- Do not write clue wording, memories, dialogue, inner monologue, actions, sensory material, or scene prose.
- Do not let a POV reveal knowledge it cannot perceive or legitimately infer.
- Do not use authorial concealment to make a character ignore naturally available knowledge.
- Do not change upstream canonical files, choose return owners, write run-state, or publish another stage's completion.
- Do not claim the whole HLD does not need an unresolved answer; HI1 may only assess HI1 dependency.

## Done

Done means the deterministic validator passes, the semantic rubric passes, the parent can determine exactly one next action from the package plus external `stage-result.json`, and all three eval cases meet six dimensions at 2/2. Otherwise return `revise`, `blocked`, or `runtime_error` evidence without a ready completion.
