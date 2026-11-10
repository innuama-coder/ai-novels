# TASK-007 CLAUDE.md

## Karpathy Context Engineering

Work only on the current task and keep source-backed context minimal, explicit, and auditable.

## Required Reading

- engine/docs/ai-novel-workflow/conception-autonomous-workflow-v2.md §7, §3.9, §14-§15, §16 item 7
- skills/novel-event-timeline-designer/SKILL.md

## Current task

实现 T1 事件时间线设计技能; owned areas: skills/novel-event-timeline-designer.

## Constraints

- 不写章节或场景正文
- 不改变故事线目的
- 不创建未受世界/环境约束的事件

Do not claim completion from file existence. Preserve unrelated changes and stop on an authority conflict.

## Verification

- python -m unittest skills.novel-event-timeline-designer.tests.test_v2_runtime
- 覆盖因果断链、时序矛盾、环境缺失和无后果事件

## Final Response

Report delivered files, acceptance evidence, verification results, unresolved risks, and exact Handoff artifacts.

