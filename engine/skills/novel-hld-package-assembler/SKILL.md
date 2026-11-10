---
name: novel-hld-package-assembler
description: Deterministically assemble the admitted HB0 baseline, seven accepted HLD design packages including HD1 chapter definitions, and passing HQ1 semantic review into the lossless HP1 machine package, cross-index, traceability matrix, and exact LWR-to-LWK LLD handoff. Use only for a sealed HP1 work-order. Never add, repair, reinterpret, summarize away, or revise story semantics.
---

# Novel HLD Package Assembler

## Mission

Seal the already-reviewed HLD into a reproducible machine package and exact LLD handoff. HP1 is a script skill: it packages and proves; it does not design.

## Read before execution

Read completely:

1. [references/input-output-contract.md](references/input-output-contract.md)
2. [references/sop.md](references/sop.md)

Read [references/methodology.md](references/methodology.md) when changing assembly logic and [references/sources.md](references/sources.md) when auditing its research basis. Read [references/integration-notes.md](references/integration-notes.md) before integrating HK1.

## Execute

From the repository root:

```powershell
python engine/skills/novel-hld-package-assembler/scripts/run_hp1.py <sealed-workspace>/work-order.json
python engine/skills/novel-hld-package-assembler/scripts/validate_hp1.py <sealed-workspace>/work-order.json
```

Exit codes:

- `0`: ready package is byte-reproducible and independently valid;
- `2`: upstream defect is durably blocked with no ready artifacts;
- `1`: runtime/configuration failure; no semantic verdict follows.

## Hard input rule

Accept only the work-order path. Require the exact current ready chain `[HB0, HA1, HS1, HC1, HI1, HR1, HK1, HD1, HQ1]`, sealed input-gate/state, exact owner implementation, empty unresolved projection, and role/path/SHA-256 allowlist. Every upstream manifest must close over its public ready profile, bind its main artifact and validation, and be bound by its completion. HQ1 must pass with zero findings.

## Ready output

The `HP1-package` contains exactly the fixed profile in [references/input-output-contract.md](references/input-output-contract.md), including lossless canonical copies, machine package, human-readable spec, cross-index, JSON/Markdown traceability, exact LLD handoff, execution, validation, manifest and completion. `stage-result.json` is package-external.

## Forbidden behavior

- Do not invent, repair, delete, merge, reinterpret or reprioritize story semantics.
- Do not turn HLD reference IDs into prose or infer lineage from ID prefixes.
- Do not accept `LWK-*` from HK1; HK1 owns `LWR-*`, HP1 projects the same suffix to `LWK-*` bijectively and records `source_lwr_id`.
- Do not resolve open items or HDDs; aggregate only the already-recorded dispositions under the fixed rule.
- Do not read outside the sealed allowlist or use ambient time/randomness.
- Do not place `stage-result.json` inside the content package.

## Done rule

Deliver only after the independent validator regenerates every byte from the same sealed inputs, validates schemas, profile closure, completion bindings, source/decision trace resolution, stable-ID uniqueness, authority equality and LWR↔LWK bijection.
