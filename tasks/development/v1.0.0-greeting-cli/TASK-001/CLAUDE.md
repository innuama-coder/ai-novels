# TASK-001 CLAUDE.md

## Karpathy Context Engineering

Work only on the current task and keep source-backed context minimal, explicit, and auditable.

## Required Reading

- docs/ai-novel-workflow/conception-autonomous-workflow-v2.md §3.3-§3.6, §15, §16 item 1
- docs/ai-novel-workflow/contracts/autonomous-v2/

## Current task

建立 V2 正式契约运行时; owned areas: harnesses/novel-conception-autonomous/runtime, harnesses/novel-conception-autonomous/tests.

## Constraints

- 不改写领域技能语义
- 不得继续把 testing/autonomous_v2_schema_runtime.py 当生产运行时
- 不得降级为手写字段检查

Do not claim completion from file existence. Preserve unrelated changes and stop on an authority conflict.

## Verification

- python -m unittest harnesses.novel-conception-autonomous.tests.test_contract_runtime
- 使用正反 fixture 验证 Draft 2020-12 行为

## Final Response

Report delivered files, acceptance evidence, verification results, unresolved risks, and the exact Handoff artifacts. Do not claim downstream delivery.

