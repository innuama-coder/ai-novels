# TASK-008: 实现 C1 角色系统设计技能

## 目标

实现 C1 角色系统设计技能；以可运行制品、自动 Verification 与可追溯 Handoff 为完成证据。

## Source

- engine/docs/ai-novel-workflow/conception-autonomous-workflow-v2.md §8, §3.9, §14-§15, §16 item 8
- skills/novel-character-system-designer/SKILL.md

## Inputs

- B0、S1、W1、E1、T1 正式制品

## Expected outputs

- skills/novel-character-system-designer/scripts/run_v2.py
- skills/novel-character-system-designer/references/runtime-contract.md
- skills/novel-character-system-designer/tests/test_v2_runtime.py

## Allowed scope

- 按故事线与事件角色槽位补齐核心、关系层、机构层角色定义及三层关系延伸

## Forbidden scope

- 不写人物小传正文或章节
- 不为丰富而增加无职责角色
- 不改变事件因果

## Acceptance

- 所有事件角色槽位均有角色承担且无孤儿角色
- 核心角色具目标、责任、能力、边界、约束、弧线和信息状态
- 三层关系是角色定义延伸，明确作用、矛盾、变化和连接事件

## Verification

- python -m unittest skills.novel-character-system-designer.tests.test_v2_runtime
- 覆盖缺角色、无职责角色、关系误解和动机不一致

## Stop conditions

- T1 角色需求自相矛盾
- 角色补齐要求改写既有事件链

## Handoff

- 向 Q1 交付完整 C1 制品和角色—事件—故事线 coverage

