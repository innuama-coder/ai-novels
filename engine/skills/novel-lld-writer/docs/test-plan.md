# Test Plan

## Runtime

Use the bundled Python runtime:

```powershell
C:\Users\54256213\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe
```

## Positive Fixture

Command:

```powershell
C:\Users\54256213\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe skills\novel-lld-writer\scripts\validate_lld_structure.py skills\novel-lld-writer\tests\fixtures\positive-lld.md --json
```

Expected:

- exit code `0`
- status `pass`

## Negative Fixture: Prose Drift

Command:

```powershell
C:\Users\54256213\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe skills\novel-lld-writer\scripts\validate_lld_structure.py skills\novel-lld-writer\tests\fixtures\negative-prose-lld.md --json
```

Expected:

- non-zero exit code
- status `fail`
- at least one `forbidden_content` failure

## Boundary Fixture: Missing HLD

Command:

```powershell
C:\Users\54256213\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe skills\novel-lld-writer\scripts\validate_lld_structure.py skills\novel-lld-writer\tests\fixtures\boundary-missing-hld-lld.md --json
```

Expected:

- non-zero exit code
- status `fail`
- at least one `missing_required_section` failure

## Regression Rule

If the positive fixture fails, fix the skill, fixture, or validator before shipping. If either negative fixture passes, strengthen the validator or fixture before shipping.
