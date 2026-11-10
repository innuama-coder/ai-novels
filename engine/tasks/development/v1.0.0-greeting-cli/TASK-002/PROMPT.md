# TASK-002 Execution Prompt

## Execution Objective

完成 current task「实现运行状态、拓扑与返工路由」，交付真实可运行实现，不以文档声明或 legacy 产物代替完成。

## Scope

Allowed:
- 实现不可变 run-state 版本推进、固定阶段拓扑、定向 return 计算与 resolution 闭环

Forbidden:
- 不执行业务技能内容生成
- 不得绕过 `state_before`、`input_gate`、current completion 引用及其哈希绑定
- 不得把不可变 run-state 快照或文件存在当作阶段完成

## Acceptance

- 所有合法拓扑路径可推进且非法跳步被拒绝
- router 按唯一所有权和失效表确定性计算 owner、失效后缀、`resume_stage` 与 `resume_point`
- resolution 逐值重验 return、input gate、新 completion 和状态前缀；同一 return 不得重复解析
- 每次状态变化产生 revision+1 的不可变快照并绑定 `previous_state`；重放已验收迁移不得产生分叉结果

## Verification

- python -m unittest harnesses.novel-conception-autonomous.tests.test_coordinator
- 覆盖 forward、非法跳步、定向返工、从最新快照恢复、陈旧哈希、重复解析和缺失 active-return 正文

## Constraints

- 严格遵循 source authority；遇到契约矛盾执行 Stop conditions，不自行改写权威语义。
- 只修改 task.md 声明的 impacted areas，保留用户无关改动。
- 先写失败测试或 fixture，再实现最小完整行为，并保留命令输出作为 evidence。

## Decision Principles

1. 正式契约优先于旧脚本，运行证据优先于说明文字。
2. 选择能同时满足正例、负例、lineage 和 completion 的最小设计。
3. 无法证明正确时停止并报告，不以宽松 fallback 制造假通过。
