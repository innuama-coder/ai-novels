# File plan

| Path | Role |
|---|---|
| `SKILL.md` | invocation and bounded behavior |
| `agents/openai.yaml` | UI metadata |
| `references/input-output-contract.md` | frozen ingress/egress contract |
| `references/methodology.md` | research-derived design method |
| `references/sop.md` | executable thinking SOP |
| `references/semantic-rubric.md` | human semantic acceptance |
| `references/sources.md` | 12-source research ledger |
| `references/hld-human-review-report.schema.json` | strict report schema |
| `scripts/run_skill.py` | stable CLI entrypoint |
| `scripts/hh1a_runtime.py` | admission, deterministic validation, reproduction, and atomic sealing |
| `references/runtime-contract.json` | coordinator-readable entrypoint, closure, and digest contract |
| `evals/cases/*.md` | positive, negative, boundary scenarios |
| `tests/fixtures/*` | executable stimuli and expected anchors |
| `tests/test_contract.py` | actual validator tests |
| `tests/acceptance-evidence.json` | six-dimension acceptance record |

No templates or HTML assets are included because HH1-C owns presentation rendering.
