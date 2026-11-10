# TASK-010 AGENTS.md

## Karpathy-style Context Engineering

只保留 current task 的来源、输入、交付和测试上下文。

## Source Order

1. engine/docs/ai-novel-workflow/conception-autonomous-workflow-v2.md §10, §3.9, §14-§15, §16 item 10
2. skills/novel-conception-deliverable-assembler/SKILL.md

## Current task

实现 P1 机器构思交付物组装技能。

## Constraints

- 不新增构思事实
- 不润色或重写上游控制信息
- 不接受未通过 Q1 的输入

## Verification

- python -m unittest skills.novel-conception-deliverable-assembler.tests.test_v2_runtime
- 对照源制品做字段级无损与篡改验证

## Handoff

- 向 H1-A 和最终完成流程交付唯一 P1 正式包

