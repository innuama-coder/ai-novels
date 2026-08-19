# HA1 implementation plan and realized design

## 1. 契约冻结（已实现）

以 HA1 的单一 owner、`[HB0]` 拓扑、allowlist、HDD、stable IDs、authority/ownership 和 package-external result 为不可绕过的外壳。`runtime-contract.json` 将 canonical 文件、required objects、forbidden keys 和下游能力变成 runtime 可读取常量。

## 2. Agent 语义流程（已实现为 skill instructions）

Agent 按“准入 → 未决处分 → 义务盘点 → 至少两个实质候选 → 压力测试与选择 → canonical 投影 → adversarial review”执行。五份有序 evidence 分别承担 dependency、obligation、option、projection 和 self-review 证据，避免只提交一个无比较理由的结构答案。

## 3. 确定性运行时（已实现）

Runtime 验证 work order、input gate、HB0 completion、reads、HDD、draft 文件集合、证据顺序和 canonical 结构。HA1 专属检查覆盖：unit 顺序从 0 连续、unit 归属已知 phase、chapter 归属已知 unit、turning anchor 指向有效 unit、state contract 恰好覆盖全部 unit。所有 forbidden keys 递归拒绝。

Runtime 根据已冻结代数发布：合法候选 → exact ready package；Agent draft 缺陷 → revise/local_candidate；`required_now` → blocked/author_required。它计算 hash、manifest、completion/result，不做结构优劣评分。

## 4. 训练与回归证据（已实现）

P01 验证正常 ready；N01 删除 turning anchor，验证 named defect revise；B01 注入场景级字段，验证边界 revise。Fixtures 在运行前密封并由 manifest hash 保护。六维证据将自动化事实与语义验收依据分栏。

## 5. 当前不做事项

本实现不增加浏览器、人审 HTML、真实 HLD 全链执行或任意小说质量评分；这些属于其他技能/Harness 或父级集成验收。若未来公共 work-order schema 调整，应修改 Harness 兼容层并重新冻结 fixtures，不能在 HA1 内静默接受双契约。
