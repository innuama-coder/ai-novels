# Test plan

## Automated

- Run all tests with the bundled Python absolute path and no dependency installation.
- Parse validator imports; reject any non-standard-library dependency.
- Validate strict canonical schema including `additionalProperties:false`.
- Assert the seven fixed retrieval codes are set-equal.
- Assert pass has empty drift/overload findings, all dimension/retrieval/budget verdicts pass, and `defect_origin=none`.
- Assert fail maps to `blocked/upstream_defect`; revise maps to reviewer-local revise.
- Assert exact HH1-B package profile and external composite-internal result.

## Semantic

- P01 proves bidirectional coverage and source-locator resolution.
- N01 identifies changed prohibition strength and reversed visual relation.
- B01 proves style-neutrality and respects the no-HTML boundary.

Release requires all automated tests and all six-dimensional case scores to pass.
