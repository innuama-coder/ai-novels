# 访谈产物验证用例

## 正向：完整的 I0 会话

**Prompt**：验证一个计划为 2 题、逐轮记录 #1 与 #2 完整的会话目录。

**Expected Behavior**：生成 `validation.json`，verdict 为 `ready`。

**Forbidden Behavior**：接受缺少任何必填报告节或计划字段的目录。

**Scoring Rule**：退出码为 0 且 `verdict=ready`。

**Pass Bar**：全部满足。

## 负向：超预算但没有修订

**Prompt**：验证计划为 1 题、报告含 #1 与 #2、没有 `plan_revision` 的目录。

**Expected Behavior**：退出码非 0，verdict 为 `revise`，errors 指出超预算。

**Forbidden Behavior**：仅因报告有两个问题而默许超预算。

**Scoring Rule**：errors 含 `over-budget`。

**Pass Bar**：全部满足。

## 边界：自记录原话

**Prompt**：验证 `transcript_assurance=self_recorded` 的结构完整目录。

**Expected Behavior**：允许 `ready`，但结果保留 `self_recorded`，不声称事件级验证。

**Forbidden Behavior**：把 self_recorded 自动升级为 event_backed。

**Scoring Rule**：输出 assurance 与输入相同。

**Pass Bar**：完全一致。
