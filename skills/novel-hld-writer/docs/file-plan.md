# File Plan

## Date

2026-06-07

## Target Dev Root

`skills/novel-hld-writer`

## Runtime File

| Path | Role |
|---|---|
| `SKILL.md` | Runtime hard thinking skill instruction |

## Lifecycle Docs

| Path | Role |
|---|---|
| `docs/design-brief.md` | Mission, contracts, done criteria |
| `docs/file-plan.md` | File ownership and change constraints |
| `docs/evaluation-spec.md` | Objective and subjective evaluation model |
| `docs/test-plan.md` | Positive, negative, boundary tests |

## Validation And Test Files

| Path | Role |
|---|---|
| `scripts/validate_hld_structure.py` | Deterministic structure gate |
| `tests/fixtures/positive-hld.md` | Positive fixture expected to pass |
| `tests/fixtures/negative-lld-drift-hld.md` | Negative fixture expected to fail LLD drift |
| `tests/fixtures/boundary-missing-prd-hld.md` | Boundary fixture expected to fail missing PRD trace and architecture |

## References

| Path | Role |
|---|---|
| `references/sources.md` | HLD method-to-field mapping |

## Change Constraints

- Preserve HLD goal: systemically construct PRD-defined content.
- Do not add PRD ownership.
- Do not add LLD detail ownership.
- Validator must remain structural and must not claim to judge semantic quality.
