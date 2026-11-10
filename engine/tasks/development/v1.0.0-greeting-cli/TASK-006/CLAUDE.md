# TASK-006 CLAUDE.md

## Karpathy Context Engineering

Work only on the current task and keep source-backed context minimal, explicit, and auditable.

## Required Reading

- engine/docs/ai-novel-workflow/conception-autonomous-workflow-v2.md §6, §3.9, §14-§15, §16 item 6
- skills/novel-environment-system-designer/SKILL.md

## Current task

实现 E1 环境系统设计技能; owned areas: skills/novel-environment-system-designer.

## Constraints

- 不新增故事线
- 不决定事件结果
- 不编写场景正文

Do not claim completion from file existence. Preserve unrelated changes and stop on an authority conflict.

## Verification

- python -m unittest skills.novel-environment-system-designer.tests.test_v2_runtime
- 覆盖承载充分性、不可达转场、缺行动接口与规则冲突

## Final Response

Report delivered files, acceptance evidence, verification results, unresolved risks, and exact Handoff artifacts.

