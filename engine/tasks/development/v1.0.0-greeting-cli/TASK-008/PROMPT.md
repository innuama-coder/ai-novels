# TASK-008 Execution Prompt

## Execution Objective

完成 current task：实现 C1 角色系统设计技能，交付真实 V2 实现。

## Scope

Allowed:
- 按故事线与事件角色槽位补齐核心、关系层、机构层角色定义及三层关系延伸

Forbidden:
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

## Constraints

只修改 owned areas；保持 source authority；先以失败 fixture 证明缺口；遇到 stop condition 不自行改契约。

## Decision Principles

正式契约优先于 legacy；运行证据优先于说明；不能证明则阻断，不制造 fallback 假通过。

