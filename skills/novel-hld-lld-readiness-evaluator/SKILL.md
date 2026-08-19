---
name: novel-hld-lld-readiness-evaluator
description: 以两个隔离任务验证 HLD 到 LLD 的交接：先只按 lld-handoff 重建 LLD 工作，再对照已封存的 consumer 结果与 HP1 正式包验证无遗漏、无增强、无弱化。用于 novel-hld-autonomous 的 HQ2 内部任务，不负责发布顶层 HQ2 成果。
---

# HLD→LLD 交接就绪度验证

执行前完整阅读：

- [输入输出契约](references/input-output-contract.md)
- [方法论](references/methodology.md)
- [SOP](references/sop.md)
- [运行时契约](references/runtime-contract.json)

仅在需要追溯研究依据时阅读 [sources.md](references/sources.md)。

## 目标

在两个彼此隔离的任务中回答两个不同问题：

1. `consumer_test`：一个只拿到正式 `lld-handoff.json` 的 LLD 执行者，能否无猜测地重建工作、边界、约束、自由度与验收条件？
2. `fidelity_test`：上述已封存的消费结果是否忠实覆盖 HP1 正式 HLD 包，没有遗漏、擅自增强、弱化或错误分类？

## 边界

- 两个任务只能读取各自 work order/input gate 已签名 allowlist 中的文件，并逐项校验当前 hash。
- `consumer_test` 禁止读取 HLD 正式包、canonical model、spec、cross-index、traceability、作者报告或上游生产任务草稿。
- `fidelity_test` 只能读取已封存的 consumer 结果与 HP1 正式交付，不得重写交接文件或替上游修复。
- 两个任务不得共享 task id；fidelity 必须绑定 consumer 的 manifest、主文件与内容 hash。
- 本技能只发布 `result_scope=composite_internal` 的内部包。顶层 `lld-handoff-acceptance.json`、stage completion 和路由均由 Harness composite publisher 负责。

## 判定

- `pass / none` → 内部 `ready`。
- `revise / reviewer_local` → 仅修正当前 HQ2 候选，不回写上游。
- `fail / upstream_content` → `blocked / upstream_defect`，保留证据与受影响 ID。
- `fail / author_required` 或 `fail / reality_dependency` → 对应 blocker，交给 Harness 路由。
- 运行时、签名、allowlist、hash、schema、任务隔离或封存绑定失效时 fail closed，不产生可接受交付。

## 执行

Agent 在 draft 目录中只写当前 mode 的 canonical JSON 与 `review-session.json`，然后调用：

```powershell
python scripts/run_skill.py <work-order.json> <draft-directory>
```

成功时内部包必须严格包含五个文件：

- consumer：`handoff-consumption-test.json`、`review-session.json`、`consumption-test-execution.json`、`validation.json`、`package-manifest.json`
- fidelity：`handoff-fidelity-test.json`、`review-session.json`、`fidelity-test-execution.json`、`validation.json`、`package-manifest.json`

本技能不会生成顶层 completion。
