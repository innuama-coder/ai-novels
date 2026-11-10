# TASK-002 CLAUDE.md

## Karpathy Context Engineering

Work only on the current task and keep source-backed context minimal, explicit, and auditable.

## Required Reading

- engine/docs/ai-novel-workflow/conception-autonomous-workflow-v2.md §3.9, §14.1-§14.3, §16 item 2

## Current task

实现运行状态、拓扑与返工路由; owned areas: harnesses/novel-conception-autonomous/runtime, harnesses/novel-conception-autonomous/tests.

## Constraints

- 不执行业务技能内容生成
- 不得绕过 expected_input_versions
- 不得把 checkpoint 当完成

Do not claim completion from file existence. Preserve unrelated changes and stop on an authority conflict.

## Verification

- python -m unittest harnesses.novel-conception-autonomous.tests.test_coordinator
- 覆盖成功、返工、暂停恢复、预算耗尽和陈旧版本五类路径

## Final Response

Report delivered files, acceptance evidence, verification results, unresolved risks, and the exact Handoff artifacts. Do not claim downstream delivery.
