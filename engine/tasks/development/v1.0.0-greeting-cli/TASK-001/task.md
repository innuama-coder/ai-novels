# TASK-001: 建立 V2 正式契约运行时

## 目标

建立 V2 正式契约运行时，并以可运行制品、自动验证和可追溯 handoff 作为完成证据。

## 来源

- engine/docs/ai-novel-workflow/conception-autonomous-workflow-v2.md §3.3-§3.6, §15, §16 item 1
- engine/docs/ai-novel-workflow/contracts/autonomous-v2/

## 输入

- 22 份 autonomous-v2 JSON Schema
- 现有 testing/autonomous_v2_schema_runtime.py 仅作为测试参考

## 交付

- harnesses/novel-conception-autonomous/requirements.txt
- harnesses/novel-conception-autonomous/runtime/contracts.py
- harnesses/novel-conception-autonomous/runtime/canonical.py
- harnesses/novel-conception-autonomous/tests/test_contract_runtime.py

## Allowed scope

- 引入并锁定支持 Draft 2020-12 的正式 JSON Schema 依赖
- 实现 schema 加载、严格校验、canonical JSON、hash 与 manifest 基础函数

## Forbidden scope

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

## Stop conditions

- 无法获得或固定 Draft 2020-12 validator
- 现有 schema 被正式 validator 判定自相矛盾且未先回到契约评审

## Handoff

- 向 TASK-002/003 交付稳定 Python API、依赖清单与测试命令

