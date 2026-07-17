# DP-HLD-001 HLD Contract And Validator Design

## Source Refs

- `tasks/design/hld/2026-07-07-duanxian-hld-design-planning/design-task-package.md`
- `docs/superpowers/plans/2026-07-07-novel-hld-workflow-refactor.md`
- `docs/superpowers/runs/prd/2026-07-07-duanxian-prd-workflow/artifacts/final-prd-package.md`

## Scope Boundary

This task designs the HLD contract JSON and validator behavior only. It must not generate HLD world rules, characters, environments, events, threads, style, POV, or final HLD prose. It also must not implement runtime product code. The design result describes the files, schemas, validation functions, negative fixtures, and regression expectations needed before HLD workflow implementation begins.

## Control Flow

The validator first reads the HLD contract JSON, then reads workflow and skill files, then checks PRD gate behavior, artifact topology, source map closure, risk verdict consistency, and convergence semantics. It fails immediately on missing files or malformed structures. It continues collecting non-structural violations so a developer receives a complete report in one run.

## Data Flow

Inputs are the HLD contract JSON, `skills/novel-hld-workflow/SKILL.md`, the twelve independent skill files, PRD risk report, PRD final package, and planned blocked/pass fixtures. The validator transforms these into normalized rule rows, artifact bindings, source refs, and verdict records. The output is a deterministic pass/fail report.

## Interface Contracts

`validate_hld_contract.py` exposes callable functions for entry gate, harness purity, artifact DAG, skill owner coverage, artifact schemas, Source Map preservation, risk verdict consistency, and convergence log structure. Tests import these functions directly and also execute the script as a command-line validator.

## State And Persistence

The contract is file-backed under `docs/superpowers/specs/2026-07-07-novel-hld-contract.json`. Validator fixtures live under `docs/superpowers/runs/hld/...` or a dedicated test fixture directory. No state is stored outside the repository.

## Error Handling And Diagnostics

Every P0/P1 contract violation includes stable rule id, expected value, actual value, and the affected file. Same-id fact rewrites must fail even when source refs are unchanged. Missing planned validator coverage must fail before claiming readiness.

## Security And Permissions

The validator is read-only except for normal test output. Do not implement code outside the planned validator and tests in this design task. Do not invoke network access or privileged commands.

## Observability

Regression tests cover blocked PRD gate, harness purity, artifact owner topology, schema presence, fact-level Source Map rewrites, unresolved P0/P1 verdict blocking, and convergence log semantics.

## Verification

The planned verification command is `python3 scripts/validate_hld_contract.py` plus `pytest tests/test_validate_hld_contract.py -q`. This document itself is verified by `tasks/design/validate_design_doc_quality.py`.

## Task Acceptance Mapping

| Planned acceptance item | Design response |
|---|---|
| fact-level binding checks are specified | The validator design requires Source Map preservation checks that compare upstream fact atoms with HLD fact atoms and fail same-ref rewrites. |
| negative fixtures are specified | The regression design includes negative fixtures for blocked PRD gate, malformed artifact topology, Source Map rewrite, unresolved P0/P1, and weak convergence rows. |
| planned validator functions map to contract rules | Each HLD contract rule is mapped to a named `validate_hld_contract.py::validate_*` function and a matching `test_validate_hld_contract.py::test_*` regression. |

## Validator Function Contract Matrix

| Function | Inputs | Pass condition | Fail condition | Diagnostic payload |
|---|---|---|---|---|
| `validate_hld_entry_gate` | PRD risk report, HLD run manifest | Blocked PRD produces only blocked manifest; passed PRD permits artifact execution. | HLD business artifact appears while PRD entry is blocked. | Rule id, PRD verdict, illegal artifact path. |
| `validate_harness_purity` | `skills/novel-hld-workflow/SKILL.md` | Harness verbs are limited to gate, dispatch, collect, route, package, and accept. | Harness text writes world, character, event, or prose facts. | Rule id, forbidden phrase, line context. |
| `validate_artifact_dag` | HLD contract JSON, skill output index | Artifact 01-12 dependencies match the topology in the design task package. | Missing dependency, reversed dependency, cycle, or artifact 12 feeding artifact 11. | Rule id, artifact id, expected and actual dependency sets. |
| `validate_artifact_schema` | Artifact Markdown text, required schema table | Required heading and columns are present in the owning artifact. | Missing heading, missing column, or wrong owner skill. | Rule id, artifact id, missing column list. |
| `validate_source_map_fact_preservation` | Final HLD Source Map, PRD scene/freeze/story facts | Each upstream fact atom is preserved or explicitly expanded without contradiction. | Same source id is reused while the fact atom changes meaning. | Rule id, source ref, upstream atom, HLD atom. |
| `validate_p0_p1_verdict_gate` | Artifact 12 risk report and verdict matrix | Any open P0/P1 blocks Agent quality pass and LLD entry. | Verdict says pass while an unresolved P0/P1 remains. | Rule id, risk id, severity, verdict field. |
| `validate_convergence_log_structure` | Artifact 12 convergence log | Every P0/P1 row has stable id, root cause, fix hypothesis, regression proof, attempt count, rerun target, and status. | Heading-only log, missing blocking semantics, or attempt count not increasing. | Rule id, stable issue id, missing field list. |

## Negative Fixture Matrix

| Fixture | Mutation | Expected failure |
|---|---|---|
| `blocked_prd_with_business_artifact` | Adds artifact 01 while PRD risk report still says `blocked_pending_human_review`. | `validate_hld_entry_gate` fails before downstream artifact validation. |
| `same_source_fact_rewrite` | Keeps `scene:PRD-S00` but changes death/failed handoff into successful handoff. | `validate_source_map_fact_preservation` reports upstream/HLD atom mismatch. |
| `integrator_depends_on_risk_checker` | Makes artifact 11 consume artifact 12. | `validate_artifact_dag` reports reversed dependency and cycle risk. |
| `p1_pass_verdict` | Leaves a P1 unresolved but writes `LLD entry verdict=pass`. | `validate_p0_p1_verdict_gate` reports verdict inconsistency. |
| `weak_convergence_log` | Provides only a heading or issue title. | `validate_convergence_log_structure` reports missing root cause, regression proof, and rerun target. |

## Contract Rule Traceability Matrix

| Contract group | Planned validator | Planned regression proof |
|---|---|---|
| Entry gate and blocked semantics | `validate_hld_entry_gate` | `test_hld_blocks_without_prd_pass_to_hld` |
| Harness purity and no business facts | `validate_harness_purity` | `test_harness_contains_no_business_design` |
| Artifact owner topology | `validate_artifact_dag`, `validate_artifact_schema` | `test_artifact_topology_and_owner_schema_are_closed` |
| PRD/freeze/story preservation | `validate_source_map_fact_preservation` | `test_same_source_scene_fact_rewrite_fails` |
| Risk verdict consistency | `validate_p0_p1_verdict_gate` | `test_unresolved_p0_p1_blocks_agent_quality_and_lld_entry` |
| Convergence protocol | `validate_convergence_log_structure` | `test_contract_rules_and_convergence_have_executable_proof` |

## Risks

The main risk is repeating the prior presence-only validator mistake. The design prevents that by requiring expected binding maps for every rule and negative tests for wrong-but-present bindings.

## Handoff

The developer receives a contract file path, validator function list, regression fixture list, and acceptance conditions. No HLD business generation is authorized by this design.
