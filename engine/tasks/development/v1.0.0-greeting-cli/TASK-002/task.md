# TASK-002: 实现运行状态、拓扑与返工路由

## 目标

实现运行状态、拓扑与返工路由，并以可运行制品、自动验证和可追溯 handoff 作为完成证据。

## 来源

- engine/docs/ai-novel-workflow/conception-autonomous-workflow-v2.md §3.9, §14.1-§14.3, §16 item 2

## 输入

- TASK-001 正式契约 API
- run-state、return-route、completion schema

## 交付

- harnesses/novel-conception-autonomous/runtime/coordinator.py
- harnesses/novel-conception-autonomous/runtime/return_routing.py
- harnesses/novel-conception-autonomous/tests/test_coordinator.py

## Allowed scope

- 实现不可变 run-state 版本推进、固定阶段拓扑、定向 return 计算与 resolution 闭环

## Forbidden scope

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

## Stop conditions

- run-state 与 return-route schema 无法表达权威流程
- owner、失效后缀或恢复点无法由 §14.1-§14.3 确定性计算

## Handoff

- 向所有后续任务交付唯一 coordinator API 和状态迁移证据
