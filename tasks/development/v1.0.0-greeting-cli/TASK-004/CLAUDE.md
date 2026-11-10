# TASK-004 CLAUDE.md

## Karpathy Context Engineering

Work only on the current task and keep source-backed context minimal, explicit, and auditable.

## Required Reading

- docs/ai-novel-workflow/conception-autonomous-workflow-v2.md §4, §3.9, §14-§15, §16 item 4
- skills/novel-storyline-architecture-designer/SKILL.md

## Current task

实现 S1 故事线架构设计技能; owned areas: skills/novel-storyline-architecture-designer.

## Constraints

- 不设计世界、环境、事件目录或角色档案
- 不改写 B0 锁定事实
- 不把可选旋律线强制为正文

Do not claim completion from file existence. Preserve unrelated changes and stop on an authority conflict.

## Verification

- python -m unittest skills.novel-storyline-architecture-designer.tests.test_v2_runtime
- 用通用 fixture 与缺线/断链/事实漂移负例验证

## Final Response

Report delivered files, acceptance evidence, verification results, unresolved risks, and the exact Handoff artifacts. Do not claim downstream delivery.

