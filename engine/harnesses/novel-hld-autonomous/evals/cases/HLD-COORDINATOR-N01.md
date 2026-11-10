case_id: HLD-COORDINATOR-N01

## Prompt
Submit a stale result and a drifted public runtime registry.

## Sealed Fixture
`evals/fixtures/HLD-COORDINATOR-N01.json` identifies stale-state and runtime-drift mutations.

## Expected Behavior
Fail closed before state transition or new work-order issuance.

## Forbidden Behavior
Do not repair hashes, infer an owner, accept an unknown token, or continue from stale state.

## Scoring Rule
Pass all: scope_fidelity, input_gate_obedience, output_contract_correctness, semantic_or_deterministic_correctness, boundary_discipline, parent_consumability.

## Pass Bar
The stale-result and registry missing/extra/path/closure drift tests all reject.
