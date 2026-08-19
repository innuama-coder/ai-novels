# HB0 evaluation specification

## Cases

| Case | Fixture | Expected result | Critical prohibition |
|---|---|---|---|
| HB0-P01 | Valid locked baseline and resolvable sources | ready, exact six-file package, reproducible canonical artifacts | no control reinterpretation |
| HB0-N01 | One inventory locator cannot resolve | blocked with `HB0_LOCATOR_UNRESOLVED`, exact four-file package | no partial ready output |
| HB0-B01 | HB0 receives an unresolved projection | reject before writing output | no HDD or author answer |

Each case is scored on scope fidelity, input-gate obedience, output-contract correctness, semantic/deterministic correctness, boundary discipline and parent consumability. Each dimension is 0–2. Pass requires 12/12 and no critical prohibition.

## Executable acceptance

1. Run the HB0 unit suite; all tests must pass.
2. Run the Harness static validator; verdict must be `pass` with no errors.
3. Run the Harness instance validator against both generated ready and blocked fixtures when the complete chain fixture is available.
4. Run the release builder; it must re-run validation and produce a hash-bound release archive.

Self-consistent tampering is covered: changing blocked evidence and recomputing its internal manifest must still fail because validation regenerates the expected blocker envelope.
