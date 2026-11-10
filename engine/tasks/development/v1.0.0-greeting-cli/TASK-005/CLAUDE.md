# TASK-005 CLAUDE.md

## Karpathy Context Engineering

Work only on the current task and keep source-backed context minimal, explicit, and auditable.

## Required Reading

- engine/docs/ai-novel-workflow/conception-autonomous-workflow-v2.md §5, §3.9, §14-§15, §16 item 5
- skills/novel-world-model-designer/SKILL.md

## Current task

实现 W1 虚拟世界模型设计技能; owned areas: skills/novel-world-model-designer.

## Constraints

- 不枚举具体场景
- 不写事件链
- 不创建角色档案

Do not claim completion from file existence. Preserve unrelated changes and stop on an authority conflict.

## Verification

- python -m unittest skills.novel-world-model-designer.tests.test_v2_runtime
- 正反 fixture 验证规则覆盖、矛盾和越界

## Final Response

Report delivered files, acceptance evidence, verification results, unresolved risks, and the exact Handoff artifacts. Do not claim downstream delivery.

