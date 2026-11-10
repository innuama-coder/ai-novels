# Test Plan

## Date

2026-06-07

## Target

`engine/skills/novel-prd-writer/SKILL.md`

## Test Strategy

This is a thinking skill. Tests are agentic semantic tests: a tester acts as the agent, uses the skill, produces or reviews a PRD, then scores the output with `docs/evaluation-spec.md`.

Deterministic structure checks use:

```powershell
python skills\novel-prd-writer\scripts\validate_prd_structure.py <artifact> --json
```

Use any Python 3 interpreter. If the Windows `python` shim times out, use the Codex bundled Python interpreter.

## Test Case 1: Positive Case

### Prompt

```text
我有一个科幻小说：一个退休记忆修复师在火星地下城发现自己的童年记忆被城市系统伪造。故事要克制、冷感、有调查线和亲情线。请写小说 PRD。
```

### Expected Behavior

- Produces PRD sections for concept, roles, setting, routes, plot constraints, theme/style, acceptance.
- Defines role requirements without full arcs.
- Defines investigation route and family/emotional route without node order.
- Marks style constraints: restrained, cold, memory-fragment imagery.
- Gives Must/Won't constraints.
- Verdict: `pass` or `revise` with concrete missing fields.

### Forbidden

- Chapter-by-chapter outline.
- Scene visuals such as exact room, gesture, or dialogue.
- Market positioning or audience metrics.

## Test Case 2: Negative Case

### Prompt

```text
请写一个小说 PRD，并顺便给我 30 章大纲、关键场景表和第一章正文。
```

### Expected Behavior

- Produces only PRD or states that outline/key scenes/prose are outside PRD.
- Routes chapter outline/key scene table to HLD.
- Routes first chapter prose to Writing Agent.
- Verdict notes scope conflict.

### Forbidden

- Fulfilling all requested artifacts inside PRD writer.

## Test Case 3: Boundary Case

### Prompt

```text
我想写一个很孤独、很蓝、像冬天海边一样的小说，主角可能是女孩，也可能是老人，最好有一点梦境感。
```

### Expected Behavior

- Extracts available style/atmosphere facts.
- Marks missing concept, role, route, and conflict as `待定`.
- Provides PRD intake questions or provisional constraints.
- Does not invent a full plot.
- Verdict: `revise` if enough facts exist for a provisional PRD, otherwise `fail`.

### Forbidden

- Pretending a complete PRD exists.
- Inventing named characters and plot as facts.

## Test Case 4: Boundary With HLD

### Prompt

```text
PRD 里帮我把主线每个节点、角色每次转变、高潮前后的关键场景都安排好。
```

### Expected Behavior

- Explains that PRD may define route functions and required plot functions.
- Refuses node order, character transition sequence, and key scene arrangement as HLD work.
- Produces a PRD-compatible route/plot requirement matrix.

## Test Case 5: Boundary With LLD

### Prompt

```text
PRD 里要写清楚每个关键场景的画面、光线、声音、角色动作和对白方向。
```

### Expected Behavior

- Refuses scene-level details as LLD work.
- Defines style, sensory boundaries, and material constraints at PRD level.
- Suggests LLD should later expand these into scene blueprints.

## Review Checklist

For every test output, score:

- Direction clarity
- Constraint strength
- Role-route-plot coverage
- Boundary discipline
- Method traceability
- Downstream consumability

Use the scoring and pass bar in `docs/evaluation-spec.md`.

## Fixture Checks

| Fixture | Expected Exit | Expected Reason |
|---|---:|---|
| `tests/fixtures/positive-prd.md` | 0 | complete PRD structure |
| `tests/fixtures/positive-semantic-titles-prd.md` | 0 | complete PRD with localized section titles |
| `tests/fixtures/negative-hld-drift-prd.md` | 1 | forbidden HLD drift |
| `tests/fixtures/negative-market-drift-prd.md` | 1 | forbidden market/commerce drift |
| `tests/fixtures/boundary-incomplete-prd.md` | 1 | missing required sections |
