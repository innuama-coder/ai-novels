# TASK-007: 实现 T1 事件时间线设计技能

## 目标

实现 T1 事件时间线设计技能，并以可运行制品、自动验证和可追溯 handoff 作为完成证据。

## 来源

- engine/docs/ai-novel-workflow/conception-autonomous-workflow-v2.md §7, §3.9, §14-§15, §16 item 7
- skills/novel-event-timeline-designer/SKILL.md

## 输入

- B0、S1、W1、E1 正式制品

## 交付

- skills/novel-event-timeline-designer/scripts/run_v2.py
- skills/novel-event-timeline-designer/references/runtime-contract.md
- skills/novel-event-timeline-designer/tests/test_v2_runtime.py

## Allowed scope

- 将所有故事线展开为背景事件、铺垫、触发、升级、转折、危机、收束及跨线连接

## Forbidden scope

- 不写章节或场景正文
- 不改变故事线目的
- 不创建未受世界/环境约束的事件

## Acceptance

- 主线和必需支线不存在时间/因果断点，背景事件能解释前置条件
- 每个事件定义参与者角色需求、环境、触发、前置、结果、信息变化和后继
- 并发、回忆、插叙和汇合点有明确时间关系

## Verification

- python -m unittest skills.novel-event-timeline-designer.tests.test_v2_runtime
- 覆盖因果断链、时序矛盾、环境缺失和无后果事件

## Stop conditions

- E1 无法承载必需事件
- 补齐事件必须改变已批准故事线

## Handoff

- 向 C1 交付完整事件目录、时间线和角色槽位需求

