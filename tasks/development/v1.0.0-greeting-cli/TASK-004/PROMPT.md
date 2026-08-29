# TASK-004 Execution Prompt

## Execution Objective

完成 current task「实现 S1 故事线架构设计技能」，交付真实可运行实现，不以文档声明或 legacy 产物代替完成。

## Scope

Allowed:
- 生成多维故事线、因果链、汇合/分叉/交叉点、悬念冲突和边界控制信息

Forbidden:
- 不设计世界、环境、事件目录或角色档案
- 不改写 B0 锁定事实
- 不把可选旋律线强制为正文

## Acceptance

- 输出通过正式 schema 和 lineage 校验
- 主体线覆盖起点—升级—转折—危机—收束，其他线有关系与连接点
- 每条线明确展开资格、主题作用、冲突/悬念和开发边界

## Verification

- python -m unittest skills.novel-storyline-architecture-designer.tests.test_v2_runtime
- 用通用 fixture 与缺线/断链/事实漂移负例验证

## Constraints

- 严格遵循 source authority；遇到契约矛盾执行 Stop conditions，不自行改写权威语义。
- 只修改 task.md 声明的 impacted areas，保留用户无关改动。
- 先写失败测试或 fixture，再实现最小完整行为，并保留命令输出作为 evidence。

## Decision Principles

1. 正式契约优先于旧脚本，运行证据优先于说明文字。
2. 选择能同时满足正例、负例、lineage 和 completion 的最小设计。
3. 无法证明正确时停止并报告，不以宽松 fallback 制造假通过。

