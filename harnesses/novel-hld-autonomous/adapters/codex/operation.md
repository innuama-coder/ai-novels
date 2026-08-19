# Codex operation contract

This is the mandatory runtime path. The parent is a dispatcher and verifier; bounded skills own story reasoning.

## Bootstrap

1. Run `python harnesses/novel-hld-autonomous/tools/post_install_validate.py`.
2. Read `MANIFEST.runtime.yaml`, `agent.md`, `workflow.md`, `rules.md` and the current stage owner `SKILL.md` completely.
3. Create the run request and call the coordinator bootstrap CLI. Do not dispatch if its formal result is blocked or invalid.
4. Resolve the owner through `references/public-runtime-registry.json`; registry, skill contract and implementation digest must agree.

## Stage loop

For each coordinator-issued work order:

1. verify the work-order schema, input package manifests, hashes, owner, version, implementation digest and exact allowlist;
2. create a fresh Agent task identity and give it only the work order, sealed allowlisted inputs, current owner instructions and explicitly referenced shared contracts;
3. do not provide a canonical draft, expected answer, prior review conclusion or files outside the allowlist;
4. require the child to run its public entry point and return only its package plus package-external `stage-result.json`;
5. record the task identity and transcript; independently run deterministic validation in the parent context;
6. reject missing, extra, changed or unmanifested files and reject any result whose owner/version/digest does not bind to the issued work order;
7. pass the validated formal result to the coordinator/router and persist only the new immutable state artifact;
8. continue only when the router issues the next work order. On `needs_revision`, follow the formal revision topology. On `blocked`, emit the blocked report. On an author event, stop and wait for a sealed external answer event.

HQ2 consumer and fidelity tests use different fresh task identities and disjoint allowlists. HH1-A/B/C likewise remain independent; the deterministic publisher alone assembles their accepted outputs. HF1 may finalize only after an approved author-resolution artifact.

## Qualification mode

Qualification uses the same public path. A separate reviewer task scores the resulting artifacts; the producer may not review itself. Store fixture manifests, prompts, exact instruction files, producer/reviewer transcripts, deterministic validations, semantic review and products under one immutable evidence root. Generate the result envelopes and aggregate acceptance defined in `docs/agentic-qualification-contract.md`, then run its validator. A same-context rehearsal, declaration-only fixture or parent-authored draft is not qualification evidence.
