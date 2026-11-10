# TASK-008 AGENTS.md

## Karpathy-style Context Engineering

为 current task 保留最小、完整、可审计上下文。

## Source Order

1. engine/docs/ai-novel-workflow/conception-autonomous-workflow-v2.md §8, §3.9, §14-§15, §16 item 8
2. skills/novel-character-system-designer/SKILL.md

## Current task

实现 C1 角色系统设计技能；owned areas: skills/novel-character-system-designer。

## Constraints

- 不写人物小传正文或章节
- 不为丰富而增加无职责角色
- 不改变事件因果

不得执行下游任务，不得用 legacy completion 代替 V2。

## Verification

- python -m unittest skills.novel-character-system-designer.tests.test_v2_runtime
- 覆盖缺角色、无职责角色、关系误解和动机不一致

## Handoff

- 向 Q1 交付完整 C1 制品和角色—事件—故事线 coverage

