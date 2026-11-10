# TASK-016 Prompt

## Execution Objective

执行 current task「建立通用与《断线》整链前向验收套件」并交付可复现证据。

## Scope

Allowed:
- 构造去项目硬编码的通用用例、断线回归用例、失败注入和全链证据断言

Forbidden:
- 不得把《断线》内容写进通用运行器
- 不得用快照完全替代语义/契约断言
- 不得覆写已批准项目交付物

## Acceptance

- 通用 fixture 从 B0 到作者批准完整通过
- 《断线》前向测试验证内容一致性且不依赖硬编码名称规则
- 至少覆盖每个 gate、一个跨阶段返工、暂停恢复、篡改和 legacy 输入拒绝

## Verification

- python -m unittest testing.test_conception_autonomous_v2_e2e
- 重复运行两次验证确定性与幂等性

## Constraints

只在 owned areas 工作；遵循 source authority；不得修改契约来迎合测试；出现 stop condition 立即阻断。

## Decision Principles

独立验证优先于自报完成；负例优先于快照；任何 missing、failed、unresolved 都不能降级。

