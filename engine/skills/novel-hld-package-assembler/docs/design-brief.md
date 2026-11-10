# Design brief

## Problem

Eight reviewed HLD packages must become one stable machine contract for LLD without losing provenance, introducing new story meaning or allowing a superficially valid envelope to hide changed bytes.

## Users

- HLD Harness scheduler: needs an exact ready/blocked result.
- LLD Harness: needs stable `LWK-*` units and complete constraints.
- Auditor: needs lossless canonical models, cross-index, trace and reproducibility evidence.

## Success

The same sealed inputs produce identical bytes; every upstream byte is closure-verified; every source/decision/work unit resolves; canonical models are unchanged; no semantic authoring occurs.

## Non-goals

Story improvement, source reinterpretation, HDD resolution, prose development, LLD scene/chapter design, scheduler state mutation and release archive construction.
