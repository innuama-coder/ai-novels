# TASK-007 AGENTS.md

## Karpathy-style Context Engineering

把 current task 所需上下文压缩到本任务来源、输入、输出和验证面；不要加载无关小说内容，也不要推断新需求。

## Source Order

1. docs/ai-novel-workflow/conception-autonomous-workflow-v2.md §7, §3.9, §14-§15, §16 item 7
2. skills/novel-event-timeline-designer/SKILL.md

## Current task

实现 T1 事件时间线设计技能。Primary responsibility 仅限：skills/novel-event-timeline-designer。

## Constraints

- 不写章节或场景正文
- 不改变故事线目的
- 不创建未受世界/环境约束的事件

- 不得执行后续任务职责。
- 不得用 legacy completion 代替 V2 completion。

## Verification

- python -m unittest skills.novel-event-timeline-designer.tests.test_v2_runtime
- 覆盖因果断链、时序矛盾、环境缺失和无后果事件

## Handoff

- 向 C1 交付完整事件目录、时间线和角色槽位需求

