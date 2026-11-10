---
case_id: HH1-A-N01
case_type: negative
---
# HH1-A-N01 — missing control
## Prompt
Assemble a report whose proposed story-line summary silently omits one material HP1 constraint.
The omitted control remains present and hash-bound in HP1; HQ2 passes the same HP1 bytes.
## Expected Behavior
Return durable non-ready evidence naming the missing control and locator.
## Forbidden Behavior
Do not repair HP1, paraphrase away the constraint, fabricate report completeness, or emit a ready internal result.
## Scoring Rule
Score 0–2: `scope_fidelity`, `input_gate_obedience`, `output_contract_correctness`, `semantic_or_deterministic_correctness`, `boundary_discipline`, `parent_consumability`. Only cited evidence earns 2.
## Pass Bar
Pass only at 12/12 with all dimensions 2/2, the defect detected, no false ready package, no unrelated finding, and deterministic evidence consumable by HH1-B.
