# TASK-001 Execution Prompt

## Execution Objective

完成 current task「建立 V2 正式契约运行时」，交付真实可运行实现，不以文档声明或 legacy 产物代替完成。

## Scope

Allowed:
- 引入并锁定支持 Draft 2020-12 的正式 JSON Schema 依赖
- 实现 schema 加载、严格校验、canonical JSON、hash 与 manifest 基础函数

Forbidden:
- 不改写领域技能语义
- 不得继续把 testing/autonomous_v2_schema_runtime.py 当生产运行时
- 不得降级为手写字段检查

## Acceptance

- 正式 validator 对全部 22 份 schema 自检通过并拒绝 additionalProperties、条件分支和引用错误
- canonical JSON 与 hash 在字段顺序变化时保持稳定
- 依赖安装与离线运行方式有可复现说明

## Verification

- python -m unittest harnesses.novel-conception-autonomous.tests.test_contract_runtime
- 使用正反 fixture 验证 Draft 2020-12 行为

## Constraints

- 严格遵循 source authority；遇到契约矛盾执行 Stop conditions，不自行改写权威语义。
- 只修改 task.md 声明的 impacted areas，保留用户无关改动。
- 先写失败测试或 fixture，再实现最小完整行为，并保留命令输出作为 evidence。

## Decision Principles

1. 正式契约优先于旧脚本，运行证据优先于说明文字。
2. 选择能同时满足正例、负例、lineage 和 completion 的最小设计。
3. 无法证明正确时停止并报告，不以宽松 fallback 制造假通过。

