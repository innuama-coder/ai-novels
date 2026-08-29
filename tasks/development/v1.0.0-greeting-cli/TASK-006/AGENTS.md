# TASK-006 AGENTS.md

## Karpathy-style Context Engineering

把 current task 所需上下文压缩到本任务来源、输入、输出和验证面；不要加载无关小说内容，也不要推断新需求。

## Source Order

1. docs/ai-novel-workflow/conception-autonomous-workflow-v2.md §6, §3.9, §14-§15, §16 item 6
2. skills/novel-environment-system-designer/SKILL.md

## Current task

实现 E1 环境系统设计技能。Primary responsibility 仅限：skills/novel-environment-system-designer。

## Constraints

- 不新增故事线
- 不决定事件结果
- 不编写场景正文

- 不得执行后续任务职责。
- 不得用 legacy completion 代替 V2 completion。

## Verification

- python -m unittest skills.novel-environment-system-designer.tests.test_v2_runtime
- 覆盖承载充分性、不可达转场、缺行动接口与规则冲突

## Handoff

- 向 T1 交付环境目录、连接图和 storyline coverage

