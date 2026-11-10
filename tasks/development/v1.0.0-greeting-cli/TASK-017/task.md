# TASK-017: 执行最终交付验收并出具报告

## Responsibility

执行最终交付验收并出具报告；本任务只拥有 tasks/development/v1.0.0-greeting-cli/acceptance-report.md。

## Source

- docs/ai-novel-workflow/conception-autonomous-workflow-v2.md §14-§16
- tasks/development/v1.0.0-greeting-cli/development-planning.json

## Inputs

- TASK-001 至 TASK-016 的代码、测试、completion 与 handoff 证据

## Expected outputs

- tasks/development/v1.0.0-greeting-cli/acceptance-report.md

## Allowed scope

- 只执行独立验收、追溯覆盖核对和报告结论

## Forbidden scope

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

## Stop conditions

- 任何依赖任务未完成或证据缺失
- 任何测试 failed 或存在 unresolved blocker

## Handoff

- 向用户交付 acceptance-report.md 和明确的可开发/不可开发结论

