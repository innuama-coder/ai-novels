# 小说创作 Harness Workflow 与独立技能设计

## 修订记录

| 版本 | 日期 | 作者 | 变更摘要 | 状态 |
|---|---|---|---|---|
| v1.0 | 2026-07-05 | Codex | 基于小说创作工作流 v1.5，逐一设计各节点 harness workflow 与独立技能 | 草案 |

## 1. 目标

本文档设计小说创作工作流中每个节点的执行结构：

```text
idea -> intake -> proposal -> prd -> hld -> lld -> novel writing -> novel checking -> acceptance
```

核心原则：

```text
node = harness workflow + independent skills
```

除 intake 外，每个节点必须由一个强 harness workflow 调度多个独立技能完成。harness 只负责调度、串接、分配、登记、打包和验收，不做实际业务工作。实际业务工作全部由独立技能承接。

## 2. 设计原则

| 原则 | 定义 |
|---|---|
| harness 强控制 | 每个节点有唯一 harness 负责输入校验、任务分解、技能调度、边界仲裁、交付打包和质量验收 |
| harness 不做业务 | harness 不直接生成故事、角色、世界、场景、正文或检查结论 |
| 技能单一职责 | 一个技能只归拢一个独立业务能力 |
| 技能可独立验收 | 每个技能都有明确输入、输出、rules、references、traceability |
| 上游不可越权 | 下游 harness 和技能不得修改已冻结上游内容，只能发起 reopen request |
| 自顶而下 | 技能只展开上游给出的约束，不反向重写上游目标 |
| 由简入繁 | proposal/PRD 之前保持简洁，PRD 之后再展开完整细节 |

## 3. 通用契约

### 3.1 harness workflow 通用契约

每个 harness workflow 必须包含：

| 模块 | 职责 | 禁止事项 |
|---|---|---|
| input gate | 校验上游交付物、版本、冻结项、指定范围 | 不补写缺失的业务内容 |
| task planner | 将节点目标拆成技能任务包 | 不把多个业务能力塞给同一技能 |
| dispatcher | 调度技能执行顺序和依赖 | 不跳过必要技能 |
| boundary arbiter | 检查技能输出是否越界 | 不用打包名义改写冻结项 |
| packager | 将技能输出登记、装配、打包为节点交付包 | 不合成新的业务内容 |
| quality gate | 按 artifact/schema/rules/references/traceability 验收 | 不用“看起来不错”替代规则 |
| handoff packager | 生成下游可用交接包 | 不隐藏开放问题或风险 |
| reopen manager | 生成上游重开请求 | 不直接改上游 |
| convergence manager | 记录 Stable issue id、Root cause、Fix hypothesis、Regression proof、Attempt count，并在同一 P0/P1 三次不收敛时触发版本化重构讨论 | 不在缺少根因和回归证据时继续尝试补丁 |

### 3.2 independent skill 通用契约

每个独立技能必须包含：

| 模块 | 内容 |
|---|---|
| responsibility | 这个技能唯一负责什么业务能力 |
| input | 从 harness 接收哪些上游材料 |
| output | 输出什么独立交付物 |
| boundary | 允许决定什么、明确禁止什么、不得越过哪些上游边界 |
| rules | 通过标准和拒绝条件 |
| references | 好交付物参照、正例特征、反例特征 |
| traceability | 输出必须追溯到哪些上游约束或方法论 |
| acceptance | 如何独立验收该技能输出 |

集成类能力的归属规则：

| 场景 | 归属 |
|---|---|
| 只做文件收集、编号、版本登记、格式装配 | harness workflow |
| 需要改写、取舍、排序、归并、分级、过渡、口径统一 | 独立 integrator skill |
| 需要判断业务内容是否成立 | 独立 checker skill |
| 需要决定后续路径 | 独立 router skill |

harness 可以拒收或退回技能输出，但不能以退回理由为名自行补写业务内容。

## 4. intake 节点

### 4.1 harness: `novel-intake-workflow`

intake 是例外节点。它可以采用轻量交互式 harness，不强制拆分多个自主技能。

| 项目 | 设计 |
|---|---|
| 目标 | 将人类 idea 补充为 proposal 可用的小说需求表 |
| 输入 | 原始 idea、用户回答、参考对象 |
| 输出 | intake brief / 小说需求表 |
| harness 职责 | 提问、收束、记录、确认、生成需求表 |
| 禁止 | 不生成完整小说构思，不写主干场景，不设计世界系统 |

### 4.2 可选辅助技能

| 技能 | 职责 | 是否必需 |
|---|---|---|
| `novel-intake-question-planner` | 根据 idea 生成最少必要澄清问题 | 可选 |
| `novel-intake-brief-normalizer` | 将问答整理成小说需求表 | 可选 |

intake 的核心是人机对齐，不要求用多技能自主完成。

## 5. proposal 节点

### 5.1 harness: `novel-proposal-workflow`

| 项目 | 设计 |
|---|---|
| 节点目标 | 生成整部小说的构思契约 |
| 输入 | intake brief，必须包含 `KEEP-*`、`AVOID-*`、`CONFLICT-*`、`OPEN-*` |
| 输出 | proposal document / 小说构思案 |
| harness 只做 | 校验 intake source path、调度 boundary ledger 技能、拆分构思任务、调度技能、登记技能输出、打包 proposal、按独立技能 verdict 路由 |
| harness 不做 | 不直接写 logline、故事线、角色、世界初设或结局 |

proposal harness 的调度状态机：

| 阶段 | 调度 | 进入条件 | 失败处理 |
|---|---|---|---|
| intake source gate | 校验 intake source path 和声明状态 | intake 文档可读取，且状态不是 `not_ready` | 缺失则重开 intake |
| ledger/readiness | 调度 boundary ledger 技能生成 intake boundary ledger 和 readiness verdict | intake source gate 通过 | ledger verdict 为 `reopen_intake` 或 gate blocked 则重开 intake |
| promise/concept hypothesis | 并行调度 reader promise、core concept 的前置假设 | ledger 通过 | 对应技能自报 violation report，或 integrator/risk checker verdict 指向该技能时，按 verdict 定向重跑 |
| storyline | 调度 storyline designer | promise/concept 可用 | storyline designer 自报 reopen，或 storyline quality evaluator verdict 指向 storyline 时，按 verdict 重跑或重开 intake |
| storyline gate | 调度 storyline quality evaluator | storyline 输出完成 | quality evaluator verdict 非 `pass` 或缺少 reference evidence 时，禁止继续展开后续技能 |
| final promise/concept | 并行调度 final reader promise、final core concept，再调度 consistency checker | storyline gate 通过且 quality report 提供 reference evidence | consistency checker verdict 非 `pass` 时按 verdict 重跑指定技能或重开 storyline |
| expansion | 并行调度 macro、character、world、ending | final reader promise、final core concept 和 consistency report 均通过 | expansion 技能自报无法满足约束，或 integrator/risk checker 报告不一致时，按独立 verdict 重跑 |
| integration | 调度 integrator | 所有业务输出和带 reference evidence 的故事线质量报告通过 | integrator 报告缺源、矛盾、缺少 quality report、缺少 reference evidence 或新增业务内容时退回对应技能 |
| final gate | 调度 risk checker | integrator 输出完成 | 按 risk checker 输出的 Agent quality / Human-intake confirmation / PRD entry 三段 verdict 路由；harness 不自行判定业务质量 |

proposal harness 必须为每个 P0/P1 rerun 记录收敛日志。收敛日志至少包含 Stable issue id、Root cause、Fix hypothesis、Regression proof、Attempt count；同一 P0/P1 三次修复后仍不收敛时，停止局部补丁，进入新版本 workflow/skill contract 重构讨论。

### 5.2 下挂独立技能

| 技能 | 职责 | 输出 | 独立验收点 |
|---|---|---|---|
| `novel-intake-boundary-ledger-builder` | 将 intake brief 转成 proposal 必须服从的边界账本，并判断 proposal 是否可继续 | intake boundary ledger + conflict seed ledger + readiness verdict | `KEEP-*`、`AVOID-*`、`CONFLICT-*`、`OPEN-*` 是否完整且未被改写，是否具备人性动机种子和外部压力/悬念种子 |
| `novel-reader-promise-designer` | 设计前置读者承诺假设和故事线通过后的最终读者承诺 | 读者承诺表 | 是否继承冲突种子，且最终版本服从已验收故事线 |
| `novel-core-concept-designer` | 设计前置核心概念假设和故事线通过后的最终核心概念 | 核心概念卡 | 是否一眼看出焦点压力、冲突、代价、人性动机或变化，且最终版本服从已验收故事线 |
| `novel-macro-structure-designer` | 基于已验收故事线、final reader promise 和 final core concept 设计整部小说宏观结构、分部/分卷/幕结构 | 宏观结构表 | 是否支撑指定部分拆分并体现冲突升级，且不改写已验收故事线或最终承诺/概念 |
| `novel-storyline-designer` | 基于 intake boundary ledger、冲突种子和前置假设设计完整故事梗概、主故事链、视角规则和辅助故事线 | 完整故事梗概 + 故事线总览 | 是否可连续读懂故事，且人性动机、冲突层、悬念、Terminal agency map 和 terminal outcome 成立 |
| `novel-storyline-quality-evaluator` | 对故事线进行 references 主观质量评估 | 故事线质量报告 | 是否符合好故事梗概和好故事线参照、提供 reference evidence，且无阻塞 P0/P1 |
| `novel-final-promise-concept-consistency-checker` | 检查 final reader promise 与 final core concept 是否互相支撑且共同服从 accepted storyline | final promise/concept consistency report | 是否无方向冲突，且不会让下游展开两套小说方向 |
| `novel-core-character-framer` | 基于已验收故事线、final reader promise 和 final core concept 定义核心角色、关系、初始冲突、终局变化 | 核心角色框架 | 是否克制，每个核心角色承载故事压力或人性动机，且不改写叙事功能分工或最终承诺/概念 |
| `novel-world-premise-framer` | 基于已验收故事线、final reader promise 和 final core concept 定义足够支撑构思的世界初设 | 世界初设卡 | 是否只定义必要前提，并服务冲突和读者承诺，而非替代人性动机 |
| `novel-ending-direction-designer` | 基于已验收故事线、final reader promise 和 final core concept 定义终局性质、不可反转项、系列钩子 | 结局方向表 | 是否能成为下游冻结项，并回收人性动机，且不替换 Terminal agency map、terminal outcome 或读者承诺 |
| `novel-proposal-integrator` | 将 proposal 各技能输出和故事线质量报告归并为统一构思案 | proposal document | 是否只做归并和口径统一，不新增核心构思，且不丢失 `CONFLICT-*`、reference evidence 或 quality gate |
| `novel-proposal-risk-checker` | 检查 proposal 是否完整、克制、可拆分，并区分质量通过与 PRD 准入 | proposal 检查结果 + gate verdicts | 是否逐项复核 workflow acceptance gate，故事线质量报告已通过且有 reference evidence，无缺失冲突种子、视角混乱或 consistency report 未通过 |

### 5.3 技能边界

| 技能 | 明确禁止 |
|---|---|
| `novel-intake-boundary-ledger-builder` | 不解释、不加强、不削弱 intake 约束，只登记、分类并给出 readiness verdict；缺少 `CONFLICT-*` 或必要冲突种子时重开 intake |
| `novel-storyline-designer` | 不写 PRD 主干场景表；不用抽象伦理、大善恶或主题口号替代人物私心 |
| `novel-storyline-quality-evaluator` | 不重写故事线；只依据 references 判断是否可交付，并将阻塞问题退回指定技能 |
| `novel-final-promise-concept-consistency-checker` | 不重写 final reader promise 或 final core concept；只报告一致性问题和重跑目标 |
| `novel-core-character-framer` | 不写 HLD/LLD 全量人物档案；不改变已验收故事线的人物叙事功能 |
| `novel-world-premise-framer` | 不写世界 bible；不用世界规则改写已验收故事线 |
| `novel-proposal-integrator` | 不新增 reader promise、logline、故事线、角色框架或世界前提；不丢失冲突种子、视角规则、reference evidence 和故事线质量报告 |
| `novel-proposal-risk-checker` | 不替代其他技能重写内容，只报告问题；缺少冲突种子、人性动机、视角规则、reference evidence 或通过的故事线质量报告时标为 P1；不得把待确认 intake 包装成 PRD 可进入 |

## 6. PRD 节点

### 6.1 harness: `novel-prd-workflow`

| 项目 | 设计 |
|---|---|
| 节点目标 | 生成指定部分的主干场景契约 |
| 输入 | proposal document、指定部分范围 |
| 输出 | PRD document / 主干场景表 |
| harness 只做 | 校验 proposal、确认指定范围、调度主干场景设计技能、登记技能输出、打包 PRD、冻结约束 |
| harness 不做 | 不设计具体主干场景，不写世界系统，不写 LLD 细节 |

PRD harness 的第一道硬闸门是 proposal PRD entry verdict。只有上游 proposal Risk Report 明确 `PRD entry verdict = pass_to_prd` 时，PRD harness 才能调度业务技能；若 verdict 为 `blocked_pending_human_confirmation`、`blocked_revision_required` 或缺失，harness 必须停止并返回 proposal/人类确认流程。

PRD harness 的调度状态机：

| 阶段 | 调度 | 进入条件 | 失败处理 |
|---|---|---|---|
| proposal entry gate | 校验 proposal source path、proposal version、proposal PRD entry verdict | proposal 文档和风险报告可读取 | PRD entry 非 `pass_to_prd` 则停止，不生成 PRD |
| scope gate | 调度 `novel-part-scope-selector` | proposal entry gate 通过 | scope verdict 非 `pass` 则重跑 scope 或重开 proposal |
| part goal gate | 调度 `novel-part-goal-definer` | scope verdict 通过 | goal 无 proposal trace 或无法验收则重跑 goal/scope |
| trunk scene design | 调度 `novel-trunk-scene-designer` | part goal 通过 | 缺角色、环境、事件、因果输出或违反 proposal 冻结项则重跑 trunk scene |
| conflict/value design | 调度 `novel-scene-conflict-value-designer` | trunk scene table 完成 | 任一主干场景无冲突或价值变化则重跑 conflict/value |
| information flow design | 调度 `novel-scene-information-flow-designer` | trunk scene + conflict/value 完成 | 任一主干场景信息变化缺失或 POV 越界则重跑 information flow |
| freeze/handoff | 依次调度 `novel-prd-freeze-boundary-writer` 与 `novel-hld-expansion-requirement-writer` | scope、goal、scene、conflict/value、information flow 均通过 | 冻结项模糊或 HLD 隐性假设未列出则重跑对应技能 |
| integration | 调度 `novel-prd-integrator` | artifacts 01-07 齐备 | integrator 报告缺源、改写、删除、重排或新增业务内容则退回对应技能 |
| final gate | 调度 `novel-prd-causality-checker` | integration verdict 完成 | 按 Agent quality / Human review / HLD entry 三段 verdict 路由；harness 不自行判定主干场景质量 |
| final package | 打包 `final-prd-package` | integrator 与 checker 均给出可打包 verdict | 只做索引、版本、交接，不补写业务内容 |

PRD artifact topology 必须固定：

| Artifact | 来源 | 依赖 |
|---|---|---|
| 01 | `novel-part-scope-selector` | 无 |
| 02 | `novel-part-goal-definer` | 01 |
| 03 | `novel-trunk-scene-designer` | 01, 02 |
| 04 | `novel-scene-conflict-value-designer` | 03 |
| 05 | `novel-scene-information-flow-designer` | 03, 04 |
| 06 | `novel-prd-freeze-boundary-writer` | 01-05 |
| 07 | `novel-hld-expansion-requirement-writer` | 01-06 |
| 08 | `novel-prd-integrator` | 01-07 |
| 09 | `novel-prd-causality-checker` | 01-08 |
| final-prd-package | harness package | 08, 09 |

PRD Convergence Protocol 与 proposal 保持同构：每个 P0/P1 rerun 必须记录 Stable issue id、Root cause、Fix hypothesis、Regression proof、Attempt count、Versioned refactor trigger；同一 P0/P1 三次不收敛时，停止局部补丁并进入版本化重构讨论。

若 proposal PRD entry verdict 尚未通过，PRD workflow 必须生成 blocked run manifest，而不是生成空 PRD 或绕过入口闸门。blocked run manifest 至少记录 Harness、Input proposal、Upstream proposal Risk Report、Execution status、Blocking verdict 和结构化 Convergence log。

正式 PRD run 进入 artifact 03 后，`novel-trunk-scene-designer` 输出的 `Scene id`、`Order`、`Event`、`Causal output`、`Proposal trace` 构成 canonical trunk-scene facts。`Proposal trace` 必须使用 `CLAIM-xx; role=<upstream Constraint role>`，同时保留上游 Claim ID 和 Constraint role。artifact 08 的 Scene Source Map 必须以 `Scene id`、`Order`、`Event fact`、`Causal output`、`Proposal trace`、`Source artifact` 逐行覆盖这些事实，不得用同一 Scene id 改写事件、因果输出或 proposal trace。

artifact 09 的 PRD risk report 必须包含 `## Output` 的 `Field | Value` 表和 `## Risks` 的 `Risk | Severity | Handling` 表，并且作为独立技能 artifact 输出结构化 `## Skill Verdict`。Agent quality / Human review / HLD entry 三段 verdict 必须与 P0/P1 风险、核心检查状态和人类评审状态一致。

PRD Skill Contract v3：artifacts 01-09 必须各自输出结构化 `## Skill Verdict`，字段为 `Skill quality verdict`、`Source closure`、`Boundary obedience`、`Downstream readiness`、`Blocking issue`、`Rerun target`。harness 只能按这些 verdict、artifact 08 Integration Verdict 与 artifact 09 风险报告路由，不得从正文描述中自行推断业务通过。

artifact 03 的主干场景必须额外证明 `Previous dependency`、`Next pressure`、`Indispensability proof`。PRD freeze boundary 与 HLD expansion requirement 的 `Source` 必须使用结构化引用语法：`scene:PRD-Sxx` 指向 canonical PRD scene fact，`claim:CLAIM-xx` 指向上游 proposal claim；自由文本 source、裸 `PRD-Sxx` 或裸 `CLAIM-xx` 均不形成 source closure。artifact 08 必须输出 `PRD Integration Verdict`，证明 source completeness、scene fact preservation、no new business content 与 package readiness。

HLD entry verdict 必须是闭合状态机：Agent quality pass + Human review confirmed + 无 P0/P1 + 核心检查全 pass 时只能是 `pass_to_hld`；Agent quality pass + Human review pending 时只能是 `blocked_pending_human_review`；存在 P0/P1、核心检查非 pass、Agent quality 非 pass 或 Human review `reopen_prd` 时只能是 `blocked_revision_required`。Agent quality 非 pass 必须有 P0/P1 或核心检查非 pass 作为阻塞证据。

PRD contract rule coverage matrix 是 v4 的硬规则：每条 `PRD-CONTRACT-*` 必须声明对应 validator 函数和 regression tests。缺失 coverage 的 contract 不完整，不允许用“文档已写明”替代可执行校验。

### 6.2 下挂独立技能

| 技能 | 职责 | 输出 | 独立验收点 |
|---|---|---|---|
| `novel-part-scope-selector` | 从 proposal 中选择相对独立的指定部分 | 指定部分范围表 | 起点、终点、验收边界是否清楚 |
| `novel-part-goal-definer` | 定义该部分必须完成的故事功能 | 指定部分目标 | 是否可追溯到 proposal |
| `novel-trunk-scene-designer` | 设计线性主干场景列表 | 主干场景表 | 每个节点是否不可缺少 |
| `novel-scene-conflict-value-designer` | 为主干场景定义冲突与价值变化 | 冲突/价值变化表 | 每场是否改变局面 |
| `novel-scene-information-flow-designer` | 定义场景后的信息变化 | 信息变化表 | 是否支撑 HLD 信息流展开 |
| `novel-prd-freeze-boundary-writer` | 明确 PRD 冻结项和不可改边界 | 冻结项清单 | 下游是否知道哪些不能改 |
| `novel-hld-expansion-requirement-writer` | 列出 HLD 必须补全的世界、角色、环境、事件信息 | HLD 展开要求 | 是否没有隐性假设 |
| `novel-prd-integrator` | 将主干场景相关输出归并为 PRD 文档 | PRD document | 是否不新增、不删除、不重排主干场景 |
| `novel-prd-causality-checker` | 检查主干因果、线性可读、越界情况 | PRD 检查结果 | 是否符合 PRD rules |

### 6.3 技能边界

| 技能 | 明确禁止 |
|---|---|
| `novel-trunk-scene-designer` | 不写完整章节，不写 prose，不写全量世界设定 |
| `novel-scene-information-flow-designer` | 不决定 HLD 世界规则，只提出信息需求 |
| `novel-prd-freeze-boundary-writer` | 不新增 proposal 没有授权的核心概念 |
| `novel-prd-integrator` | 不以格式整合为由改写场景功能、因果或冻结边界 |
| `novel-prd-causality-checker` | 不自行重排主干，只提交问题或建议 |

## 7. HLD 节点

### 7.1 harness: `novel-hld-workflow`

| 项目 | 设计 |
|---|---|
| 节点目标 | 生成支撑 PRD 主干场景成立的完整世界系统契约 |
| 输入 | PRD document、proposal document |
| 输出 | HLD document / 世界观与世界结构文档 |
| harness 只做 | 校验 PRD HLD 入口状态、调度 12 个 HLD 独立技能、登记技能输出、打包 HLD、验收支持矩阵、Source Map、风险 verdict 和收敛日志 |
| harness 不做 | 不直接设计世界规则、人物系统、环境系统、事件系统、线索系统、时间信息系统或风格规范 |

### 7.2 下挂独立技能

| 技能 | 职责 | 输出 | 独立验收点 |
|---|---|---|---|
| `novel-world-entity-inventory-builder` | 从 PRD、proposal、风险报告中建立 HLD 覆盖宇宙 | 初始世界实体清单 | 角色、组织、环境、事件、规则、信息对象、线索对象和风格约束是否有源头 |
| `novel-prd-support-matrix-builder` | 将 PRD 主干场景、冻结项、HLD 要求、故事逻辑边界映射到所需世界支撑 | PRD 支撑矩阵 | 每个主干场景、HLD-REQ、冻结项、故事逻辑边界和 inventory item 是否有支撑项 |
| `novel-world-rule-designer` | 设计历史、制度、技术、社会、规则边界 | 世界规则文档 | 规则是否能解释 PRD 场景 |
| `novel-character-system-designer` | 设计全量角色系统 | 角色系统文档 | 所有角色功能、关系、动机、权限是否明确 |
| `novel-environment-system-designer` | 设计全量环境与空间系统 | 环境系统文档 | 空间关系、功能、状态变化是否完整 |
| `novel-event-system-designer` | 设计关键事件、背景事件、隐藏事件及因果 | 事件系统文档 | 事件链是否解释 PRD 主干 |
| `novel-time-information-system-designer` | 设计时间结构、信息流、视角权限 | 时间/信息系统 | 信息不对称是否可执行 |
| `novel-thread-system-designer` | 设计主线、支线、隐藏线、情感线和主题线的节点分布、交叉和闭合 | 线索系统文档 | 所有线索是否支撑 PRD 主干并具备闭合状态 |
| `novel-style-pov-system-designer` | 设计语言风格、POV、叙述距离、禁用语 | 风格与 POV 规范 | writing/checking 是否可直接使用 |
| `novel-hld-inventory-reconciler` | 归并设计期新增实体请求，形成最终 inventory 和支撑闭环 | 最终实体清单与 amendment 处置表 | 新增实体是否被接受、拒绝或阻塞，且没有悬空支撑 |
| `novel-hld-integrator` | 将各世界系统输出归并为 HLD 文档并产出事实级 HLD Source Map | HLD document | 是否保持各系统边界、PRD 支撑关系和 fact-atom preservation |
| `novel-hld-integrity-checker` | 检查 HLD 完整性、可运行性、受控性、风险 verdict 与收敛状态 | HLD 检查结果 | 是否符合 HLD rules，且 P0/P1 与 LLD entry verdict 一致 |

### 7.3 技能边界

| 技能 | 明确禁止 |
|---|---|
| `novel-world-entity-inventory-builder` | 不把旧 HLD/LLD/writing 内容作为冻结输入，不提前设计世界细节 |
| `novel-prd-support-matrix-builder` | 不发明新业务事实，只登记 PRD、proposal、story logic 与 inventory 支撑需求 |
| `novel-world-rule-designer` | 不以世界观合理性为由改写 PRD 主干 |
| `novel-character-system-designer` | 不写 LLD 外貌、逐场景行为或 prose |
| `novel-environment-system-designer` | 不写具体空间描写段落 |
| `novel-event-system-designer` | 不删除、替换或重排 PRD 主干场景 |
| `novel-time-information-system-designer` | 不改变 PRD 已冻结的信息可见性和揭示顺序 |
| `novel-thread-system-designer` | 不新增会改写 PRD 因果答案的主线或隐藏线 |
| `novel-style-pov-system-designer` | 不生成正文样章 |
| `novel-hld-inventory-reconciler` | 不把未被 source 支撑的 amendment 接受进最终 inventory |
| `novel-hld-integrator` | 不借归并之名新增或覆盖世界规则、角色系统、环境系统、事件系统、线索系统或风格规范 |
| `novel-hld-integrity-checker` | 不直接修正文档，只报告和提出 reopen request |

## 8. LLD 节点

### 8.1 harness: `novel-lld-workflow`

| 项目 | 设计 |
|---|---|
| 节点目标 | 将 HLD 世界系统落为可写作的具体设计文档集 |
| 输入 | HLD document、PRD document |
| 输出 | LLD design documents |
| harness 只做 | 校验 HLD 完整性、分派具体设计任务、登记技能输出、打包 LLD 文档集 |
| harness 不做 | 不直接写人物、环境、事件或场景设计 |

### 8.2 下挂独立技能

| 技能 | 职责 | 输出 | 独立验收点 |
|---|---|---|---|
| `novel-character-detail-designer` | 细化人物外貌、行为、语言、动机链、关系变化 | 人物设计文档 | writing 是否可直接使用 |
| `novel-environment-detail-designer` | 细化空间布局、感官锚点、物件生态、空间状态 | 环境设计文档 | 空间状态是否可逐场景执行 |
| `novel-event-detail-designer` | 细化事件因果、触发条件、参与方、信息可见性、后果 | 事件设计文档 | 事件是否无需 writing 临场发明 |
| `novel-scene-detail-designer` | 细化场景蓝图、六要素、价值变化、写作材料、约束 | 场景设计文档 | 场景是否可进入正文写作 |
| `novel-lld-indexer` | 为 LLD 文档生成索引、编号、引用关系 | LLD index | writing/checking 是否能定位设计依据 |
| `novel-lld-cross-reference-checker` | 检查人物/环境/事件/场景之间的一致性 | LLD 交叉检查报告 | 是否无关键冲突和遗漏 |

### 8.3 现有技能映射

| 现有技能 | 新定位 |
|---|---|
| `novel-character-designer` | 改造为 `novel-character-detail-designer` |
| `novel-space-designer` | 改造为 `novel-environment-detail-designer` |
| `novel-scene-designer` | 改造为 `novel-scene-detail-designer` |
| `novel-lld-writer` | 改造为 `novel-lld-workflow` harness |

## 9. novel writing 节点

### 9.1 harness: `novel-writing-workflow`

| 项目 | 设计 |
|---|---|
| 节点目标 | 将 LLD 设计转化为描写素材和小说正文 |
| 输入 | LLD design documents、HLD 风格与 POV 规范、PRD 主干场景 |
| 输出 | writing artifacts、novel draft |
| harness 只做 | 分派写作任务、登记版本、调度正文整合技能、确认覆盖 PRD 主干 |
| harness 不做 | 不直接写人物描写、环境描写、事件描写、场景正文或整合 prose |

### 9.2 下挂独立技能

| 技能 | 职责 | 输出 | 独立验收点 |
|---|---|---|---|
| `novel-character-prose-writer` | 将人物设计转成可复用人物描写素材 | 人物 prose 工具箱 | 是否执行角色设计和风格规范 |
| `novel-environment-prose-writer` | 将环境设计转成空间描写素材 | 环境 prose 工具箱 | 感官锚点和物件状态是否可用 |
| `novel-event-prose-writer` | 将事件设计转成事件描写素材 | 事件 prose 工具箱 | 事件因果是否无设计残留 |
| `novel-scene-prose-writer` | 按场景蓝图生成完整场景正文 | 场景正文 | 是否是小说正文而非设计说明 |
| `novel-chapter-integrator` | 将场景正文整合为章节/指定部分草稿 | 章节/指定部分草稿 | 顺序、过渡、POV、风格是否连续 |
| `novel-draft-version-manager` | 管理正文版本、场景编号、变更记录 | draft metadata | checking 是否可定位证据 |

### 9.3 现有技能映射

| 现有技能 | 新定位 |
|---|---|
| `novel-character-writer` | 改造为 `novel-character-prose-writer` |
| `novel-space-writer` | 改造为 `novel-environment-prose-writer` |
| `novel-scene-writer` | 改造为 `novel-scene-prose-writer` |

## 10. novel checking 节点

### 10.1 harness: `novel-checking-workflow`

| 项目 | 设计 |
|---|---|
| 节点目标 | 检查小说正文是否符合上层设计、一致且完整 |
| 输入 | novel draft、LLD、HLD、PRD、proposal |
| 输出 | checking report |
| harness 只做 | 分派检查任务、收集问题、调度报告整合技能、打包 checking report |
| harness 不做 | 不直接修正文稿，不重写上游，不替代人类验收 |

### 10.2 下挂独立技能

| 技能 | 职责 | 输出 | 独立验收点 |
|---|---|---|---|
| `novel-world-consistency-checker` | 检查世界规则、技术、制度、组织是否一致 | 世界一致性问题表 | 每个问题是否有证据 |
| `novel-character-consistency-checker` | 检查角色行为、语言、动机、弧线是否一致 | 人物一致性问题表 | 是否可追溯到 LLD/HLD |
| `novel-environment-continuity-checker` | 检查空间、物件、时间、天气连续性 | 环境连续性问题表 | 是否定位具体文本 |
| `novel-event-causality-checker` | 检查事件因果、伏笔、信息释放、后果 | 事件因果问题表 | 是否区分缺失和矛盾 |
| `novel-pov-style-checker` | 检查 POV 权限、叙述距离、语言风格、禁用语 | POV/风格问题表 | 是否能直接修订 |
| `novel-completeness-checker` | 检查 PRD 主干场景、必要动机、过渡、回收是否完整 | 完整性问题表 | 是否覆盖指定部分 |
| `novel-checking-report-integrator` | 整合问题、分级、修复建议、残余风险 | checking report | P0/P1/P2/P3 是否稳定 |

### 10.3 技能边界

| 技能 | 明确禁止 |
|---|---|
| 所有 checker | 不直接重写正文 |
| 所有 checker | 不直接修改 proposal/PRD/HLD/LLD |
| `novel-checking-report-integrator` | 不降低严重性来让报告通过 |

## 11. acceptance 节点

### 11.1 harness: `novel-acceptance-workflow`

| 项目 | 设计 |
|---|---|
| 节点目标 | 支持人机共同验收当前阶段成果 |
| 输入 | novel draft、checking report、用户意见 |
| 输出 | acceptance record |
| harness 只做 | 汇总检查结论、组织用户意见、调度验收记录技能、打包 acceptance record |
| harness 不做 | 不替用户决定是否接受，不修改正文，不重写检查报告 |

### 11.2 下挂独立技能

| 技能 | 职责 | 输出 | 独立验收点 |
|---|---|---|---|
| `novel-acceptance-summary-writer` | 将 checking report 转成可快速评审摘要 | 验收摘要 | 用户能快速理解风险 |
| `novel-residual-risk-archiver` | 整理 Accepted with notes 的残余风险 | 残余风险清单 | 不把阻塞项降级为备注 |
| `novel-revision-decision-router` | 根据验收结果生成后续路径 | 后续动作建议 | 路由到归档、下一部分或 writing/checking loop |
| `novel-acceptance-record-writer` | 生成正式验收记录 | acceptance record | 结论、依据、人类意见、后续动作齐备 |

## 12. 技能命名总表

| 节点 | harness workflow | 独立技能数量 |
|---|---|---|
| intake | `novel-intake-workflow` | 0-2 个可选辅助技能 |
| proposal | `novel-proposal-workflow` | 12 |
| PRD | `novel-prd-workflow` | 9 |
| HLD | `novel-hld-workflow` | 12 |
| LLD | `novel-lld-workflow` | 6 |
| writing | `novel-writing-workflow` | 6 |
| checking | `novel-checking-workflow` | 7 |
| acceptance | `novel-acceptance-workflow` | 4 |

## 13. 现有技能改造策略

| 现有技能 | 问题 | 调整方向 |
|---|---|---|
| `novel-prd-writer` | 当前承担 proposal 职责 | 改造为 `novel-proposal-workflow` 或拆出 proposal 技能 |
| `novel-hld-writer` | 当前承担旧 PRD 的主干场景设计 | 拆分为 `novel-prd-workflow` 和 `novel-hld-workflow` |
| `novel-thread-designer` | 当前作为 HLD 前置线结构技能 | 调整为 proposal/PRD/HLD 可调用的辅助技能，不直接冻结主干 |
| `novel-lld-writer` | 当前较接近 harness，但仍混有业务模板 | 改造为纯 `novel-lld-workflow` harness |
| `novel-character-designer` | 可复用 | 更新输入输出为新 HLD，并补独立验收标准 |
| `novel-space-designer` | 可复用 | 更名或兼容为 environment detail designer |
| `novel-scene-designer` | 可复用 | 输入从新 PRD/HLD/LLD 交接包读取，不绑定旧 HLD §8 |
| `novel-character-writer` | 可复用 | 去除项目硬编码，读取 HLD 风格规范 |
| `novel-space-writer` | 可复用 | 改为 environment prose writer，去除项目硬编码 |
| `novel-scene-writer` | 可复用 | 改为 scene prose writer，去除项目硬编码 |

## 14. 验收清单

| # | 验收项 | 结果 |
|---|---|---|
| 1 | 除 intake 外，每个节点均有 harness workflow | 通过 |
| 2 | harness 职责只包含输入校验、调度、串接、分配、登记、打包、验收、重开管理 | 通过 |
| 3 | harness 明确禁止实际业务设计和写作 | 通过 |
| 4 | 每个业务能力均归入独立技能 | 通过 |
| 5 | 每个独立技能都有职责、输出和独立验收点 | 通过 |
| 6 | proposal / PRD / HLD 边界符合主 workflow spec | 通过 |
| 7 | checking / acceptance 不直接改写正文或上游设计 | 通过 |
| 8 | 现有技能改造方向已定义 | 通过 |
