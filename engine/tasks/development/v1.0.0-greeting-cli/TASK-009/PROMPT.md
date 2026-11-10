# TASK-009 Execution Prompt

## Execution Objective

完成 current task：迁移 Q1 构思审查技能到 V2 双任务审查，交付真实 V2 实现。

## Scope

Allowed:
- 实现语义审查任务与 handoff 审查任务隔离、问题路由、修复回环和统一 Q1 completion

Forbidden:
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

## Constraints

只修改 owned areas；保持 source authority；先以失败 fixture 证明缺口；遇到 stop condition 不自行改契约。

## Decision Principles

正式契约优先于 legacy；运行证据优先于说明；不能证明则阻断，不制造 fallback 假通过。

