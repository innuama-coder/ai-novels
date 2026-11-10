# TASK-011: 迁移 H1-A 人审报告设计与组装技能

## Responsibility

迁移 H1-A 人审报告设计与组装技能。只拥有 skills/novel-conception-human-review-assembler。

## Source and inputs

- docs/ai-novel-workflow/conception-autonomous-workflow-v2.md §11.1-§11.2, §3.8-§3.9, §14-§15, §16 item 11
- skills/novel-conception-human-review-assembler/SKILL.md
- P1 正式机器构思包
- 现有 H1-A 1.x 脚本仅作迁移参考

## Expected outputs

- skills/novel-conception-human-review-assembler/scripts/run_v2.py
- skills/novel-conception-human-review-assembler/references/review-plan-contract.md
- skills/novel-conception-human-review-assembler/tests/test_v2_runtime.py

## Allowed scope

- 从 P1 设计十分钟人审信息架构、视觉表达计划、片段槽位和共享工作区

## Forbidden scope

- 不改变 P1 事实
- 不直接写小说片段或 HTML
- 不回读 legacy R1/D1

## Acceptance

- 世界、故事线、环境/事件、角色及控制信息在十分钟路径内完整可达
- 每个视觉/文本模块绑定 P1 source anchor
- fragment-input-package 和 H1 workspace 通过 schema 与 lineage

## Verification

- python -m unittest skills.novel-conception-human-review-assembler.tests.test_v2_runtime
- 验证覆盖、时长预算、锚点和 legacy 输入拒绝

## Stop conditions

- P1 不完整
- 十分钟预算与完整控制信息无法同时满足且需调整契约

## Handoff

- 向 H1-B 交付片段输入包；向 H1-C 交付报告计划和 workspace

