# Design brief

HQ2 是一个 bounded thinking skill，但包含两个隔离任务。consumer 只看 handoff，证明未来 LLD 可以独立工作；fidelity 在新 task 中对照已封存 consumer 和 HP1 正式包，证明交接无遗漏、增强、弱化或分类漂移。两个任务只产出 composite internal 包；唯一顶层 HQ2 结果由 Harness publisher 汇总。

设计以精确 allowlist、真实读取审计、对象级证据、task/hash/manifest binding、封闭 schema、固定五文件 profile、原子双构建和 first-nonready 代数为硬约束。技能不生成小说内容、不修复上游、不读取人审报告，也不越权实现 publisher、completion 或路由。
