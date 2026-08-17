---
name: novel-conception-autonomous
description: 将已批准的完整小说构思访谈结果生产化为 V2 小说构思机器包、人类评审片段和 HTML，并在外部作者决定后生成最终开发准入或确定性返工路由。用于从访谈结果开始运行或恢复完整 B0→S1→W1→E1→T1→C1→Q1→P1→H1 构思链；不得使用旧 D1/R1 路径。
---

# 小说构思自主生产调度

这是完整构思链的唯一生产入口。领域内容仍由十个独立技能拥有；本技能只负责准入、
唯一 owner 调度、持久状态、返工、恢复、作者门和最终交付。

完整读取 `dependency-spec.json`、`agent.md`、`workflow.md`、`rules.md`、
`docs/input-contract.md` 和 `docs/output-contract.md`。在 repo-shaped 发布包中，这些
文件位于 `harnesses/novel-conception-autonomous/`；源码树中从当前适配器向上两级定位。

<!-- ADAPTER-CONTRACT:BEGIN -->
{
  "schema_version": "2.1",
  "manifest_name": "novel-conception-autonomous",
  "entrypoint": "runtime.production_orchestrator:initialize_production_run",
  "resume_entrypoint": "runtime.production_orchestrator:resume_production_run",
  "ordered_steps": [
    {"order": 1, "id": "verify-approved-interview-input"},
    {"order": 2, "id": "initialize-or-resume-production-run"},
    {"order": 3, "id": "dispatch-exact-stage-owner"},
    {"order": 4, "id": "persist-and-revalidate-transaction"},
    {"order": 5, "id": "forward-external-author-decision"},
    {"order": 6, "id": "report-authoritative-result"}
  ],
  "authority": {
    "author_decision": "external-author",
    "run_state": "production-orchestrator",
    "domain_content": "exact-stage-owner"
  },
  "forbidden": [
    "synthesize-author-decision",
    "own-run-state",
    "redefine-run-state",
    "legacy-success",
    "semantic-owner-fallback",
    "bypass-work-order"
  ]
}
<!-- ADAPTER-CONTRACT:END -->

1. 验证 I0–I5 完成记录、V1/V2 批准、作者批准和访谈状态属于同一当前基线。 (`verify-approved-interview-input`)
2. 新运行调用 `runtime.production_orchestrator.initialize_production_run`；已有运行只能调用 `resume_production_run`，不得从记忆重建状态。 (`initialize-or-resume-production-run`)
3. 调用 `issue_stage_work` 取得唯一工作单，并严格按 `dependency-spec.json` 调用 owner 的受控 start/submit/run API；提交的 `actor` 必须等于工作单 `required_actor`，禁止备用技能和手写 completion。 (`dispatch-exact-stage-owner`)
4. 通过 `execute_stage_work(actor=...)` 或 `commit_h1_workspace(actor=...)` 提交正式 receipt；失败后重新加载，包孤儿只能在 owner validator 通过并携带同一 actor 后走 recovery API。 (`persist-and-revalidate-transaction`)
5. H1-C 后先单独发布 H1 并进入 `waiting_author`；只转发外部密封的 `approved / revise / rejected`，不得生成作者决定。 (`forward-external-author-decision`)
6. `approved` 才发布 final；`revise` 报告确定性 owner 和恢复点；`rejected` 停止。所有结果报告当前持久 state、包路径和 completion。 (`report-authoritative-result`)

## 固定调用链

`B0 → S1 → W1 → E1 → T1 → C1 → Q1 → P1 → H1-A plan → H1-B → H1-A assemble → H1-C → H1 completion → external author decision → approved-only final`。

每一步开始前必须运行依赖验证器。工作单、gate、state、workspace、manifest、completion
和外部决定均是哈希绑定的不可变证据。旧 `run_from_rendered_h1` 只保留兼容既有调用，
不得再作为新构思的入口。
