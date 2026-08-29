# TASK-005 AGENTS.md

## Karpathy-style Context Engineering

把 current task 所需上下文压缩到本任务来源、输入、输出和验证面；不要加载无关小说内容，也不要推断新需求。

## Source Order

1. docs/ai-novel-workflow/conception-autonomous-workflow-v2.md §5, §3.9, §14-§15, §16 item 5
2. skills/novel-world-model-designer/SKILL.md

## Current task

实现 W1 虚拟世界模型设计技能。Primary responsibility 仅限：skills/novel-world-model-designer。

## Constraints

- 不枚举具体场景
- 不写事件链
- 不创建角色档案

- 不得执行后续任务职责。
- 不得用 legacy completion 代替 V2 completion。
- 如命令或依赖缺失，按 stop conditions 明确阻断。

## Verification

- python -m unittest skills.novel-world-model-designer.tests.test_v2_runtime
- 正反 fixture 验证规则覆盖、矛盾和越界

## Handoff

- 向 E1 交付 W1 正式制品和故事线到规则的 coverage

最终交接必须列出改动路径、验证命令、结果、剩余风险和 completion/evidence 路径。

