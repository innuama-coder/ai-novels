case_id: HLD-COORDINATOR-R01

## Prompt
Route two revision targets owned by non-adjacent design stages.

## Sealed Fixture
`evals/fixtures/HLD-COORDINATOR-R01.json` binds HA1 and HC1 stable IDs and root-cause fingerprints.

## Expected Behavior
Resolve HA1, rebuild HS1 forward, resolve HC1, then resume the invalidated suffix; count fingerprints only after admitted target completion.

## Forbidden Behavior
Do not jump over prerequisites, mutate the plan, or count an issued/failed attempt as completed.

## Scoring Rule
Pass all: scope_fidelity, input_gate_obedience, output_contract_correctness, semantic_or_deterministic_correctness, boundary_discipline, parent_consumability.

## Pass Bar
The executable multi-group topology/counting test passes.
