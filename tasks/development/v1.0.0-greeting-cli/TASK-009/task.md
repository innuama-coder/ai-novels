# TASK-009: 迁移 Q1 构思审查技能到 V2 双任务审查

## 目标

迁移 Q1 构思审查技能到 V2 双任务审查；以可运行制品、自动 Verification 与可追溯 Handoff 为完成证据。

## Source

- docs/ai-novel-workflow/conception-autonomous-workflow-v2.md §9, §3.9, §14-§15, §16 item 9
- skills/novel-conception-reviewer/SKILL.md

## Inputs

- B0 及 S1/W1/E1/T1/C1 制品
- 现有 reviewer 1.x 脚本仅作迁移参考

## Expected outputs

- skills/novel-conception-reviewer/scripts/run_v2.py
- skills/novel-conception-reviewer/references/isolation-protocol.md
- skills/novel-conception-reviewer/tests/test_v2_runtime.py

## Allowed scope

- 实现语义审查任务与 handoff 审查任务隔离、问题路由、修复回环和统一 Q1 completion

## Forbidden scope

- 不得在同一上下文伪造两份审查
- 审查器不直接修复领域制品
- 不得用 legacy D1/R1 completion 通过 V2

## Acceptance

- 两项审查由独立执行上下文产生并保留可验证 isolation evidence
- 审查覆盖自洽、真实性边界、逻辑、完整性、全覆盖和契约交接
- 每个 blocker 精确路由到责任阶段并经 resolver 后重新审查

## Verification

- python -m unittest skills.novel-conception-reviewer.tests.test_v2_runtime
- 以刻意注入的跨域矛盾、缺 coverage、坏 handoff 和伪隔离证据验证

## Stop conditions

- 运行环境无法提供可验证隔离
- 审查结论依赖作者裁决而非自动返工

## Handoff

- 仅在双审查通过后向 P1 交付 Q1 completion 与审查证据

