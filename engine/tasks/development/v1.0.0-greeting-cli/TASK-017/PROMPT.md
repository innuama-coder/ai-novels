# TASK-017 Prompt

## Execution Objective

执行 current task「执行最终交付验收并出具报告」并交付可复现证据。

## Scope

Allowed:
- 只执行独立验收、追溯覆盖核对和报告结论

Forbidden:
- 不在验收任务中补功能或改契约
- 不得豁免失败测试
- 不得把待修问题记为通过

## Acceptance

- 所有 source traceability、coverage、verification、handoff 证据齐全
- 全部单元、契约、harness、E2E 和负例测试通过
- 报告逐项给出 pass/fail、证据路径、遗留风险；任一 blocker 均判失败

## Verification

- 运行 development-planning.json 中全部 verification 命令
- 人工复核 V2 §14-§16 与任务覆盖矩阵
- 验证 acceptance-report.md 可从干净工作区复现

## Constraints

只在 owned areas 工作；遵循 source authority；不得修改契约来迎合测试；出现 stop condition 立即阻断。

## Decision Principles

独立验证优先于自报完成；负例优先于快照；任何 missing、failed、unresolved 都不能降级。

