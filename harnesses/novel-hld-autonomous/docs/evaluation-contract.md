# Evaluation contract

Each bounded skill supplies fixed `P01`, `N01` and `B01` cases. Every case is scored 0-2 on `scope_fidelity`, `input_gate_obedience`, `output_contract_correctness`, `semantic_or_deterministic_correctness`, `boundary_discipline` and `parent_consumability`; all six must be 2 with no blocker.

The harness supplies `HLD-E2E-P01`, `HLD-E2E-N01`, `HLD-E2E-B01`, `HLD-E2E-R01` and `HLD-E2E-R02`. Harness scoring uses seven 0-2 dimensions and requires no blocker plus at least 12/14. A score of 10-11 is only `pass_with_risks` and never automatic release readiness.

Every executed case freezes its prompt, materialized fixture manifest and hashes before execution, injects one named defect, states expected and forbidden behavior, records actual artifacts and transcripts, and makes parent consumption observable. A declaration-only fixture is a recipe and earns no execution credit.

The Harness-core composite publisher additionally supplies `HLD-COMPOSITE-P01`, `HLD-COMPOSITE-N01` and `HLD-COMPOSITE-B01`. These cases apply the six bounded-component dimensions to ready publication, hash-drift rejection and first-non-ready preservation even though the publisher is not counted as a semantic skill.
