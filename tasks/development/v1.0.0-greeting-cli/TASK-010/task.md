# TASK-010: 实现 P1 机器构思交付物组装技能

## Responsibility

实现 P1 机器构思交付物组装技能。只拥有 skills/novel-conception-deliverable-assembler。

## Source and inputs

- docs/ai-novel-workflow/conception-autonomous-workflow-v2.md §10, §3.9, §14-§15, §16 item 10
- skills/novel-conception-deliverable-assembler/SKILL.md
- Q1 已通过的全部正式制品

## Expected outputs

- skills/novel-conception-deliverable-assembler/scripts/run_v2.py
- skills/novel-conception-deliverable-assembler/references/package-contract.md
- skills/novel-conception-deliverable-assembler/tests/test_v2_runtime.py

## Allowed scope

- 无损组装机器构思包、索引、开发 handoff、lineage 与 completion

## Forbidden scope

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

## Stop conditions

- Q1 completion 不完整
- 上游制品之间仍有未解决冲突

## Handoff

- 向 H1-A 和最终完成流程交付唯一 P1 正式包

