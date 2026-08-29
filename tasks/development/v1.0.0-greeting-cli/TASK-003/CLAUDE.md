# TASK-003 CLAUDE.md

## Karpathy Context Engineering

Work only on the current task and keep source-backed context minimal, explicit, and auditable.

## Required Reading

- docs/ai-novel-workflow/conception-autonomous-workflow-v2.md §3.7, §3.3-§3.6, §13-§15, §16 item 3

## Current task

实现 B0 基线封装、事实门与完成判定; owned areas: harnesses/novel-conception-autonomous/runtime, harnesses/novel-conception-autonomous/tests.

## Constraints

- 不补写故事内容
- 不把访谈推断升级为锁定事实
- 不允许仅凭文件存在判完成

Do not claim completion from file existence. Preserve unrelated changes and stop on an authority conflict.

## Verification

- python -m unittest harnesses.novel-conception-autonomous.tests.test_baseline
- 用批准、未批准、冲突、篡改四组 fixture 验证

## Final Response

Report delivered files, acceptance evidence, verification results, unresolved risks, and the exact Handoff artifacts. Do not claim downstream delivery.

