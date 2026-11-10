# Acceptance evidence — 2026-08-06

## Outcome

HP1 passes its functional delivery gate. The prerequisite HB0 committed-reference defect found during integration was corrected and its regression passes.

## Automated evidence

Command:

```powershell
python -m unittest skills.novel-hld-baseline-admitter.tests.test_hb0_runtime skills.novel-hld-package-assembler.tests.test_hp1_runtime harnesses.novel-hld-autonomous.tests.test_package_envelope harnesses.novel-hld-autonomous.tests.test_owner_routing harnesses.novel-hld-autonomous.tests.test_schema_catalog -v
```

Result: 23 tests passed. Coverage includes:

- HB0 committed output refs resolve and contain no staging paths;
- HP1 clean-chain, HQ1 failure, invalid input LWK, unresolved boundary;
- lossless canonical copy, stable owner/source index, explicit trace resolution and LWR↔LWK bijection;
- non-main file hash drift, closure surplus and forged completion binding;
- byte reproduction, fixed package profile and package-external result;
- common acyclic completion closure, LWR/LWK owner routing and standard-library schema behavior.

Compilation command:

```powershell
python -m py_compile skills/novel-hld-package-assembler/scripts/hp1_runtime.py skills/novel-hld-package-assembler/scripts/run_hp1.py skills/novel-hld-package-assembler/scripts/validate_hp1.py skills/novel-hld-baseline-admitter/scripts/hb0_runtime.py
```

Result: pass.

## Contract evidence

- Fifteen primary sources with access date and absorbed method.
- Closed schemas for all six HP1 JSON deliverables; common schemas for manifest/completion/result.
- Three fixed-hash fixtures and P/N/B eval cases with five required sections, six dimensions and hard 2/2 each (12/12).
- Self-contained standard-library runtime; no `jsonschema` dependency.

## Known integration requirement

The HK1 producing contract must use `LWR-*`; any legacy `LWK-*` input remains intentionally blocked. Release portability for packaging all routed skills remains a Harness release task, outside HP1 semantics.
