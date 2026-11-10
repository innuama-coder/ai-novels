# TASK-011 CLAUDE.md

## Karpathy Context Engineering

Use auditable, minimal context for the current task.

## Required Reading

- engine/docs/ai-novel-workflow/conception-autonomous-workflow-v2.md §11.1-§11.2, §3.8-§3.9, §14-§15, §16 item 11
- skills/novel-conception-human-review-assembler/SKILL.md

## Current task

迁移 H1-A 人审报告设计与组装技能.

## Constraints

- 不改变 P1 事实
- 不直接写小说片段或 HTML
- 不回读 legacy R1/D1

## Verification

- python -m unittest skills.novel-conception-human-review-assembler.tests.test_v2_runtime
- 验证覆盖、时长预算、锚点和 legacy 输入拒绝

## Final Response

List delivered paths, acceptance and Verification evidence, risks, and exact Handoff artifacts.

