# HB0 file plan

| Path | Purpose | Runtime critical |
|---|---|---:|
| `SKILL.md` | Agent-facing trigger, contract and execution rules | yes |
| `agents/openai.yaml` | Skill discovery metadata | yes |
| `scripts/hb0_runtime.py` | Admission, projection, packaging and independent revalidation | yes |
| `scripts/run_hb0.py` | Execution CLI | yes |
| `scripts/validate_hb0.py` | Existing-package validation CLI | yes |
| `references/input-output-contract.md` | Exact roles, file profiles and failure semantics | yes |
| `references/preparation-compatibility-lock.json` | Pinned upstream implementation and schema hashes | yes |
| `references/methodology.md` | Research-derived design rationale | no |
| `references/sop.md` | Operator procedure | no |
| `references/sources.md` | Auditable research register | no |
| `evals/cases/HB0-P01.md` | Ready-path evaluation | no |
| `evals/cases/HB0-N01.md` | Invalid-input evaluation | no |
| `evals/cases/HB0-B01.md` | Boundary evaluation | no |
| `tests/test_hb0_runtime.py` | Executable regression suite | no |

No asset directory is required. HB0 has no templates and does not generate prose.
