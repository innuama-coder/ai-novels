# Harness file plan

| Area | Responsibility |
|---|---|
| `manifest.yaml`, `agent.md`, `workflow.md`, `rules.md` | Portable topology, behavior and invariants |
| `schemas/` | Closed data contracts for requests, state, results, packages, HDDs, revision and author gates |
| `runtime/` | Deterministic canonicalization, routing, state, HDD, revision, author gate and package logic |
| `validators/` | Static project and concrete-instance validation |
| `evals/` | Positive, negative, boundary and revision declarations |
| `adapters/codex/` | Runtime mapping without portable-core drift |
| `tools/build_release.py` | Validated source/runtime archive generation |
| `releases/`, `dist/` | Release notes and generated hash-bound artifacts |
