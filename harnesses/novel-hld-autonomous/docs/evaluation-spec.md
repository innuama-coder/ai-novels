# Harness evaluation specification

Each of the 14 bounded skills defines positive, negative and boundary cases. A fresh Agent must execute all 42; every case scores the six bounded dimensions from 0-2, and pass requires 12/12 with no blocker. The separate harness suite defines one positive full-chain case, one invalid-input case, one ownership-boundary case and two revision cases; it uses the seven harness dimensions and requires at least 12/14 with no blocker.

Structural acceptance additionally requires all schemas to compile, topology and owner matrices to agree, package profiles to close, adapters to declare support honestly, concrete deterministic instances to validate, and release construction to re-run validation. Structural acceptance never substitutes for the fresh-Agent evidence required by `agentic-qualification-contract.md`.
