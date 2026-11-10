# File plan

| Path | Role |
|---|---|
| `SKILL.md` | bounded reviewer behavior |
| `agents/openai.yaml` | UI metadata |
| `references/input-output-contract.md` | frozen HH1-B ingress/egress |
| `references/methodology.md` | evidence and fidelity method |
| `references/sop.md` | review procedure |
| `references/semantic-rubric.md` | human acceptance anchors |
| `references/sources.md` | independent research ledger |
| `references/presentation-fidelity-review.schema.json` | strict canonical schema |
| `scripts/run_skill.py` | stable CLI |
| `scripts/hh1b_runtime.py` | admission, evidence/verdict validation, reproduction, and atomic sealing |
| `references/runtime-contract.json` | coordinator-readable entrypoint, closure, and digest contract |
| `evals/cases/*.md` | P01/N01/B01 scenarios |
| `tests/fixtures/*` | executable stimuli |
| `tests/test_contract.py` | bundled-Python regression tests |
| `tests/acceptance-evidence.json` | six-dimension evidence |

No report template, HTML, CSS, SVG, or renderer fixture belongs here.
