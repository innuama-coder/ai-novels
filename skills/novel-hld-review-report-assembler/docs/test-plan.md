# Test plan

## Automated

- Validate SKILL structure with the system skill validator.
- Compile both Python entrypoints.
- Run all tests with the bundled Python absolute path and no temporary dependency installation.
- Parse validator imports and reject any non-standard-library dependency.
- Run `unittest` against P01 and N01 fixtures.
- Recompute CJK, Latin, visual count, and reading minutes from report decision content.
- Check exact HH1-A ready profile including at least one `generation-evidence/*.json` and no top-level completion.

## Semantic

- Inspect P01 for conclusion-first wording and reversible HP1 traceability.
- Inspect N01 to prove `HUI-` and binding drift fail closed.
- Inspect B01 to prove the skill preserves controls rather than optimizing by omission.

## Release gate

All automated tests pass; all three scenarios score 2/2 on all six dimensions; no unresolved blocker remains.
