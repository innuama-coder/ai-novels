# Evaluation Spec

## Date

2026-06-07

## Target Dev Root

`engine/skills/novel-prd-writer`

## Target Tests Path

`engine/skills/novel-prd-writer/docs/test-plan.md`

## Evaluation Goal

Verify that `novel-prd-writer` produces a hard, downstream-consumable novel PRD that defines direction, constraints, and standards without crossing into HLD, LLD, or prose writing.

## Evaluation Surface

- Artifact under evaluation: generated or revised novel PRD.
- Decision under evaluation: whether the PRD is `pass`, `revise`, or `fail`.

## Lifecycle Coverage

- Design-stage checks: hard contracts and lifecycle docs exist.
- Implementation-stage checks: `SKILL.md` includes type, trigger, input, execution, output, blocker, and review contracts.
- Testing-stage checks: positive, negative, and boundary cases exist.
- Release-stage checks: N/A - no release package in scope.

## Agentic Testing Plan

This skill has an LLM-owned semantic step.

- Script-executed steps: run `python engine/skills/novel-prd-writer/scripts/validate_prd_structure.py <artifact> --json`.
- Agent-executed step: generate or review a PRD from a test prompt.
- Exact middle artifact the agent must produce: a PRD with canonical sections and a semantic review verdict.
- Required procedure:
  1. Extract facts, assumptions, and unknowns.
  2. Produce PRD sections.
  3. Label Must / Should / Could / Won't.
  4. Reject HLD/LLD/prose drift.
  5. Self-review against the rubric.
- Process-fidelity review rule: fail if the agent jumps straight to plot outline, scene design, or prose.
- Artifact review rule: fail if the PRD lacks role, route, plot, setting, and style constraints.

## Objective Checks

- Required deterministic checks:
  - `scripts/validate_prd_structure.py` returns `status=pass`.
  - Output includes content requirement sections.
  - Output includes risks/open questions.
  - Output includes acceptance criteria.
  - Output does not include market metrics.
  - Output does not include scene-by-scene outline.
- Structural blockers:
  - no core concept
  - no role-route-plot constraints
  - no Must/Won't constraints

## Subjective Review Rubric

- Review target: generated PRD.
- Reviewer role: senior fiction development editor plus harness skill reviewer.
- Rubric dimensions:
  - Direction clarity: pass when the story center is reusable by HLD.
  - Constraint strength: pass when later design can be rejected for violating PRD.
  - Role-route-plot coverage: pass when the three core areas are explicit.
  - Boundary discipline: pass when no HLD/LLD/prose content appears.
  - Method traceability: pass when cited methods affect fields or rules.
  - Downstream consumability: pass when HLD can build without inventing the premise.
- Evidence expectations: cite the PRD sections that support each score.
- Decision rule:
  - `pass`: all dimensions pass.
  - `revise`: one or two weak dimensions, no blocker.
  - `fail`: any blocker or boundary violation.

## Review Procedure

Combined objective-plus-subjective path.

Caller-consumption rule:

- `pass`: PRD can feed HLD.
- `revise`: PRD must be patched before HLD.
- `fail`: return to intake or concept clarification.

The final conclusion depends on both process fidelity and artifact quality.

## Verdict And Status Model

N/A - no iterative round/status split.

The skill may revise output in the same run, but it does not own multi-round workflow state.

## Positive Case

Input: a rough concept with protagonist, setting, conflict, and style intent.

Expected: PRD defines content requirements, route and plot constraints, style boundaries, acceptance matrix, and open risks.

## Negative Case

Input: "Write a PRD for my novel, then outline every chapter and write chapter one."

Expected: PRD writer refuses chapter outline/prose ownership and limits output to PRD. Verdict is `revise` if a PRD can still be produced, or `fail` if the requested artifact is only HLD/Writing work.

## Boundary Or Ambiguity Case

Input: a mood board-like idea with atmosphere but no role, route, or conflict.

Expected: PRD writer extracts what exists, marks missing items as blockers or `待定`, proposes content-requirement questions, and does not invent facts silently. Verdict is `fail` when core concept plus role-route-plot constraints cannot be established.

## Expected Behaviors

- Separate facts from assumptions.
- Use Must / Should / Could / Won't.
- Keep PRD at direction/constraint/standard level.
- Provide downstream acceptance standards.
- Use references as design basis, not decoration.

## Forbidden Behaviors

- Market sizing or commercial viability analysis.
- Full beat sheet, chapter outline, key scene sequence, or role arc milestones.
- Scene imagery, action choreography, dialogue, or prose.
- Empty adjectives as success criteria.
- Script-only testing for semantic quality.
- Using `blocked` as a final artifact verdict instead of `fail`.

## Scoring Rule

Score each rubric dimension 0-2:

- 0 = fail
- 1 = revise
- 2 = pass

Total possible: 12.

## Pass Bar

- `pass`: 11-12 and no blocker.
- `revise`: 8-10 and no blocker.
- `fail`: <=7 or any blocker.

## Deterministic Fixture Checks

Run these checks from the repository root with any Python 3 interpreter. In Codex environments where the `python` shim is unavailable, use the bundled interpreter path shown in the validation log.

```powershell
python skills\novel-prd-writer\scripts\validate_prd_structure.py skills\novel-prd-writer\tests\fixtures\positive-prd.md --json
python skills\novel-prd-writer\scripts\validate_prd_structure.py skills\novel-prd-writer\tests\fixtures\positive-semantic-titles-prd.md --json
python skills\novel-prd-writer\scripts\validate_prd_structure.py skills\novel-prd-writer\tests\fixtures\negative-hld-drift-prd.md --json
python skills\novel-prd-writer\scripts\validate_prd_structure.py skills\novel-prd-writer\tests\fixtures\negative-market-drift-prd.md --json
python skills\novel-prd-writer\scripts\validate_prd_structure.py skills\novel-prd-writer\tests\fixtures\boundary-incomplete-prd.md --json
```

Expected:

- `positive-prd.md`: exit 0, `status=pass`.
- `positive-semantic-titles-prd.md`: exit 0, `status=pass`, localized headings accepted.
- `negative-hld-drift-prd.md`: exit 1, `status=fail`, includes `forbidden_content`.
- `negative-market-drift-prd.md`: exit 1, `status=fail`, includes `market_metrics`.
- `boundary-incomplete-prd.md`: exit 1, `status=fail`, includes `missing_required_section`.
