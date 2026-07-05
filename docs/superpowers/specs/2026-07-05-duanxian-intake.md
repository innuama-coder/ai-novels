# 小说需求表：「断线」

## 修订记录

| 版本 | 日期 | 作者 | 变更摘要 | 状态 |
|---|---|---|---|---|
| v0.1 | 2026-07-05 | Codex | 使用 `novel-intake-workflow` 从仓库原始 idea 与前置材料整理 intake brief | 废弃 |
| v0.2 | 2026-07-05 | Codex | 按“由简入繁”原则大幅精简，只保留 intake 最小核心信息 | 待确认 |

## Intake Brief

| 字段 | 内容 |
|---|---|
| 项目名称 | 「断线」 |
| 原始 idea | 从《超脑48小时》的“记忆移植 + 任务压力”获得启发，但不写人类换脑；改为“前序人类记忆被注入数字生命体”，重点放在数字生命体的自我意识觉醒。 |
| 核心意图 | 写一个关于记忆、身份边界和非人意识诞生的近未来科幻故事。核心问题是：承载他人记忆的非人存在，能否形成属于自己的意识和情感。 |
| 硬约束 | `KEEP-01` 主体必须是数字生命体，不是被换脑的人类。<br>`KEEP-02` 核心变化必须是意识觉醒/进化，不是记忆衰退。<br>`AVOID-01` 必须避免照搬《超脑48小时》的罪犯换脑、48 小时倒计时和人性改造路径。 |
| 参考对象 | 《超脑48小时》：只参考“记忆移植 + 任务压力”的情节引擎，不能照搬设定和人物路径。 |
| 开放问题 | `OPEN-01` proposal 需要决定这部小说的整体结构、主线和结局方向。<br>`OPEN-02` proposal 需要决定数字生命体、技术员、前序人类三者之间的核心关系。<br>`OPEN-03` proposal 需要决定参考对象之外还需要哪些风格或题材参照。 |
| 交接状态 | `ready_with_open_questions` |
| 确认状态 | 待确认。本文只冻结最小核心信息；旧 PRD/HLD/LLD/writing 文档均不在 intake 阶段冻结。 |

## 非冻结说明

旧 PRD、HLD、LLD、writing 和 survey 中的大量内容只能作为后续 proposal 参考材料，不能反向写入 intake 需求表。proposal 可以重新取舍、重组或废弃其中的具体设定。

## Traceability

| 来源 | 用途 |
|---|---|
| `docs/superpowers/specs/2026-06-06-digital-life-novel-design.md` | 提取原始 idea 与核心差异 |
| `docs/plan-prd-research.md` | 证明部分后续问题仍未冻结 |
| `docs/superpowers/specs/2026-07-05-novel-creation-workflow-design.md` | 校验 intake 保持最小核心，不进入 proposal/PRD/HLD |
