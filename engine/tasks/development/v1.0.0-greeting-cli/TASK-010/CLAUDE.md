# TASK-010 CLAUDE.md

## Karpathy Context Engineering

Use auditable, minimal context for the current task.

## Required Reading

- engine/docs/ai-novel-workflow/conception-autonomous-workflow-v2.md §10, §3.9, §14-§15, §16 item 10
- skills/novel-conception-deliverable-assembler/SKILL.md

## Current task

实现 P1 机器构思交付物组装技能.

## Constraints

- 不新增构思事实
- 不润色或重写上游控制信息
- 不接受未通过 Q1 的输入

## Verification

- python -m unittest skills.novel-conception-deliverable-assembler.tests.test_v2_runtime
- 对照源制品做字段级无损与篡改验证

## Final Response

List delivered paths, acceptance and Verification evidence, risks, and exact Handoff artifacts.

