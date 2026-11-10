# HB0 implementation plan

## Implemented sequence

1. Load a work order and enforce owner, version, implementation hash, stage, mode, state and allowlist invariants.
2. Verify the compatibility lock against staged upstream validator, schemas and release metadata.
3. Re-run the exact upstream preparation validator.
4. Validate the baseline package, manifest closure, hashes, lineage, fixed HLD assignment and authority partition.
5. Resolve every source locator and verify canonical value hashes.
6. Project the control baseline, unresolved register and stage access index without inventing decisions.
7. Write a staged ready or blocked package and atomically publish it.
8. Write the top-level result outside the content package.
9. Independently reload inputs and regenerate the expected result before accepting delivery.

## Failure policy

- Invalid or drifting input becomes a typed blocked result.
- Harness misuse, output collision or corrupt existing output raises a runtime failure.
- No fallback parser, locator relaxation, silent merge or best-effort repair is permitted.

## Release condition

Implementation remains a candidate until all unit tests, Harness validators and release build pass and acceptance evidence records the exact commands and outcomes.
