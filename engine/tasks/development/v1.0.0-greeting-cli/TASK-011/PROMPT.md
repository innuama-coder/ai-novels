# TASK-011 Prompt

## Execution Objective

完成 current task「迁移 H1-A 人审报告设计与组装技能」并提供运行证据。

## Scope

Allowed:
- 从 P1 设计十分钟人审信息架构、视觉表达计划、片段槽位和共享工作区

Forbidden:
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

## Constraints

服从 source authority；只改 owned areas；legacy 只作迁移参考；stop condition 出现时停止。

## Decision Principles

契约优先，证据优先；先负例后实现；不以文件存在、宽松校验或人工说明代替完成。

