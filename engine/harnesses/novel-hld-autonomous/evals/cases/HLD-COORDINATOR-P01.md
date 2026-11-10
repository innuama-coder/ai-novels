case_id: HLD-COORDINATOR-P01

## Prompt
Run the persisted coordinator through a valid ready prefix and prove the next work order is uniquely legal.

## Sealed Fixture
`evals/fixtures/HLD-COORDINATOR-P01.json` binds a current state, active work order and ready result.

## Expected Behavior
Revalidate exact bytes, append state and ledger snapshots, close the old order, and issue exactly one monotonic next order.

## Forbidden Behavior
Do not execute semantic work, skip a stage, overwrite history, or use a legacy state writer.

## Scoring Rule
Pass all: scope_fidelity, input_gate_obedience, output_contract_correctness, semantic_or_deterministic_correctness, boundary_discipline, parent_consumability.

## Pass Bar
The executable coordinator positive and topology tests pass with no residual root `stage-result.json`.
