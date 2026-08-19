# HB0 test plan

## Automated tests

- Positive: valid input produces the six-file ready profile; independent validation passes; canonical projections reproduce exactly; `stage-result.json` stays outside the package.
- Negative: unresolved RFC 6901 locator produces `HB0_LOCATOR_UNRESOLVED`, no ready artifacts and the four-file blocked profile.
- Tamper regression: blocked evidence with recomputed internal manifest is rejected after complete admission plus projection rerun.
- Boundary: an unresolved projection addressed to HB0 is rejected before any output is written.

## Cross-component tests

- Harness static validation checks topology, ownership, source access, package profiles, schemas, eval declarations and adapters.
- Harness instance validation checks a concrete workspace envelope, references, state and stage package.
- Release build re-runs static validation and packages only declared portable core and adapter files with checksums.

## Pass bar

All tests and validators pass with zero errors. Skips, expected failures, weakened schemas and manual waiver do not count as acceptance.
