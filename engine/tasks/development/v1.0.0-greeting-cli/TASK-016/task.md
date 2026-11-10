# TASK-016: 建立通用与《断线》整链前向验收套件

## Responsibility

建立通用与《断线》整链前向验收套件；本任务只拥有 harnesses/novel-conception-autonomous/evals、testing。

## Source

- engine/docs/ai-novel-workflow/conception-autonomous-workflow-v2.md §15-§17
- projects/duanxian/ 已批准访谈与构思资料

## Inputs

- 可运行主 harness
- 通用最小 fixture
- 《断线》已批准输入

## Expected outputs

- harnesses/novel-conception-autonomous/evals/README.md
- harnesses/novel-conception-autonomous/evals/fixtures/generic/fixture.json
- harnesses/novel-conception-autonomous/evals/fixtures/duanxian/fixture.json
- testing/test_conception_autonomous_v2_e2e.py

## Allowed scope

- 构造去项目硬编码的通用用例、断线回归用例、失败注入和全链证据断言

## Forbidden scope

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

## Stop conditions

- 整链只能通过项目特判
- 测试无法在隔离临时目录执行

## Handoff

- 向最终交付验收提供测试日志、制品 manifest、coverage 和失败注入报告

