# TASK-006 Execution Prompt

## Execution Objective

完成 current task「实现 E1 环境系统设计技能」，交付真实可运行实现，不以文档声明或 legacy 产物代替完成。

## Scope

Allowed:
- 把世界规则展开为可承载具体事件的环境，定义空间、设施、感知、权限、风险、资源和转场

Forbidden:
- 不新增故事线
- 不决定事件结果
- 不编写场景正文

## Acceptance

- 所有需落地的故事线节点均有可执行环境承载
- 环境具有事件所需入口、限制、可感知信息、行动接口和转场关系
- 环境只从 W1 展开且不违背世界规则

## Verification

- python -m unittest skills.novel-environment-system-designer.tests.test_v2_runtime
- 覆盖承载充分性、不可达转场、缺行动接口与规则冲突

## Constraints

- 严格遵循 source authority；遇到契约矛盾执行 Stop conditions，不自行改写权威语义。
- 只修改 task.md 声明的 impacted areas，保留用户无关改动。
- 先写失败测试或 fixture，再实现最小完整行为，并保留命令输出作为 evidence。

## Decision Principles

1. 正式契约优先于旧脚本，运行证据优先于说明文字。
2. 选择能同时满足正例、负例、lineage 和 completion 的最小设计。
3. 无法证明正确时停止并报告，不以宽松 fallback 制造假通过。

