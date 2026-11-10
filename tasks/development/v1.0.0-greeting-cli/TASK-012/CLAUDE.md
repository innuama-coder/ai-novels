# TASK-012 CLAUDE.md

## Karpathy Context Engineering

Use auditable, minimal context for the current task.

## Required Reading

- docs/ai-novel-workflow/conception-autonomous-workflow-v2.md §11.3, §3.8-§3.9, §14-§15, §16 item 12
- skills/novel-conception-fragment-writer/SKILL.md

## Current task

迁移 H1-B 小说评审片段编写技能.

## Constraints

- 不补设定或改变剧情结论
- 不把片段当正式正文
- 不绕过 P1 anchors

## Verification

- python -m unittest skills.novel-conception-fragment-writer.tests.test_v2_runtime
- 验证数量、风格、锚点、越权事实和禁写心理活动

## Final Response

List delivered paths, acceptance and Verification evidence, risks, and exact Handoff artifacts.

