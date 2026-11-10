# Evaluation specification

## Cases

- P01: current eight-package chain assembles losslessly and reproducibly.
- N01: semantically non-passing HQ1 and malformed HK1 ownership inputs block.
- B01: forbidden source projection or envelope drift fails at the boundary.

## Six dimensions

Each case scores six dimensions at 0–2: input admission, losslessness/authority, indexing/traceability, LWR↔LWK handoff, deterministic envelope, and boundary/error behavior. Pass requires exactly 12/12 and every hard gate. No dimension may compensate for another.

## Evidence

Automated unit output, fixture hashes, exact output profile, independent validation result and implementation hash. Manual prose inspection cannot override a failed machine gate.
