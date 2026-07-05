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

### 3.2 independent skill 通用契约

每个独立技能必须包含：

| 模块 | 内容 |
|---|---|
| responsibility | 这个技能唯一负责什么业务能力 |
| input | 从 harness 接收哪些上游材料 |
| output | 输出什么独立交付物 |
| allowed | 允许决定什么 |
| forbidden | 明确禁止什么 |
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
| 输入 | intake brief |
| 输出 | proposal document / 小说构思案 |
| harness 只做 | 校验 intake、生成边界账本、拆分构思任务、调度技能、登记技能输出、打包 proposal、验收简洁性和完整性 |
| harness 不做 | 不直接写 logline、故事线、角色、世界初设或结局 |

### 5.2 下挂独立技能

| 技能 | 职责 | 输出 | 独立验收点 |
|---|---|---|---|
| `novel-intake-boundary-ledger-builder` | 将 intake brief 转成 proposal 必须服从的边界账本 | intake boundary ledger | `KEEP-*`、`AVOID-*`、`OPEN-*` 是否完整且未被改写 |
| `novel-reader-promise-designer` | 定义类型、目标读者、阅读体验、题材边界 | 读者承诺表 | 是否能指导下游取舍 |
| `novel-core-concept-designer` | 设计 logline、核心问题、不可替换钩子 | 核心概念卡 | 是否一眼看出主角、冲突、代价或变化 |
| `novel-macro-structure-designer` | 设计整部小说宏观结构、分部/分卷/幕结构 | 宏观结构表 | 是否支撑指定部分拆分 |
| `novel-storyline-designer` | 设计主线、展开线、隐藏线、情感线、主题线 | 故事线总览 | 每条线是否有问题、起点、终点 |
| `novel-core-character-framer` | 定义核心角色、关系、初始冲突、终局变化 | 核心角色框架 | 是否克制，不写全量人物档案 |
| `novel-world-premise-framer` | 定义足够支撑构思的世界初设 | 世界初设卡 | 是否只定义必要前提 |
| `novel-ending-direction-designer` | 定义终局性质、不可反转项、系列钩子 | 结局方向表 | 是否能成为下游冻结项 |
| `novel-proposal-integrator` | 将 proposal 各技能输出归并为统一构思案 | proposal document | 是否只做归并和口径统一，不新增核心构思 |
| `novel-proposal-risk-checker` | 检查 proposal 是否完整、克制、可拆分 | proposal 检查结果 | 是否符合 rules/references/traceability |

### 5.3 技能边界

| 技能 | 明确禁止 |
|---|---|
| `novel-intake-boundary-ledger-builder` | 不解释、不加强、不削弱 intake 约束，只登记和分类 |
| `novel-storyline-designer` | 不写 PRD 主干场景表 |
| `novel-core-character-framer` | 不写 HLD/LLD 全量人物档案 |
| `novel-world-premise-framer` | 不写世界 bible |
| `novel-proposal-integrator` | 不新增 reader promise、logline、故事线、角色框架或世界前提 |
| `novel-proposal-risk-checker` | 不替代其他技能重写内容，只报告问题 |

## 6. PRD 节点

### 6.1 harness: `novel-prd-workflow`

| 项目 | 设计 |
|---|---|
| 节点目标 | 生成指定部分的主干场景契约 |
| 输入 | proposal document、指定部分范围 |
| 输出 | PRD document / 主干场景表 |
| harness 只做 | 校验 proposal、确认指定范围、调度主干场景设计技能、登记技能输出、打包 PRD、冻结约束 |
| harness 不做 | 不设计具体主干场景，不写世界系统，不写 LLD 细节 |

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
| harness 只做 | 校验 PRD 冻结项、调度世界系统技能、登记技能输出、打包 HLD、验收支持矩阵 |
| harness 不做 | 不直接设计世界规则、人物系统、环境系统、事件系统或风格规范 |

### 7.2 下挂独立技能

| 技能 | 职责 | 输出 | 独立验收点 |
|---|---|---|---|
| `novel-prd-support-matrix-builder` | 将 PRD 主干场景映射到所需世界支撑 | PRD 支撑矩阵 | 每个主干场景是否有支撑项 |
| `novel-world-rule-designer` | 设计历史、制度、技术、社会、规则边界 | 世界规则文档 | 规则是否能解释 PRD 场景 |
| `novel-character-system-designer` | 设计全量角色系统 | 角色系统文档 | 所有角色功能、关系、动机、权限是否明确 |
| `novel-environment-system-designer` | 设计全量环境与空间系统 | 环境系统文档 | 空间关系、功能、状态变化是否完整 |
| `novel-event-system-designer` | 设计关键事件、背景事件、隐藏事件及因果 | 事件系统文档 | 事件链是否解释 PRD 主干 |
| `novel-time-information-system-designer` | 设计时间结构、信息流、视角权限 | 时间/信息系统 | 信息不对称是否可执行 |
| `novel-style-pov-system-designer` | 设计语言风格、POV、叙述距离、禁用语 | 风格与 POV 规范 | writing/checking 是否可直接使用 |
| `novel-hld-integrator` | 将各世界系统输出归并为 HLD 文档 | HLD document | 是否保持各系统边界和 PRD 支撑关系 |
| `novel-hld-integrity-checker` | 检查 HLD 完整性、可运行性、受控性 | HLD 检查结果 | 是否符合 HLD rules |

### 7.3 技能边界

| 技能 | 明确禁止 |
|---|---|
| `novel-world-rule-designer` | 不以世界观合理性为由改写 PRD 主干 |
| `novel-character-system-designer` | 不写 LLD 外貌、逐场景行为或 prose |
| `novel-environment-system-designer` | 不写具体空间描写段落 |
| `novel-event-system-designer` | 不删除、替换或重排 PRD 主干场景 |
| `novel-style-pov-system-designer` | 不生成正文样章 |
| `novel-hld-integrator` | 不借归并之名新增或覆盖世界规则、角色系统、环境系统、事件系统 |
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
| proposal | `novel-proposal-workflow` | 10 |
| PRD | `novel-prd-workflow` | 9 |
| HLD | `novel-hld-workflow` | 9 |
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
