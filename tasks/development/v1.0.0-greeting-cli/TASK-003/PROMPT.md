# TASK-003 Execution Prompt

## Execution Objective

完成 current task「实现 B0 基线封装、事实门与完成判定」，交付真实可运行实现，不以文档声明或 legacy 产物代替完成。

## Scope

Allowed:
- 无损封装 B0，按原文稳定 control ID 建立锁定项/开放项/证据锚点，执行事实门、manifest 与 completion

Forbidden:
- 不补写故事内容
- 不把访谈推断升级为锁定事实
- 不发明原文不存在的 control ID、fact adoption 或批准记录
- 不允许仅凭文件存在判完成

## Acceptance

- 每个锁定事实可追溯到批准来源
- 冲突事实、缺失证据和未批准简报均硬阻断
- B0 completion 同时校验语义状态、制品、hash、manifest 和 run-state

## Verification

- python -m unittest harnesses.novel-conception-autonomous.tests.test_baseline
- 用批准、未批准、冲突、篡改四组 fixture 验证

## Constraints

- 严格遵循 source authority；遇到契约矛盾执行 Stop conditions，不自行改写权威语义。
- 只修改 task.md 声明的 impacted areas，保留用户无关改动。
- 先写失败测试或 fixture，再实现最小完整行为，并保留命令输出作为 evidence。

## Decision Principles

1. 正式契约优先于旧脚本，运行证据优先于说明文字。
2. 选择能同时满足正例、负例、lineage 和 completion 的最小设计。
3. 无法证明正确时停止并报告，不以宽松 fallback 制造假通过。
