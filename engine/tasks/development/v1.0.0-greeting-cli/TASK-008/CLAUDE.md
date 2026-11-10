# TASK-008 CLAUDE.md

## Karpathy Context Engineering

Use minimal source-backed context for the current task.

## Required Reading

- engine/docs/ai-novel-workflow/conception-autonomous-workflow-v2.md §8, §3.9, §14-§15, §16 item 8
- skills/novel-character-system-designer/SKILL.md

## Current task

实现 C1 角色系统设计技能; owned areas: skills/novel-character-system-designer.

## Constraints

- 不写人物小传正文或章节
- 不为丰富而增加无职责角色
- 不改变事件因果

Preserve unrelated changes and stop on authority conflict.

## Verification

- python -m unittest skills.novel-character-system-designer.tests.test_v2_runtime
- 覆盖缺角色、无职责角色、关系误解和动机不一致

## Final Response

Report files, acceptance evidence, Verification results, risks, and Handoff artifacts.

