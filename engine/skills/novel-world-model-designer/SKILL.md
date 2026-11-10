---
name: novel-world-model-designer
description: Build and validate the W1 world-model package from ready B0 and S1 packages. Use when projecting storyline world requirements into sourced rules, eight structured world facets, institutions, operating systems, flows, support coverage, and E1 environment demands through the controlled five-phase W1 runtime.
---

# Novel World Model Designer

Create a traceable world model that can carry every approved S1 storyline without deciding E1 topology, event chronology, or character profiles.

## Required references

Read these before producing W1:

- [W1 schema](../../engine/docs/ai-novel-workflow/contracts/autonomous-v2/world-model.schema.json)
- [W1 runtime contract](references/runtime-contract.md)

## Controlled workflow

1. Verify ready B0 and S1 packages and use the coordinator-issued W1 input gate.
2. Call `start_w1_session()` once in the Agent's `CODEX_THREAD_ID`.
3. Author and submit these phases in order with `submit_w1_phase()`:
   `requirement-projection`, `world-rules-and-history`, `systems-and-flows`,
   `cross-line-world-test`, and `final-world-model`.
4. Treat every successful phase as sealed. If an earlier projection changes,
   start a fresh session instead of rewriting evidence.
5. Call `run_w1()` only after all five phase gates pass. Use
   `validate_w1_package()` for read-only package verification.

Every phase is cumulative. P1-P3 validate their own source and semantic
obligations before writing evidence. P4 is assembled with the sealed P1-P3
projections and receives full-model validation before its evidence is sealed.
P5 must be the exact projection of sealed P1-P4 and must pass full validation.

## Current contract obligations

- Set canonical model `schema_version` to `2.1` and `contract_revision` to
  `2026-08-11`. Version `2.0` is legacy-only.
- Preserve S1 `world_requirements` exactly as `storyline_requirements`.
- Give each rule a valid `source_ids` link to at least one world requirement.
- Give each institution and system `source_requirement_ids`. Institutions also
  define `world_position`, `interests`, `dependencies`, `conflicts`, and
  `intervention_scope`. `dependencies` and `conflicts` are both present; either
  may be empty, but they cannot both be empty.
- Give every one of the eight world facets structured entries containing a
  substantive `claim`, `requirement_ids`, and `rule_ids`.
- Cover every requirement with at least one rule and one system. Institution
  coverage is optional per requirement.
- Use `claim_coverage` to cover exactly the source requirement's
  `required_capability`, every constraint and acceptance check, and
  `downstream_freedom`. Each record binds source pointer/hash to a realization
  ID/pointer with a disposition and rationale.
- Use the fixed dispositions: required capability `realized`, constraints
  `constrained`, acceptance checks `tested`, and downstream freedom
  `deferred_to_downstream`.
- Give every E1 demand nonempty `macro_geography`, `institution_facility`,
  `spatial_relations`, and `plot_carriers` dimensions.
- Treat those four dimensions as a current W1-local schema extension. Do not
  add them to the shared canonical handoff schema; legacy W1 demands retain the
  historical handoff shape.
- Keep all governed entity and flow IDs globally unique. Resource flows may
  have several sources for one target; authority-flow targets have one owner;
  exact duplicate edges are invalid.
- Bind package freshness to W1's deterministic implementation dependency
  registry. Later E1/T1/C1 schema changes do not stale W1; changes to W1 or an
  upstream validator that W1 executes do.
- Provide fresh derivations for rules, systems, and support records. Never
  reference an `author_open` ID from an implementation-bearing rule, decision,
  support, or derivation field. Only the authority partition and corresponding
  open item may retain it.

Legacy ready packages require a 2.0 model, a revision-free historical session
and evidence chain, and a package-bound runtime/world-schema digest pair from
the trusted legacy allowlist. A bare 2.0 model can be checked only for migration;
it is not package-ready provenance. Do not label new packages as legacy.

## Boundary

W1 owns world scope, rules, history pressure, institutions, systems, resource,
authority and information mechanisms, and E1 requirements. It must not create
concrete environments or functional zones, event timelines or events, or
character profiles. Return author decisions outside W1 authority to I2/B0.
