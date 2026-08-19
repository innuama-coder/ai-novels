case_id: HLD-COORDINATOR-B01

## Prompt
Return an author-required or reality-dependency blocked result.

## Sealed Fixture
`evals/fixtures/HLD-COORDINATOR-B01.json` selects both external blocker classes.

## Expected Behavior
Open a byte-bound author question or a structured reality research request and issue no bounded skill.

## Forbidden Behavior
Do not answer for the author, research facts, or treat an external dependency as a local revision.

## Scoring Rule
Pass all: scope_fidelity, input_gate_obedience, output_contract_correctness, semantic_or_deterministic_correctness, boundary_discipline, parent_consumability.

## Pass Bar
Both external transaction tests pass and active_work_order_ref is null while waiting/re-entering.
