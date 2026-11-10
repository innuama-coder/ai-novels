# TASK-015：组装自主构思主 Harness、适配器与发布验证

## Responsibility

Owned areas：

- `harnesses/novel-conception-autonomous`
- `docs/ai-novel-workflow/conception-orchestration.md`
- `docs/ai-novel-workflow/conception-phase.md`

## Source

- `docs/ai-novel-workflow/conception-autonomous-workflow-v2.md` §2、§13–§16
- `docs/ai-novel-workflow/conception-orchestration.md`
- 已验收的 TASK-004–TASK-014 生产入口与 V2 公共契约

## Objective

交付一个可移植、可验证、评审门控的自主构思 Harness。正式入口从已经
`rendered` 的 H1 工作区开始：发布唯一 H1 completion，消费外部密封的作者
决定，仅在 `approved` 分支发布最终构思 completion。

## Inputs

- 当前 B0–P1 九阶段之前的八个正式 package 与 coordinator 状态
- 正式 P1 package
- 真实 H1-A plan、H1-B、H1-A assembly、H1-C package
- 密封的 H1 workspace 链与 input gate
- 外部密封的作者决定
- P1 绑定的 development handoff

测试允许隔离正式 P1 fixture，但必须记录边界；不得替换或 patch H1 validator。

## Deliverables

- `manifest.yaml`、`agent.md`、`workflow.md`、`rules.md`
- `runtime/harness.py::run_from_rendered_h1`
- `docs/` 硬输入、输出、验证与发布契约
- `schemas/` 公共 V2 schema 索引与发布时的完整 bundle
- `evals/cases/` 正负边界语料
- `adapters/codex/{SKILL.md,install.md,mapping.md}`
- `validators/validate_harness.py`
- `tools/build_release.py` 及 source/Codex 可复验发布包

## Hard workflow

`B0→S1→W1→E1→T1→C1→Q1→P1→H1-A plan→H1-B→H1-A assemble→H1-C→H1 completion→external decision`

- `approved → final completion → development ready`
- `revise → deterministic routed return；final=None`
- `rejected → terminal rejected；final=None`

## Boundaries

- 不复制领域生成逻辑到 orchestration。
- 不创建、改写或推断作者决定。
- 不修改上游 validator 以放宽输入。
- 不把 checkpoint、H1 子包或文档声明当作 completion。
- 不保留 D1/R1 作为 V2 成功或兼容路径。

## Acceptance

- manifest、生产入口、状态键、分支与权威 V2 图完全一致。
- 入口精确返回 `HarnessRunReceipt(branch,h1,decision,final,state)`。
- approved 是唯一开发准入；revise/rejected 永不产生 final。
- validator 检查 portable core、schema、入口、图、适配器、eval、依赖锁定、
  legacy 禁入与 release builder。
- release builder 对 source、staging、ZIP 解包态逐层复验，checksum manifest
  仅含相对路径。
- 真实 H1-A/B/assembly/C 整链测试通过，且没有 patch H1 validators。

## Verification

```powershell
uv run --offline --with-requirements harnesses/novel-conception-autonomous/requirements.txt `
  python harnesses/novel-conception-autonomous/validators/validate_harness.py
uv run --offline --with-requirements harnesses/novel-conception-autonomous/requirements.txt `
  python -m unittest harnesses.novel-conception-autonomous.tests.test_harness_integration -v
uv run --offline --with-requirements harnesses/novel-conception-autonomous/requirements.txt `
  python harnesses/novel-conception-autonomous/tools/build_release.py
```

## Stop conditions

- 任一上游 production validator 不能验证其正式 package。
- 作者决定不是外部密封事件，或不绑定当前 P1/H1/HTML。
- coordinator 不是当前 B0–P1 前缀，或 H1 workspace 不是当前 rendered 状态。

## Handoff

向 TASK-016 交付唯一整链入口、三分支运行证据、validator 报告、发布包与相对
checksum manifest。
