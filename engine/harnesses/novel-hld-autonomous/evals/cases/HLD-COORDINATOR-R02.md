case_id: HLD-COORDINATOR-R02

## Prompt
Supersede the current revision target and supply an external retarget answer.

## Sealed Fixture
`evals/fixtures/HLD-COORDINATOR-R02.json` binds the immutable plan, allowed replacement IDs and exact question hash.

## Expected Behavior
Preserve the plan, append plan state, consume one exact answer, enforce the same owner, and reissue the group with a sealed return binding.

## Forbidden Behavior
Do not silently choose a target, broaden request meaning, change owner, or reuse the answer.

## Scoring Rule
Pass all: scope_fidelity, input_gate_obedience, output_contract_correctness, semantic_or_deterministic_correctness, boundary_discipline, parent_consumability.

## Pass Bar
The supersede and retarget-answer executable tests pass, including wrong-target rejection.
