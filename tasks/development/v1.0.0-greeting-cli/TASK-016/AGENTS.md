# TASK-016 AGENTS.md

## Karpathy-style Context Engineering

current task 只加载验收所需的最小完整上下文。

## Source Order

1. docs/ai-novel-workflow/conception-autonomous-workflow-v2.md §15-§17
2. projects/duanxian/ 已批准访谈与构思资料

## Current task

建立通用与《断线》整链前向验收套件。

## Constraints

- 不得把《断线》内容写进通用运行器
- 不得用快照完全替代语义/契约断言
- 不得覆写已批准项目交付物

## Verification

- python -m unittest testing.test_conception_autonomous_v2_e2e
- 重复运行两次验证确定性与幂等性

## Handoff

- 向最终交付验收提供测试日志、制品 manifest、coverage 和失败注入报告

