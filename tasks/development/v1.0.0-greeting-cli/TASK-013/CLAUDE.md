# TASK-013 CLAUDE.md

## Current task

Implement and verify the H1-C V2 deterministic offline HTML renderer.

## Required reading

1. `docs/ai-novel-workflow/conception-autonomous-workflow-v2.md` §11.4, §3.8–§3.9, §14–§15, §16 item 13
2. `skills/novel-conception-review-html-generator/SKILL.md`
3. `skills/novel-conception-review-html-generator/references/v2-html-contract.md`

## Boundaries

- Treat the validated H1-A report as the only content source.
- Call the formal H1-A assembly validator; never replace it with a production mock.
- Render without rewriting, adding, summarizing, or inferring conception content.
- Keep the document offline, scriptless, form-free, external-resource-free, and decision-neutral.
- Advance only `assembled -> rendered`.
- H1 completion and `completed` belong to TASK-014.
- Keep legacy code isolated from V2 admission and completion.

## Verification

Run H1-C V2 tests, isolated legacy HTML tests, V2 static contract tests, and relevant real H1-A/H1-B integration tests.

## Handoff

Report production paths, independent verification, SHA-256 hashes, package evidence, and remaining blockers. Do not claim root acceptance or H1 completion.
