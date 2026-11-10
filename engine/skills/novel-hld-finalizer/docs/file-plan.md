# File plan

| Path | Role |
|---|---|
| `SKILL.md`, `agents/openai.yaml` | invocation and bounded behavior |
| `references/input-output-contract.md` | exact branch contracts |
| `references/methodology.md`, `sop.md`, `semantic-rubric.md` | deterministic closure method |
| `references/sources.md` | 14-source research ledger |
| `references/*.schema.json` | author event, completion, final validation schemas |
| `scripts/run_skill.py` | preflight/execute/validate CLI |
| `scripts/validate_package.py` | standard-library validation library |
| `evals/cases/*.md`, `tests/fixtures/*` | P01/N01/B01 evidence |
| `tests/test_contract.py`, `tests/acceptance-evidence.json` | bundled-Python release proof |

Approved runtime outputs: `hld-completion.json`, `final-validation.json`, `finalizer-execution.json`, `package-manifest.json`, plus external `stage-result.json`. Revise/rejected use their exact non-ready profiles.
