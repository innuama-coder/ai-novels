# TASK-007 Execution Prompt

## Execution Objective

完成 current task「实现 T1 事件时间线设计技能」，交付真实可运行实现，不以文档声明或 legacy 产物代替完成。

## Scope

Allowed:
- 将所有故事线展开为背景事件、铺垫、触发、升级、转折、危机、收束及跨线连接

Forbidden:
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

## Constraints

- 严格遵循 source authority；遇到契约矛盾执行 Stop conditions，不自行改写权威语义。
- 只修改 task.md 声明的 impacted areas，保留用户无关改动。
- 先写失败测试或 fixture，再实现最小完整行为，并保留命令输出作为 evidence。

## Decision Principles

1. 正式契约优先于旧脚本，运行证据优先于说明文字。
2. 选择能同时满足正例、负例、lineage 和 completion 的最小设计。
3. 无法证明正确时停止并报告，不以宽松 fallback 制造假通过。

