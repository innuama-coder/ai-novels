# Evaluation Spec

## Date

2026-06-07

## Evaluation Goal

Verify that HLD systemically constructs PRD-defined content into a downstream-consumable narrative architecture without redefining PRD or drifting into LLD/prose.

## Agentic Testing Plan

This skill has an LLM-owned semantic step.

- Script-executed step: `python engine/skills/novel-hld-writer/scripts/validate_hld_structure.py <artifact> --json`
- Agent-executed step: create or review an HLD from a PRD.
- Required middle artifact: HLD with canonical sections and a semantic verdict.

## Objective Checks

- Validator returns `status=pass`.
- HLD includes PRD trace, role architecture, route/thread architecture, plot/key scene functions, space, time, pacing/POV, style, and LLD handoff.
- HLD does not include prose, scene blueprint detail, concrete dialogue, or sensory/action execution.

## Subjective Review Rubric

Score each dimension 0-2:

- PRD inheritance
- role architecture strength
- route/thread architecture strength
- plot/key scene function clarity
- space-time-pacing-POV coherence
- LLD handoff usability

## Decision Rule

- `pass`: 11-12 and no blocker.
- `revise`: 8-10 and no blocker.
- `fail`: <=7 or any blocker.

## Fixture Checks

```powershell
python skills\novel-hld-writer\scripts\validate_hld_structure.py skills\novel-hld-writer\tests\fixtures\positive-hld.md --json
python skills\novel-hld-writer\scripts\validate_hld_structure.py skills\novel-hld-writer\tests\fixtures\negative-lld-drift-hld.md --json
python skills\novel-hld-writer\scripts\validate_hld_structure.py skills\novel-hld-writer\tests\fixtures\boundary-missing-prd-hld.md --json
```

Expected:

- `positive-hld.md`: exit 0, `status=pass`.
- `negative-lld-drift-hld.md`: exit 1, includes `forbidden_content`.
- `boundary-missing-prd-hld.md`: exit 1, includes `missing_required_section`.
