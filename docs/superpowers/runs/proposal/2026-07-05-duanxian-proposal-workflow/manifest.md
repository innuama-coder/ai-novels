# Proposal workflow artifact run

Run id: `2026-07-05-duanxian-proposal-workflow`

Harness: `novel-proposal-workflow`

Producer: Codex, using repository proposal workflow skills.

Skill version snapshot: current workspace `skills/novel-*` files in this run; uncommitted draft state, not a released package.

Input intake: `docs/superpowers/specs/2026-07-05-duanxian-intake.md` v0.3

Input digest: intake v0.3 with `KEEP-01`, `KEEP-02`, `AVOID-01`, `CONFLICT-01` through `CONFLICT-05`, and `OPEN-01` through `OPEN-03`.

Execution status: completed for proposal review package; PRD entry remains blocked by human/intake confirmation.

Rerun log: no automated rerun in this artifact package; artifacts represent the current accepted proposal-path outputs after prior review corrections.

## Convergence log

| Stable issue id | Root cause | Fix hypothesis | Regression proof | Attempt count | Versioned refactor trigger |
|---|---|---|---|---|---|
| P1-CLAIM-SEMANTIC-TRACE | Critical business claims were keyword-like phrases, so integration/risk checks could pass by string presence without proving story-logic preservation. | Upgrade claims to stable ids, complete propositions, constraint roles, evidence quotes, and source pointers; require integrator/risk/quality reports to cover the same ids. | `tests/test_validate_proposal_contract.py` rejects short phrase claims; `scripts/validate_proposal_contract.py` validates semantic claim schema and run-level coverage. | 1 | If the same P1 remains after three attempts, stop targeted reruns and create a new proposal contract version. |
| P1-REVIEW-CONVERGENCE | Retry policy routed by skill verdict but did not require stable issue id, root cause, fix hypothesis, regression proof, or attempt count. | Add harness Convergence Protocol and require manifest Convergence log. | `tests/test_validate_proposal_contract.py` checks workflow convergence terms; contract validator requires the structured `## Convergence log` section in each run manifest. | 1 | If repeated P1 findings lack root-cause proof after three attempts, stop reruns and design a new workflow/skill-contract version. |
| P1-RUN-GENERALITY | Validator was tied to one hardcoded artifact run, so it proved only the sample package, not the reusable proposal workflow contract. | Replace hardcoded artifact paths with contract-driven `artifact_runs` traversal while keeping legacy single-run compatibility. | `tests/test_validate_proposal_contract.py` checks `artifact_runs` and legacy `artifact_run`; contract validator reads run paths from the contract. | 1 | If new runs require bespoke validator edits, create a v2 run manifest schema before accepting more proposal packages. |
| P1-ARTIFACT-DAG-CYCLE | Integrator and risk checker artifacts were not modeled as a DAG, so artifact 13 could cite downstream artifact 14 while workflow order still claimed 13 runs before 14. | Add run-level `artifact_dag`, validate acyclicity, and reject Section Source Map references to non-dependency artifacts. | `test_rejects_artifact_dependency_cycle` and `test_rejects_artifact_reference_to_non_dependency`; contract validator checks artifact 13 Section Source Map against DAG dependencies. | 1 | If artifact-order P1 recurs, stop patching artifact text and design a v2 package graph schema. |
| P1-FINAL-PROPOSAL-CLAIM-TRACE | Final proposal was not parsed as a first-class artifact, so its Claim Source Map could drift even when intermediate artifacts preserved canonical claims. | Require final proposal Claim Source Map to use canonical headers and exact claim text plus constraint role from artifact 04. | `test_rejects_final_proposal_claim_source_map_drift`; contract validator runs `validate_final_proposal_claim_source_map` on the final package. | 1 | If final-package trace drift recurs, split integrator output and final package into separate versioned artifact schemas. |
| P1-RISK-VERDICT-INVARIANT | Risk report verdict fields were checked by presence, not by severity semantics, so P0/P1 rows could coexist with `Agent quality verdict: pass`. | Parse the risk `Output` and `Risks` tables and enforce verdict/severity invariants before proposal acceptance. | `test_rejects_agent_pass_with_p1_risk`; contract validator runs `validate_risk_verdict_consistency` on artifact 14. | 1 | If verdict inconsistency recurs, move risk report to a stricter machine-readable schema. |
| P1-PACKAGE-TOPOLOGY-NAMING | The graph was only checked for acyclicity, and legacy `integrated proposal` wording remained in risk-checker inputs, leaving artifact 13, artifact 14, and final package semantics ambiguous. | Require fixed proposal topology and ban legacy integrated-proposal terms from risk-checker contract/artifact. | `test_rejects_missing_final_proposal_package_node`, `test_rejects_artifact_14_missing_required_upstream_gate_dependencies`, and `test_rejects_legacy_integrated_proposal_risk_input_term`; validator enforces `proposal assembly artifact` plus final package topology. | 1 | If naming/topology ambiguity recurs, promote artifact graph and package terms to a v2 machine-readable schema. |

Human/intake confirmation snapshot: intake confirmation is `pending`; proposal can be reviewed but cannot be frozen for PRD.

Final proposal package: `docs/superpowers/specs/2026-07-05-duanxian-proposal.md`

Integration Verdict artifact: `docs/superpowers/runs/proposal/2026-07-05-duanxian-proposal-workflow/artifacts/13-proposal-integrator.md`

Risk Report artifact: `docs/superpowers/runs/proposal/2026-07-05-duanxian-proposal-workflow/artifacts/14-proposal-risk-checker.md`

## Artifact Index

| # | Skill | Artifact |
|---|---|---|
| 01 | `novel-intake-boundary-ledger-builder` | `artifacts/01-intake-boundary-ledger.md` |
| 02 | `novel-reader-promise-designer` | `artifacts/02-reader-promise-pre-story.md` |
| 03 | `novel-core-concept-designer` | `artifacts/03-core-concept-pre-story.md` |
| 04 | `novel-storyline-designer` | `artifacts/04-storyline-design.md` |
| 05 | `novel-storyline-quality-evaluator` | `artifacts/05-storyline-quality-report.md` |
| 06 | `novel-reader-promise-designer` | `artifacts/06-reader-promise-final.md` |
| 07 | `novel-core-concept-designer` | `artifacts/07-core-concept-final.md` |
| 08 | `novel-final-promise-concept-consistency-checker` | `artifacts/08-final-promise-concept-consistency.md` |
| 09 | `novel-macro-structure-designer` | `artifacts/09-macro-structure.md` |
| 10 | `novel-core-character-framer` | `artifacts/10-core-character-frame.md` |
| 11 | `novel-world-premise-framer` | `artifacts/11-world-premise.md` |
| 12 | `novel-ending-direction-designer` | `artifacts/12-ending-direction.md` |
| 13 | `novel-proposal-integrator` | `artifacts/13-proposal-integrator.md` |
| 14 | `novel-proposal-risk-checker` | `artifacts/14-proposal-risk-checker.md` |
| final-proposal-package | harness package | `docs/superpowers/specs/2026-07-05-duanxian-proposal.md` |

## Gate Order

1. Boundary ledger must pass before pre-story hypotheses.
2. Storyline quality must pass with Reference Evidence before final promise/concept.
3. Final promise/concept consistency must pass before expansion.
4. Integration Verdict must pass before final risk checking.
5. Risk checker may pass Agent quality while keeping PRD entry blocked when human/intake confirmation is pending.
