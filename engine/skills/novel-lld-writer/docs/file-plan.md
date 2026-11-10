# File Plan

## Runtime Skill

- `SKILL.md`: main skill instructions, hard contract, boundary rules, workflow, and review rubric.

## Lifecycle Docs

- `docs/design-brief.md`: mission, responsibilities, non-responsibilities, contracts, done criteria, and risks.
- `docs/file-plan.md`: file layout and ownership.
- `docs/evaluation-spec.md`: objective and semantic evaluation rules.
- `docs/test-plan.md`: validation commands and expected fixture behavior.

## Scripts

- `scripts/validate_lld_structure.py`: objective structural validator for LLD artifacts.

## Tests

- `tests/fixtures/positive-lld.md`: should pass.
- `tests/fixtures/negative-prose-lld.md`: should fail because it drifts into prose/full dialogue.
- `tests/fixtures/boundary-missing-hld-lld.md`: should fail because the required HLD inheritance packet is missing.

## References

- `references/sources.md`: method references from internet research and how they map into LLD-level responsibilities.

## Ownership Rules

- Runtime behavior belongs in `SKILL.md`.
- Method expansion belongs in `references/sources.md`.
- Objective gates belong in `scripts/validate_lld_structure.py`.
- Evaluation expectations belong in `docs/evaluation-spec.md`.
- Fixture expectations belong in `docs/test-plan.md`.
