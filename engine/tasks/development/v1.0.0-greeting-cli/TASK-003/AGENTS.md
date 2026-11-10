# TASK-003 AGENTS.md

## Karpathy-style Context Engineering

把 current task 所需上下文压缩到本任务来源、输入、输出和验证面；不要加载无关小说内容，也不要推断新需求。

## Source Order

1. engine/docs/ai-novel-workflow/conception-autonomous-workflow-v2.md §3.7, §3.3-§3.6, §13-§15, §16 item 3

## Current task

实现 B0 基线封装、事实门与完成判定。Primary responsibility 仅限：harnesses/novel-conception-autonomous/runtime；harnesses/novel-conception-autonomous/tests。

## Constraints

- 不补写故事内容
- 不把访谈推断升级为锁定事实
- 不允许仅凭文件存在判完成

- 不得执行后续任务职责。
- 不得用 legacy completion 代替 V2 completion。
- 如命令或依赖缺失，按 stop conditions 明确阻断。

## Verification

- python -m unittest harnesses.novel-conception-autonomous.tests.test_baseline
- 用批准、未批准、冲突、篡改四组 fixture 验证

## Handoff

- 向 S1 提供唯一合法 B0 输入包与完成收据

最终交接必须列出改动路径、验证命令、结果、剩余风险和 completion/evidence 路径。

