# Test Plan

## Date

2026-06-07

## Target

`skills/novel-hld-writer/SKILL.md`

## Test Strategy

Use both deterministic structure checks and agentic semantic review.

Deterministic command:

```powershell
python skills\novel-hld-writer\scripts\validate_hld_structure.py <artifact> --json
```

Use any Python 3 interpreter. If the Windows `python` shim times out, use the Codex bundled Python interpreter.

## Test Case 1: Positive HLD

Fixture: `tests/fixtures/positive-hld.md`

Expected: exit 0.

## Test Case 2: LLD Drift

Fixture: `tests/fixtures/negative-lld-drift-hld.md`

Expected: exit 1, forbidden scene blueprint/dialogue/sensory detail.

## Test Case 3: Missing PRD Trace

Fixture: `tests/fixtures/boundary-missing-prd-hld.md`

Expected: exit 1, missing required architecture sections.

## Agentic Review Checklist

- Does it inherit PRD constraints?
- Does it build role architecture?
- Does it build route/thread architecture?
- Does it define key scene functions without LLD detail?
- Does it include space/time/pacing/POV architecture?
- Does it hand off cleanly to LLD?
