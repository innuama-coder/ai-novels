# TASK-005 Execution Prompt

## Execution Objective

完成 current task「实现 W1 虚拟世界模型设计技能」，交付真实可运行实现，不以文档声明或 legacy 产物代替完成。

## Scope

Allowed:
- 依据全部故事线定义世界规则、制度、技术/资源、地理时空、社会运行与边界

Forbidden:
- 不枚举具体场景
- 不写事件链
- 不创建角色档案

## Acceptance

- 每条故事线所依赖的世界能力、限制和代价均有规则承载
- 规则含适用范围、例外、代价与一致性检查
- 输出不越界吸收 E1/T1/C1 职责

## Verification

- python -m unittest skills.novel-world-model-designer.tests.test_v2_runtime
- 正反 fixture 验证规则覆盖、矛盾和越界

## Constraints

- 严格遵循 source authority；遇到契约矛盾执行 Stop conditions，不自行改写权威语义。
- 只修改 task.md 声明的 impacted areas，保留用户无关改动。
- 先写失败测试或 fixture，再实现最小完整行为，并保留命令输出作为 evidence。

## Decision Principles

1. 正式契约优先于旧脚本，运行证据优先于说明文字。
2. 选择能同时满足正例、负例、lineage 和 completion 的最小设计。
3. 无法证明正确时停止并报告，不以宽松 fallback 制造假通过。

