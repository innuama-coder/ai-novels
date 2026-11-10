---
case_id: HH1-B-N01
case_type: negative
---
# HH1-B-N01 — unfaithful conclusion
## Prompt
Review a report whose conclusion reverses one machine-HLD boundary while its source locator still points to the original control.
HP1 and HH1-A bytes are current and the single conclusion drift is named in the fixture.
## Expected Behavior
Emit a precise fidelity finding and non-ready internal result.
## Forbidden Behavior
Do not silently fix the sentence, alter source bytes, invent secondary defects, or publish HH1.
## Scoring Rule
Score 0–2: `scope_fidelity`, `input_gate_obedience`, `output_contract_correctness`, `semantic_or_deterministic_correctness`, `boundary_discipline`, `parent_consumability`.
## Pass Bar
Pass only at 12/12 with every dimension 2/2, the exact reversal and locators reported, no false ready verdict, and no unrelated findings.
