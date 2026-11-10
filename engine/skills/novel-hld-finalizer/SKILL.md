---
name: novel-hld-finalizer
description: Deterministically close the novel HLD after the external author gate. Use only for a sealed HF1 work order with the complete current HB0-HH1 chain, HP1 handoff, HQ2 acceptance, HH1 review package, and current unconsumed author-decision event. Approved creates the sole HLD completion; revise losslessly projects the author event; rejected terminates through a blocked result. Never infer approval from chat, modify HLD, start LLD, or write return plans/run-state.
---

# Novel HLD Finalizer

Operate as the bounded HF1 script skill. The harness owns author-gate intake, routing, revision plans, state transitions, and LLD startup. HF1 only verifies and projects the sealed current facts.

## Required reading

Read [input-output-contract.md](references/input-output-contract.md), [sop.md](references/sop.md), [methodology.md](references/methodology.md), and [semantic-rubric.md](references/semantic-rubric.md) completely before execution. Use [sources.md](references/sources.md) for method provenance.

## Execution

1. Run `python scripts/run_skill.py preflight --work-order <work-order.json> --input-gate <input-gate.json>`.
2. Require exact upstream `[HB0,HA1,HS1,HC1,HI1,HR1,HK1,HD1,HQ1,HP1,HQ2,HH1]`, current run/revision, exact allowlist roles, no active return, and no pending/superseded revision plan.
3. Verify every completion, manifest, validation, canonical artifact and allowlisted input by SHA-256. Verify the external author decision is current, unconsumed, and binds HP1, HQ2, HH1 and HTML byte-for-byte.
4. For `approved`, revalidate HQ2 pass and current `lld-handoff.json`, then run `execute` to produce the approved package and sole top-level HF1 completion.
5. For `revise`, validate every target against cross-index/render registry and losslessly project the event into an external-author-request revise result. For `rejected`, emit author-rejected blocked evidence.
6. Run `python scripts/run_skill.py validate --work-order <work-order.json> --input-gate <input-gate.json> --workspace <sealed-workspace> --json`.

## Hard boundaries

- Do not infer approval, revision, or rejection from conversation text; only the sealed external event is authority.
- Do not modify HP1, HQ2, HH1, HTML, handoff, registry, cross-index, or author decision.
- Do not generate completion for revise or rejected.
- Do not generate LLD content or start LLD; completion only declares `next_stage=novel-lld`.
- Do not generate return requests, revision plans, active-return state, termination state, or run-state.
- Do not accept stale hashes, repeated/consumed decisions, unresolved target IDs, incomplete chains, or an HQ2 non-pass.

## Done

Approved is ready only when every current binding revalidates and the exact completion package validates. Revise/rejected are successful deterministic projections but never ready completions. Any uncertainty or mismatch fails closed with durable evidence.
