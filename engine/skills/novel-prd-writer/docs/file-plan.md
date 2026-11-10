# File Plan

## Date

2026-06-07

## Target Dev Root

`engine/skills/novel-prd-writer`

## Existing Runtime File

| Path | Role | Action |
|---|---|---|
| `SKILL.md` | Runtime skill instruction | Harden with contracts, boundaries, review criteria, and references |

## Lifecycle Docs

| Path | Role | Action |
|---|---|---|
| `docs/design-brief.md` | Skill mission, type, contracts, done criteria | Add |
| `docs/file-plan.md` | File ownership and future change map | Add |
| `docs/evaluation-spec.md` | Objective and subjective evaluation model | Add |
| `docs/test-plan.md` | Positive, negative, boundary test plan | Add |

## Validation And Test Files

| Path | Role | Action |
|---|---|---|
| `scripts/validate_prd_structure.py` | Deterministic structure gate for generated PRD artifacts | Add |
| `tests/fixtures/positive-prd.md` | Positive fixture expected to pass structure validation | Add |
| `tests/fixtures/negative-hld-drift-prd.md` | Negative fixture expected to fail HLD drift checks | Add |
| `tests/fixtures/boundary-incomplete-prd.md` | Boundary fixture expected to fail missing-section checks | Add |

## Files Not Created

| Path | Reason |
|---|---|
| `skill/SKILL.md` | Existing repo convention keeps runtime skill at `engine/skills/novel-prd-writer/SKILL.md` |
| `releases/`, `dist/` | No packaging/release request in current scope |

## Ownership Rules

- `SKILL.md` owns runtime behavior and hard contract.
- `docs/` owns lifecycle and evaluation evidence.
- `scripts/validate_prd_structure.py` owns objective structure checks only; it must not claim to judge semantic PRD quality.
- `tests/fixtures/` owns deterministic validation examples and agentic review anchors.

## Change Constraints

- Preserve PRD/HLD/LLD boundary.
- Avoid market-demand framing.
- Keep references tied to fields, constraints, review dimensions, or blocker criteria.
- Do not add workflow-stage orchestration unless the skill is converted to a harness workflow.
