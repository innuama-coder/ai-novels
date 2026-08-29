# TASK-009 CLAUDE.md

## Karpathy Context Engineering

Use minimal source-backed context for the current task.

## Required Reading

- docs/ai-novel-workflow/conception-autonomous-workflow-v2.md §9, §3.9, §14-§15, §16 item 9
- skills/novel-conception-reviewer/SKILL.md

## Current task

迁移 Q1 构思审查技能到 V2 双任务审查; owned areas: skills/novel-conception-reviewer.

## Constraints

- 不得在同一上下文伪造两份审查
- 审查器不直接修复领域制品
- 不得用 legacy D1/R1 completion 通过 V2

Preserve unrelated changes and stop on authority conflict.

## Verification

- python -m unittest skills.novel-conception-reviewer.tests.test_v2_runtime
- 以刻意注入的跨域矛盾、缺 coverage、坏 handoff 和伪隔离证据验证

## Final Response

Report files, acceptance evidence, Verification results, risks, and Handoff artifacts.

