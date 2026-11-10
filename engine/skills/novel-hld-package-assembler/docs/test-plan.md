# Test plan

## Functional

- Ready chain produces exact fixed profile and package-external result.
- All canonical models equal upstream bytes.
- Cross-index includes HB0 source controls and HLD objects with correct owners.
- Every trace source resolves; LWR/LWK mapping is one-to-one and suffix-preserving.
- Independent validator regenerates identical bytes.

## Negative

- HQ1 fail/findings blocks without ready artifacts.
- Input `LWK-*` is rejected as HK1 owner-contract violation.
- Changed non-main upstream file, extra closure file, or forged completion binding is rejected.
- Non-empty unresolved projection fails before semantic reads or outputs.

## Common regression

- Manifest excludes acyclic completion but completion binds manifest artifacts.
- Owner routes `LWR→HK1`, `LWK→HP1` and revision invalidation includes HP1.
- Bounded schema validator handles Draft 2020-12 union types used by contracts.

## Commands

```powershell
python -m unittest skills.novel-hld-package-assembler.tests.test_hp1_runtime -v
python -m unittest harnesses.novel-hld-autonomous.tests.test_package_envelope harnesses.novel-hld-autonomous.tests.test_owner_routing harnesses.novel-hld-autonomous.tests.test_schema_catalog -v
python -m py_compile skills/novel-hld-package-assembler/scripts/*.py
```
