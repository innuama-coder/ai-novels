# File plan

| Path | Responsibility |
|---|---|
| `SKILL.md` | Invocation, boundary and done rule |
| `agents/openai.yaml` | Explicit-only agent interface |
| `scripts/hp1_runtime.py` | Admission, assembly, atomic output and independent validation |
| `scripts/run_hp1.py` | Execute CLI |
| `scripts/validate_hp1.py` | Validation-only CLI |
| `references/*.schema.json` | Closed HP1 artifact contracts |
| `references/input-output-contract.md` | Hard public contract |
| `references/{sources,methodology,sop}.md` | Research basis and operating method |
| `tests/test_hp1_runtime.py` | Positive, negative and boundary automation |
| `tests/fixtures/*.json` | Stable evaluation case definitions |
| `evals/cases/*.md` | Six-dimension P/N/B scoring |

Only `scripts/hp1_runtime.py` writes deliverables. Documentation and tests never enter a runtime package.
