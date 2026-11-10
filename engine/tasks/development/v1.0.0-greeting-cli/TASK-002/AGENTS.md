# TASK-002 AGENTS.md

## Karpathy-style Context Engineering

把 current task 所需上下文压缩到本任务来源、输入、输出和验证面；不要加载无关小说内容，也不要推断新需求。

## Source Order

1. engine/docs/ai-novel-workflow/conception-autonomous-workflow-v2.md §3.9, §14.1-§14.3, §16 item 2

## Current task

实现运行状态、拓扑与返工路由。Primary responsibility 仅限：harnesses/novel-conception-autonomous/runtime；harnesses/novel-conception-autonomous/tests。

## Constraints

- 不执行业务技能内容生成
- 不得绕过 expected_input_versions
- 不得把 checkpoint 当完成

- 不得执行后续任务职责。
- 不得用 legacy completion 代替 V2 completion。
- 如命令或依赖缺失，按 stop conditions 明确阻断。

## Verification

- python -m unittest harnesses.novel-conception-autonomous.tests.test_coordinator
- 覆盖成功、返工、暂停恢复、预算耗尽和陈旧版本五类路径

## Handoff

- 向所有后续任务交付唯一 coordinator API 和状态迁移证据

最终交接必须列出改动路径、验证命令、结果、剩余风险和 completion/evidence 路径。
