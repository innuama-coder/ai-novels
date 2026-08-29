# TASK-001 AGENTS.md

## Karpathy-style Context Engineering

把 current task 所需上下文压缩到本任务来源、输入、输出和验证面；不要加载无关小说内容，也不要推断新需求。

## Source Order

1. docs/ai-novel-workflow/conception-autonomous-workflow-v2.md §3.3-§3.6, §15, §16 item 1
2. docs/ai-novel-workflow/contracts/autonomous-v2/

## Current task

建立 V2 正式契约运行时。Primary responsibility 仅限：harnesses/novel-conception-autonomous/runtime；harnesses/novel-conception-autonomous/tests。

## Constraints

- 不改写领域技能语义
- 不得继续把 testing/autonomous_v2_schema_runtime.py 当生产运行时
- 不得降级为手写字段检查

- 不得执行后续任务职责。
- 不得用 legacy completion 代替 V2 completion。
- 如命令或依赖缺失，按 stop conditions 明确阻断。

## Verification

- python -m unittest harnesses.novel-conception-autonomous.tests.test_contract_runtime
- 使用正反 fixture 验证 Draft 2020-12 行为

## Handoff

- 向 TASK-002/003 交付稳定 Python API、依赖清单与测试命令

最终交接必须列出改动路径、验证命令、结果、剩余风险和 completion/evidence 路径。

