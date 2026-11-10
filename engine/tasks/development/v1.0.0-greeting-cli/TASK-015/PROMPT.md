# TASK-015 Prompt

## Execution Objective

完成 current task「组装自主构思主 Harness、适配器与发布验证」，以可运行实现和
证据交付。入口从当前 rendered H1 开始，消费外部密封决定，仅 approved 生成 final。

## Scope

Allowed:
- 连接正式调用链、适配器、validator、release builder、日志/证据和 legacy 禁入说明

Forbidden:
- 不复制领域逻辑到 orchestration
- 不保留 D1/R1 作为 V2 成功路径
- 不以文档声明替代可运行调用
- 不 patch H1 validator，不由 Harness 创建作者决定

## Acceptance

- manifest 中顺序与权威链一致且每一 gate/route 可执行
- harness 自检覆盖必需文件、schema、运行器、completion、适配器和 legacy 禁入
- 旧入口明确失败或显式兼容，不产生半 V2 包
- revise/rejected 分支 `final=None`，approved 是唯一开发准入
- source/Codex 发布包经 source、staging、ZIP 解包三层复验

## Verification

- python harnesses/novel-conception-autonomous/validators/validate_harness.py
- 运行全体单元/契约测试并检查发布包清单

## Constraints

遵循 source authority，只改 owned areas；保留无关改动；遇到 stop condition 停止，不擅改契约。

## Decision Principles

V2 契约优先于 legacy；负例与真实运行证据优先；不可证明即阻断。
