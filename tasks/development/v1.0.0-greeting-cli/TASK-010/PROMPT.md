# TASK-010 Prompt

## Execution Objective

完成 current task「实现 P1 机器构思交付物组装技能」并提供运行证据。

## Scope

Allowed:
- 无损组装机器构思包、索引、开发 handoff、lineage 与 completion

Forbidden:
- 不新增构思事实
- 不润色或重写上游控制信息
- 不接受未通过 Q1 的输入

## Acceptance

- P1 对所有上游制品逐项可追溯且内容无语义漂移
- 包内索引、hash、manifest、版本、开发 handoff 相互一致
- 缺件、陈旧版本或 Q1 未通过时硬阻断

## Verification

- python -m unittest skills.novel-conception-deliverable-assembler.tests.test_v2_runtime
- 对照源制品做字段级无损与篡改验证

## Constraints

服从 source authority；只改 owned areas；legacy 只作迁移参考；stop condition 出现时停止。

## Decision Principles

契约优先，证据优先；先负例后实现；不以文件存在、宽松校验或人工说明代替完成。

