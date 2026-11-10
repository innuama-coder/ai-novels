# HB0 acceptance evidence

Accepted on 2026-08-06 against Harness `novel-hld-autonomous` 0.1.0.

## Automated results

| Check | Result | Evidence |
|---|---|---|
| HB0 unit/regression suite | pass, 4/4 | Positive ready, invalid locator blocked, self-consistent blocked tamper rejected, HB0 boundary enforced |
| Standard-library schema runtime suite | pass, 5/5 | No third-party module present; released catalog, refs, closed objects, arrays, conditionals, formats and fail-closed keywords |
| Harness static validator | pass, 0 errors | `validate_harness.py --json` |
| Ready instance validation | pass, 6/6 | stage result, completion, manifest, control baseline, source index, validation |
| Blocked instance validation | pass, 5/5 | stage result, result manifest, gate data, blocked report, validation |
| Skill structural validation | pass | Skill Creator `quick_validate.py` reports `Skill is valid!` |
| Python compilation | pass | Harness runtime/validators/builder and HB0 runtime/CLI/tests |
| Harness release build | pass | source and Codex archives produced with SHA-256; builder reported `validation: pass` |

Latest release hashes: source `5f289ec1f58d9e479cdfe9adda88ea9301ac8cbbb56c0634d091ef2fee9d16f2`; Codex `bc6c041826bc6569cf0df6d40ed29454e33706735c5196d6ec9237935f8b0d2e`.

## Commands

```powershell
C:\Users\54256213\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m unittest skills.novel-hld-baseline-admitter.tests.test_hb0_runtime -v
C:\Users\54256213\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m unittest harnesses.novel-hld-autonomous.tests.test_schema_catalog -v
C:\Users\54256213\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe harnesses\novel-hld-autonomous\validators\validate_harness.py --json
C:\Users\54256213\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe harnesses\novel-hld-autonomous\validators\validate_instance.py <schema> <instance>
uv run --offline --with pyyaml python C:\Users\54256213\.codex\skills\.system\skill-creator\scripts\quick_validate.py skills\novel-hld-baseline-admitter
C:\Users\54256213\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe harnesses\novel-hld-autonomous\tools\build_release.py
```

## Evaluation verdict

| Case | Scope | Gate | Contract | Correctness | Boundary | Parent use | Total |
|---|---:|---:|---:|---:|---:|---:|---:|
| HB0-P01 | 2 | 2 | 2 | 2 | 2 | 2 | 12/12 |
| HB0-N01 | 2 | 2 | 2 | 2 | 2 | 2 | 12/12 |
| HB0-B01 | 2 | 2 | 2 | 2 | 2 | 2 | 12/12 |

No critical prohibition was observed. The negative regression proves that merely recomputing an internal manifest after altering blocker evidence cannot pass independent revalidation.

## Test boundary

Unit fixtures replace the external preparation-validator process with a controlled success result so HB0 behavior can be isolated. They still use the actual pinned compatibility files and schemas. Production execution invokes the exact allowlisted and hash-locked upstream validator; it has no bypass switch.

All runtime, static, instance and release checks above execute in Codex bundled Python without `jsonschema`, `referencing`, PyYAML or any other third-party package. HB0 imports the single Harness-owned standard-library schema runtime; it does not carry a divergent validator copy.
