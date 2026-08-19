# HLD Coordinator Contract

The coordinator is the only control-plane writer. It issues one work order at a time, admits one byte-bound result, appends immutable state and ledger snapshots, and selects the next legal transition. It never performs a bounded skill's semantic work and never writes legacy workflow state.

## Bootstrap and forward topology

`init-staged` accepts one staged `hld-run-request.json` plus the exact HB0 allowlist, writes `states/revision-000.json`, and issues HB0. A ready top-level result is accepted only when its work-order identity, state-before reference, manifest, validation, completion, upstream bindings and package profile all revalidate. The only forward topology is HB0 → HA1 → HS1 → HC1 → HI1 → HR1 → HK1 → HQ1 → HP1 → HQ2 → HH1 → HF1.

HQ2 and HH1 are isolated composites. The coordinator issues their internal tasks in the declared order and issues the sole composite publisher only after the prefix is complete or the first internal non-ready result occurs. Only the publisher can create a top-level HQ2/HH1 completion.

## Public runtime and allowlist authority

`references/public-runtime-registry.json` is a closed, exact-token registry. Before issuance, the coordinator resolves the public entrypoint and the implementation digest algorithm actually enforced by that skill. The registry is checked against the frozen stage owner registry and, where present, the skill's closed runtime contract and implementation closure. Missing, extra, reordered or drifting runtime declarations fail before issuance.

HH1-A and HH1-B input roles are derived in the exact order declared by their closed runtime contracts. The coordinator derives paths and hashes only from accepted completion and manifest references; it does not search directories.

## Revision and external transactions

A revise result creates one immutable revision plan and an append-only plan-state stream. Target groups are ordered by stable-ID owner topology. Rebuilt prerequisite stages run forward; the current target stage receives an immutable `return_binding` file. A root-cause fingerprint is counted only when its target group produces an admitted ready completion. A third completed automatic attempt with the same fingerprint exhausts the run.

If a target disappears, the coordinator supersedes the active group and opens a byte-bound author retarget question. The answer must select an allowed current ID with the same exact owner. Source-resolution answers and final author decisions must be external, current, unconsumed and bound to exact question/package bytes. A reality dependency creates a structured request owned by `conception-fact-research`.

Only an external approved author decision can issue HF1. Only an admitted ready HF1 `hld-completion.json` can set `lld_ready`.

## Persisted artifacts

- `coordinator/ledger-NNNN.json` and `coordinator-current.json`
- `states/revision-NNN.json`
- `work-order-NNNNNN-*.json` and `input-gate-NNNNNN-*.json`
- `results/result-NNNNNN-*.json`
- `composite/*-state-NNN.json`
- `revision-plans/*.json`, `revision-plan-state/*.json`, `return-bindings/*.json`
- `author-transactions/*.json`, `author-events/*.json`, `reality-transactions/*.json`

Every pointer is a workspace-relative path plus SHA-256. Existing snapshots, accepted packages, plans, results and external events are never rewritten.

## CLI

`runtime/run_coordinator.py` exposes `init-staged`, `accept-result`, `accept-author-answer`, `accept-author-decision`, and `supersede-active-group`. A successful command prints the new ledger path; contract or transition failures return exit code 2 without issuing a new legal work order.
