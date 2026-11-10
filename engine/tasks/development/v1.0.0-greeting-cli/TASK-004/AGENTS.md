# TASK-004 AGENTS.md

## Karpathy-style Context Engineering

把 current task 所需上下文压缩到本任务来源、输入、输出和验证面；不要加载无关小说内容，也不要推断新需求。

## Source Order

1. engine/docs/ai-novel-workflow/conception-autonomous-workflow-v2.md §4, §3.9, §14-§15, §16 item 4
2. skills/novel-storyline-architecture-designer/SKILL.md

## Current task

实现 S1 故事线架构设计技能。Primary responsibility 仅限：skills/novel-storyline-architecture-designer。

## Constraints

- 不设计世界、环境、事件目录或角色档案
- 不改写 B0 锁定事实
- 不把可选旋律线强制为正文

- 不得执行后续任务职责。
- 不得用 legacy completion 代替 V2 completion。
- 如命令或依赖缺失，按 stop conditions 明确阻断。

## Verification

- python -m unittest skills.novel-storyline-architecture-designer.tests.test_v2_runtime
- 用通用 fixture 与缺线/断链/事实漂移负例验证

## Handoff

- 向 W1 交付 S1 正式制品、completion、manifest 与控制信息

最终交接必须列出改动路径、验证命令、结果、剩余风险和 completion/evidence 路径。

