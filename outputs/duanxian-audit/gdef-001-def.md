# 《断线》审视任务：工作项A定义书

作业：duanxian-audit-gdef-001（九作业序列第 1 项，A-定义）。内容依据固定为 main@92573f1cca40f37cee04d2beb8708ff33ba603d6；本定义书不随远端 main 移动更新。执行契约来自本作业 `.kunora/spec.yaml` 与 `.kunora/PROMPT.md`。本文定义下一作业如何阅读和总结，不代写目标总结，不启动实现一致性审计或 ISSUE 提交。

## 一、工作项A六要素

| 要素 | 可执行定义 | 可独立核查的证据与通过条件 |
| --- | --- | --- |
| 目标 | 仔细阅读项目宪法性规范、目标文档和 SPEC，回答“这本小说要成为什么”，形成供 Owner 确认的拟人化总结。 | 总结六问齐答，结论能追到冻结仓库；Owner 能区分已决定、历史来源和未决定事项。目标入口为 `duanxian/novel-goals.md`。 |
| 工作方法 | 按第二、五节先建立权威地图，再逐问提炼，核对批准包和状态证据，最后压缩为连续中文叙述。 | 每问有具体路径与章节或字段定位；关键故事事实回查 `duanxian/conception-approved/human-review-report.md`，批准状态回查两份 JSON；不能只抄目标文档或目录。 |
| 边界 | A 只理解和总结目标；读仓库可覆盖冻结内容，写入仅限该作业的新交付物。 | 不改既有文件，不写小说、不改目标、不重建机器包、不评代码实现程度、不提交 ISSUE；这些边界分别由冻结任务和 `engine/docs/ai-novel-workflow/README.md` 的职责与变更规则支撑。 |
| 约束 | 使用冻结基线、固定实施与验收分工；执行五种口径标注、来源限制和秘密保护；保留所有 Owner 不可变约束。 | 对照本节原文及第六节逐项检查；不得以“合理推断”升级故事事实或作者批准。 |
| 交付物 | A-定义交付本文；A-实施唯一交付 `outputs/duanxian-audit/goals-summary.md`，UTF-8 中文，2000–4000 中文字；A-验收按编排方渠道形成结论与必要修正指令。 | 定义书不是总结；总结不是正式开发 handoff；验收不在实施分支增加第二份报告。分支、提交号、文件哈希与验收版本绑定。 |
| 验收标准与方法 | 机械门、语义门、权威口径门、越界门全部通过后，由编排方向 Owner 请求目标总结确认。 | 第六节每项给出证据和 verdict；任何硬门失败不以总分抵销。独立验收通过不等于 Owner 已确认，更不等于小说开发准入。 |

### Owner 冻结的不可变约束（原文）

- 实施作业交付物唯一路径＝`outputs/duanxian-audit/goals-summary.md`，唯一新增文件。
- 总结必须以 main@92573f1cca40f37cee04d2beb8708ff33ba603d6 冻结内容为唯一依据。
- 总结须以拟人化方式（以“这本小说”为主语的叙述）回答：要写一本什么小说、为何写、为谁写、怎么写、写成什么样算合格、当前进度与断点；简洁清晰，2000–4000 中文字。
- 实施与验收作业的执行器/模型分配＝Owner 冻结（实施→kimi-code/k3.1-pro；验收→codex/gpt-6-astra，reasoning high），定义书不得变更。
- 审视任务全程不得修改仓库既有文件（各工作项交付物均为新增文件，落在各自交付分支）。

操作限制：本作业不安装依赖、不修改配置，仅访问授权 GitHub 仓库本体；凭据不得进入终端、日志、交付文件或提交。初始化报告和 ACK 是编排控制证据，不是业务交付物，不得添加到业务提交。后续作业仍须读取自身冻结契约，不能把本定义书解释为任意外部访问、修改历史文件或变更模型的许可。

## 二、宪法·目标·SPEC 文档地图

### 2.1 判定依据和权威优先级

这里的“宪法层”是按内容职责分类，并非声称仓库有一份名为“小说宪法”的文件。`README.md` 指向流水线业务规范入口；`engine/docs/ai-novel-workflow/README.md` 规定作者与 AI 职责、构思/开发隔离、准入和结构变更回退，因而承担宪法性约束。作业契约约束本次执行权限；小说规范约束被总结的生产方法，两者不能相互替代。

| 层次 | 实际路径 | 作用与可用范围 |
| --- | --- | --- |
| 宪法性总则 | `engine/docs/ai-novel-workflow/README.md` | “目标与非目标”“阶段接口”“统一状态与变更规则”：作者保留重大选择与批准权；开发不能从旧稿补足核心设计。 |
| 构思规范细则 | `engine/docs/ai-novel-workflow/conception-autonomous-workflow-v2.md` | 第 1–3 节定义完成、B0/S1–H1 职责、作者锁定与开放项；P1 只组装、H1 只呈现，样片不产生新事实。 |
| 开发与 HLD 规范 | `engine/docs/ai-novel-workflow/hld-autonomous-workflow-v1-design.md`；`engine/docs/ai-novel-workflow/development-phase.md` | HLD 第 2、4 节界定构思/HLD/LLD/写作及正式基线；开发第 4–6 节界定场景、修订、评分和作者定稿。这些是应遵守的方法，不证明项目已完成。 |
| 最终交付契约 | `engine/harnesses/novel-conception-autonomous/docs/final-delivery-contract.md` | 第 1–5 节规定机器本体、人审呈现、作者决定、版本绑定、正反向验收；用于解释合格与状态，不要求 A 重放生产链。 |
| 目标层汇总入口 | `duanxian/novel-goals.md` | 六章及 S01–S23 索引，承载目标、方法、边界、约束、成果、验收。其自述材料基线是 9baefb33…；本作业读取的是它在 92573f1c… 中冻结的版本，不切回该旧提交，也不把两者混称。 |
| 项目权威导览 | `README.md`；`duanxian/README.md` | 分清引擎与小说项目；项目“权威与状态”明确批准构思优先、旧 proposal/PRD/HLD 属历史链，正文是草稿。 |
| 批准版状态证据 | `duanxian/conception-approved/README.md`；`duanxian/conception-approved/author-decision.json`；`duanxian/conception-approved/conception-completion.json` | 留存批准日期、run、approval_scope、decision、status 与 hash 引用；作用是证明构思范围内的留存批准记录，不代表全部运行文件随库存在。 |
| 批准版故事呈现 | `duanxian/conception-approved/human-review-report.md` | 当前可读的批准故事、人际关系、能力限制和终局边界；抽样回查其非样片正文。配套 `.json`、`.html` 是同目录留存文件。 |
| SPEC 历史链 | `duanxian/design/specs/2026-07-05-duanxian-intake.md`；`duanxian/design/specs/2026-07-05-duanxian-proposal.md`；下列完整清单 | intake 的最小边界、proposal 的 boundary ledger 和门禁可说明来源演变；不能因为文内写了“冻结”或 `pass` 就覆盖当前批准构思。 |
| 构思过程与旧开发资料 | `duanxian/design/workflow-docs/`；`duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/manifest.md`；同目录 `gate-report.md` | 前者保留意图卡、叙述权限、覆盖关系等来源；后两者直接显示旧 HLD 的 `pending_hld_human_review` 与不得进入 LLD 的门禁。目录存在不等于当前阶段完成。 |

适用顺序必须按问题类型判断：

1. **执行权限**遵守冻结作业契约与 Owner 不可变约束，不从小说角色的“自主授权”推导 Agent 作业权限。
2. **流程规则**先总则，再当前适用的 V2/HLD/开发细则及最终交付契约。规范规定“必须有”不等于本项目“已经有”。
3. **故事内容**按项目导览优先当前批准构思；先用目标文档找入口，再回查批准包。正式内容权威仍是契约定义的 P1 机器本体及其来源链，人审报告是忠实呈现。A 可以据留存批准报告整理目标，但不能将 Markdown 提升为正式开发机器入口。
4. **历史材料**只解释来源、差异和保留问题。旧 proposal 第 18–19 节同时出现 Agent `pass` 与 human `pending` / `blocked_pending_human_confirmation`，必须保留适用阶段；不能据其旧状态否定后来的构思批准，也不能把旧四段式、角色、终局动机并入新版。
5. **冲突处理**记录两侧路径、版本、原文定位与对总结的影响。已能由批准层裁定的采用批准层并标明历史；同层冲突或缺证则明确未决，必要时交编排方裁决，禁止自编故事或修源文件。

`duanxian/conception-approved/README.md` 与旧稿内部可能保留历史根路径；应在冻结树中定位现存文件并注明迁移关系，找不到就写“原文引用、当前未定位”，不得把运行相对路径或旧根路径当作当前可读事实。目录清单仅证明路径存在，不证明每份文件内容已读或已批准。

### 2.2 五种口径和 S01–S23 使用规则

| 标注 | 适用内容 | 禁止的升级 |
| --- | --- | --- |
| 【当前权威口径】 | 批准故事正文或明确批准记录可支持的事实；引用报告具体小节、JSON 字段。 | 把旧过程稿、体验样片或工程推测当作作者决定。 |
| 【历史/旧链口径】 | 旧 SPEC、旧 HLD、意图卡与叙述契约中的版本限定事实。 | 将旧 C5、M01–M10、K1–K10 直接当作当前章节结构；复制旧 `covered` 成为新版验收结论。 |
| 【未完成项】 | 冻结材料不足以证明的目标、准入、定位或工作。 | 将“未在 Git 留存中找到”写成“现实中不存在”或“此前批准无效”。 |
| 【流程规范】 | 应怎样开发、审查、交接和批准。 | 将应然条件写成已然完成，或把验收定义写成实测结果。 |
| 【推断】 | 基于明确证据的解释、读者沟通对象等建议性归纳。 | 发明读者年龄、市场渠道、章数、技术可行性或作者心理动机。 |

总结每个事实段至少有一个适用标注；一段混合状态时分句标注或拆段。来源编号 S01–S23 沿用 `duanxian/novel-goals.md` 的原映射，不重编号、不凭记忆解释。编号只是索引：总结中须随段给出完整仓库相对路径及小节/字段，或用唯一引用键连接文末完整路径。下游未读目标文档也应能找到证据。引用不能只写“S05”或“批准目录”。

### 2.3 冻结树目录全清单

以下清单由冻结提交的 Git 文件树生成。SPEC 共 36 个文件（根层 10 个，LLD 角色 7 个、场景 10 个、空间 9 个）；workflow-docs 共 11 个文件。全文必读范围见第五节；对清单其余文件按引用需要展开，不声称全部通读。

**duanxian/design/specs（36 个文件）**

- `duanxian/design/specs/2026-06-06-digital-life-novel-design.md`
- `duanxian/design/specs/2026-06-06-first-meeting-digital-life-novel.md`
- `duanxian/design/specs/2026-06-06-hld-digital-life-novel.md`
- `duanxian/design/specs/2026-06-06-lld-digital-life-novel.md`
- `duanxian/design/specs/2026-06-06-prd-digital-life-novel.md`
- `duanxian/design/specs/2026-06-06-reference-survey.md`
- `duanxian/design/specs/2026-06-06-science-background-digital-life-novel.md`
- `duanxian/design/specs/2026-06-06-technical-systems-digital-life-novel.md`
- `duanxian/design/specs/2026-07-05-duanxian-intake.md`
- `duanxian/design/specs/2026-07-05-duanxian-proposal.md`
- `duanxian/design/specs/lld/characters/2026-06-07-character-betrayer.md`
- `duanxian/design/specs/lld/characters/2026-06-07-character-colleagues.md`
- `duanxian/design/specs/lld/characters/2026-06-07-character-it.md`
- `duanxian/design/specs/lld/characters/2026-06-07-character-jiling.md`
- `duanxian/design/specs/lld/characters/2026-06-07-character-qianxu.md`
- `duanxian/design/specs/lld/characters/2026-06-07-character-shenyu.md`
- `duanxian/design/specs/lld/characters/2026-06-07-character-zhengbozhou.md`
- `duanxian/design/specs/lld/scenes/2026-06-07-scene-K1.md`
- `duanxian/design/specs/lld/scenes/2026-06-07-scene-K10.md`
- `duanxian/design/specs/lld/scenes/2026-06-07-scene-K2.md`
- `duanxian/design/specs/lld/scenes/2026-06-07-scene-K3.md`
- `duanxian/design/specs/lld/scenes/2026-06-07-scene-K4.md`
- `duanxian/design/specs/lld/scenes/2026-06-07-scene-K5.md`
- `duanxian/design/specs/lld/scenes/2026-06-07-scene-K6.md`
- `duanxian/design/specs/lld/scenes/2026-06-07-scene-K7.md`
- `duanxian/design/specs/lld/scenes/2026-06-07-scene-K8.md`
- `duanxian/design/specs/lld/scenes/2026-06-07-scene-K9.md`
- `duanxian/design/specs/lld/spaces/2026-06-07-space-apartment.md`
- `duanxian/design/specs/lld/spaces/2026-06-07-space-city.md`
- `duanxian/design/specs/lld/spaces/2026-06-07-space-corridor.md`
- `duanxian/design/specs/lld/spaces/2026-06-07-space-digital-realm.md`
- `duanxian/design/specs/lld/spaces/2026-06-07-space-hotel-room.md`
- `duanxian/design/specs/lld/spaces/2026-06-07-space-meeting-room.md`
- `duanxian/design/specs/lld/spaces/2026-06-07-space-operation-room.md`
- `duanxian/design/specs/lld/spaces/2026-06-07-space-security-hall.md`
- `duanxian/design/specs/lld/spaces/2026-06-07-space-server-room.md`

**duanxian/design/workflow-docs（11 个文件）**

- `duanxian/design/workflow-docs/duanxian-causal-storyline.md`
- `duanxian/design/workflow-docs/duanxian-conception-review.md`
- `duanxian/design/workflow-docs/duanxian-core-character-design.md`
- `duanxian/design/workflow-docs/duanxian-coverage-matrix.md`
- `duanxian/design/workflow-docs/duanxian-development-map.md`
- `duanxian/design/workflow-docs/duanxian-intent-card.md`
- `duanxian/design/workflow-docs/duanxian-interview-review-brief.html`
- `duanxian/design/workflow-docs/duanxian-map-check.md`
- `duanxian/design/workflow-docs/duanxian-narrative-contract.md`
- `duanxian/design/workflow-docs/duanxian-novel-design-brief.md`
- `duanxian/design/workflow-docs/duanxian-subject-definition.md`

## 三、总体方案

本节是审视工作项A的作业编排，不是小说生产流水线的 stage 调度；依据本作业 `.kunora/PROMPT.md` 固定分工。

| 步骤 | 作业与执行环境 | 输入 | 产出、交接与准入 |
| --- | --- | --- | --- |
| 一：定义 | duanxian-audit-gdef-001；agent-linux-01；codex/gpt-6-astra，reasoning high | 冻结仓库、spec、PROMPT | 本文，提交至 `remote-agent/duanxian-audit-gdef-001`；机械自检、辅助核对与 Owner 审查按本作业契约执行。编排方取回已验收提交，将定义书嵌入实施 PROMPT。 |
| 二：实施 | duanxian-audit-gimpl-001；agent-linux-03；kimi/kimi-code/k3.1-pro | 冻结仓库、获准定义书、该作业 spec/PROMPT | 唯一目标总结文件；推送该实施作业冻结工作分支。提交和哈希交编排方，不能自称独立验收通过。 |
| 三：独立验收 | duanxian-audit-gacc-001；agent-linux-01；codex/gpt-6-astra，reasoning high | 同版定义书、冻结证据树、实施候选提交和总结 | 按第六节独立形成 PASS/FAIL（输入无法验证则 BLOCKED），失败给可执行修正指令并回实施迭代；PASS 后由编排方向 Owner 请求确认。 |

交付链统一为“交付分支 → 编排方按完整提交 SHA 取回 → 嵌入下一作业 PROMPT”。交接至少包含 job_ref、内容基线完整 SHA、交付分支、候选完整 SHA、唯一文件路径和 SHA-256、检查结果及尚待裁决项。不得只引用会移动的分支名。本文与总结可作为任务输入，但不是新故事事实来源。

独立验收由独立作业承担，不由实施者另写“验收通过”代替。若验收者无法取得候选同版文件或冻结证据，先说明具体缺口；不得用实施者自评或最新 main 补齐。验收过程不改变模型，不运行本阶段之外的小说生成器、生产 harness 或外部科学检索。Owner 确认只授权审视序列继续，不补发小说构思/HLD/发布批准。

## 四、任务路线图

### 4.1 九作业全景

| 序号 | 工作项/步骤 | 预期结果与进入下一步的门 |
| --- | --- | --- |
| 1 | A-定义（本作业） | 单一可执行定义书；按冻结验收通过后交 A-实施。 |
| 2 | A-实施（gimpl-001） | 六问目标总结，单一文件；自检通过并推送后交 A-验收。 |
| 3 | A-验收（gacc-001） | 独立核查；FAIL 回 2，PASS 后等 Owner 确认目标总结，确认前不进 B。 |
| 4 | B-定义 | 定义实现一致性与实现程度审视的范围、证据、方法和标准；由后续冻结作业确定具体交付路径。 |
| 5 | B-实施 | 通读获准基线的文档与代码，形成真实、自洽、有证据的审视报告；不修改既有文件。 |
| 6 | B-验收 | 核对结论、证据和覆盖；失败回 5，通过后按编排门进入 C。 |
| 7 | C-定义 | 定义问题归并、粒度、重复检查、ISSUE 内容及提交权限；不在本作业预造问题。 |
| 8 | C-实施 | 根据通过审视的问题提交 GitHub ISSUE，逐条说明问题、证据和解决建议，粒度内聚可独立处理。 |
| 9 | C-验收 | 核对 ISSUE 与证据、粒度、实际提交状态；失败回 8，通过后由编排方收口。 |

各工作项仍遵循定义→实施→独立验收的 Owner 三步协议；A 的具体执行器/模型已冻结，B/C 的具体机器、作业号、路径和新基线由各自冻结契约给出，不在本文虚构。后续发现目标理解需改变时回到 Owner 确认门，不能在 B/C 静默改写 A。

### 4.2 A 内部执行顺序与失败处置

| 步骤 | 预期 | 失败处置 |
| --- | --- | --- |
| A0 准入 | 已读契约，ACK 按当前启动要求落证，分支与基线正确，源码未修改。 | 记录实际不匹配项并交编排方；不 reset、不清理他人工作、不改契约。 |
| A1 资料阅读 | 按第五节通读，建立六问与五种口径的证据对应。 | 缺文件先查冻结 Git 树；关键事实缺证则标未完成或阻塞该断言。 |
| A2 权威核对 | 批准包、历史链、流程规则相互分开；开放项仍开放。 | 同层无法裁决的冲突上报，不择方便文本、不补设定。 |
| A3 总结初稿 | 以“这本小说”为叙述主语，六节完整，中文数在范围内。 | 在唯一新文件内压缩、补充证据或修正口径，不回改来源。 |
| A4 自检与交付 | 机械、语义、引用、范围检查通过；只提交目标文件并推送指定分支。 | 内容问题回 A3；认证/网络问题保留提交与失败状态，不换凭据、不扩大推送范围。 |
| A5 独立验收 | 按候选 SHA 逐项核对，给出定位明确的结果。 | FAIL 生成修正指令，回 A3；新候选需重跑机械门和受影响语义门。 |
| A6 Owner 确认 | 编排方呈递已通过总结及未完成项，Owner 明确确认。 | 要求修改则交实施修订并重验；未回复不视为确认。 |

## 五、实施作业工作指令

### 5.1 准入与资料读取

1. 读取本作业（实施作业自身）的 spec/PROMPT 和交接定义书，确认唯一输出、冻结来源、工作分支、凭据使用方式与 ACK 启动序。本定义书的分支和凭据属于定义作业，不得照搬到实施作业。执行 `git --version`、`python3 --version`、`git status --short`、`git rev-parse --abbrev-ref HEAD`、`git rev-parse HEAD`；记录结果于作业终端。首次实施须从内容基线开始，修正轮允许 HEAD 为该实施分支上已核验的先前候选，但相对基线仍只能新增总结文件。
2. 固定内容基线为 `92573f1cca40f37cee04d2beb8708ff33ba603d6`。先用 `git cat-file -e <基线>^{commit}` 确认对象可读，再用 `git diff <基线> -- README.md duanxian engine` 确认源材料未变；若交接候选改变了来源，停止准入，不自行恢复。读取必须对应基线，可用 `git show <基线>:<仓库相对路径>` 避免混入其他版本。
3. 按以下顺序全文阅读，长文须分段覆盖到末尾；不能只读标题、摘要或搜索命中。目录用 `git ls-tree -r --name-only <基线> -- <目录>` 获得完整清单，并与第二节核对。

| 顺序 | 必读路径及精确范围 | 阅读后应能说明 |
| --- | --- | --- |
| 1 | `duanxian/novel-goals.md` 全文含 S01–S23 | 六章覆盖什么、五种口径怎样使用、哪项只是推断。 |
| 2 | `README.md`、`duanxian/README.md` 全文 | 引擎/项目区别、当前批准包位置、历史资产与草稿状态。 |
| 3 | `duanxian/conception-approved/README.md`、`duanxian/conception-approved/author-decision.json`、`duanxian/conception-approved/conception-completion.json`、`duanxian/conception-approved/human-review-report.md` 全文 | 批准范围、run、状态、人物主体性、核验与关停边界；阅读样片但不提取新设定。 |
| 4 | `engine/docs/ai-novel-workflow/README.md` 全文 | 作者职责、构思与开发接口、状态门和结构变更回退。 |
| 5 | `duanxian/design/specs/` 全清单；`duanxian/design/specs/2026-07-05-duanxian-intake.md`、`duanxian/design/specs/2026-07-05-duanxian-proposal.md` 全文 | 最小边界、历史结构与当时人审 pending 的区别；不复活旧方案。 |
| 6 | `duanxian/design/workflow-docs/` 全清单；`duanxian/design/workflow-docs/duanxian-intent-card.md` 全文 | 目标读者未指定、旧系列范围的版本限定；拟引用的过程规则必须再读其原文。 |
| 7 | `engine/harnesses/novel-conception-autonomous/docs/final-delivery-contract.md` 全文 | P1 权威、H1 呈现、样片边界、完成凭证、正反向验收的适用范围。 |
| 8 | `engine/docs/ai-novel-workflow/development-phase.md` 全文；`engine/docs/ai-novel-workflow/conception-autonomous-workflow-v2.md` 第 1–3 节；`engine/docs/ai-novel-workflow/hld-autonomous-workflow-v1-design.md` 第 2、4 节 | 核对方法与质量数字，明确 HLD/LLD/写作职责，不把规范当项目完成证据。 |
| 9 | `duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/manifest.md`、`duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/gate-report.md` 全文 | 旧 HLD 的待人审状态及其与新版开发断点的区别。 |

4. 形成六问证据对应，可保留在当前会话中，不新增笔记文件。每条包括“要回答的问题→结论→口径→路径/小节或字段→已知限制”。凡引用清单外文档须先实际读取基线内容；历史文档链接失效时不得以猜测补出新路径。
5. 核对批准记录：`approval_scope=conception`、`decision=approved`、completion `status=ready`、两份 JSON 的 run_id 一致。可重算留存 author-decision 与 HTML 的 SHA-256，分别对照 completion.author_decision.sha256 和 decision.human_review_package.html_sha256；这只检查本地留存绑定。P1、run state、全量 completion 若未留存，应明确无法重放全链，禁止写“全部 validator 已通过”。

### 5.2 总结文档结构与写法

文件采用标题、基线说明、六个二级节及文末来源索引。固定六节为：

| 节标题 | 必须回答的内容 | 建议中文字符预算 |
| --- | --- | ---: |
| 一、要写一本什么小说 | 数字生命题材长篇；顾衡记忆与 R-07 新主体区别；沈逾关系、现实危机和当前实例告别如何构成主承诺；不编章数。 | 350–550 |
| 二、为何写 | 把记忆、身份、创造/使用/照护/退出责任落在人物选择与代价；不得替作者宣布唯一伦理答案或编写其私人动机。 | 300–450 |
| 三、为谁写 | 明说批准材料没有确定市场人群；如归纳愿意面对身份与伦理开放问题的读者，标【推断】；区分读者承诺与商业定位。 | 200–350 |
| 四、怎么写 | 构思→正式开发基线→HLD→LLD→写作及受控修订；作者/Agent 分工、场景与连续性、来源/版本；旧叙述契约只在历史口径下引用。 | 450–650 |
| 五、写成什么样算合格 | 故事硬边界、因果和人物选择、危机闭环与伦理未决；机器/语义/作者三种门；流程标准不能冒充本书实测结果。 | 450–650 |
| 六、当前进度与断点 | 构思批准的时间/run/范围；旧 HLD 待审、正文草稿；机器包与新版 HLD 完成证据的可得性；下一阶段前须取得何种输入，哪些问题继续开放。 | 350–550 |

以上预算合计 2100–3200，给基线说明、标注和索引保留余量。正式门为**全文 2000–4000 个中文字符**：统一以 Unicode CJK 字符计数，不把 UTF-8 字节、标点、英文字母和数字混算为中文字；标题、标注、索引中的中文同样计入。第六节提供同一算法，实施与验收不得各换口径。

每节首个实质叙述段以“这本小说”为主语开篇，后文可自然使用“它”或省略主语。拟人化意味着“这本小说想让读者看见……”“这本小说还不能声称……”，不意味着小说具有真实意识或代替角色发言。连续段落应讲清因果、选择和界限，避免把总结写成字段堆表、流水账或角色第一人称独白。

每个重要断言就近标口径及路径/章节；允许文末索引缩短重复路径，但引用键必须能唯一解析。写明“目标尚未指定”比补一个合理目标更合格。八个推进阶段、十条故事线、17 名角色、43 个主要事件如果被提及，只称批准报告的结构规模，不转成章节数或写作配额。根据 `duanxian/novel-goals.md` 第五章与批准报告对应小节，最终章数、全书字数仍不能确认。

完成初稿后按第六节自检，先修事实与口径，再压缩重复表述。不要运行小说流水线、修改代码、调整配置、安装软件、检索外部科学依据、复制凭据、创建 ISSUE 或额外提交报告。

### 5.3 提交、推送与完成信号

1. 从实施作业自身冻结 spec/PROMPT 取得并在当前 shell 设置 `a_work_branch`（允许推送分支）、`a_credential_file`（授权凭据文件绝对路径），两者都不可从本定义作业照搬。若缺少任一项则报告编排输入缺口，保留已完成文稿，不猜测。正常新建实施工作分支应由编排方准备；不新推 main 或其他引用。
2. 运行第六节文件检查，人工逐项完成语义门。执行 `git status --short --untracked-files=all` 与 `git diff --check`；只应有目标文件新增或该新文件在修正轮的修改。已有基线文件变化必须停止并报告，不能 reset/checkout 覆盖。
3. 使用以下命令逐条执行，每条成功后才继续。`a_work_branch` 必须与冻结 spec 的 work_branch 完全相同；首次交付与修正轮最终相对内容基线都必须只显示一个 `A`。不使用 `git add .`。

```bash
test -n "$a_work_branch"
test "$(git rev-parse --abbrev-ref HEAD)" = "$a_work_branch"
git add -- outputs/duanxian-audit/goals-summary.md
git diff --cached --check
git diff --cached 92573f1cca40f37cee04d2beb8708ff33ba603d6 --name-status
# 人工确认上一行唯一为 A outputs/duanxian-audit/goals-summary.md 后继续。
git -c user.name=remote-agent -c user.email=remote-agent@kunora.local commit -m "docs(audit): add goals summary (duanxian-audit-gimpl-001)"
git diff --name-status 92573f1cca40f37cee04d2beb8708ff33ba603d6 HEAD
git status --short
```

4. 再运行第六节已提交候选检查，确认 SHA-256 与待验收候选一致。提交信息若实施冻结契约另有原文要求，以该原文为准；修正轮用普通追加提交，不强推、不改其他引用。按自身契约使用授权凭据对同一 GitHub 仓库推送。例如契约允许与本作业相同认证方式时，在关闭命令追踪、HTTP 调试的环境中执行：

```bash
set +x
unset GIT_TRACE GIT_TRACE_CURL GIT_CURL_VERBOSE GIT_TRACE_PACKET GIT_TRACE_SETUP
test -r "$a_credential_file"
git push "https://x-access-token:$(cat -- "$a_credential_file")@github.com/innuama-coder/ai-novels.git" "HEAD:refs/heads/$a_work_branch"
git rev-parse HEAD
git ls-remote origin "refs/heads/$a_work_branch"
```

凭据只经命令替换交给 Git；不得回显 URL、打印凭据或保存含凭据的错误输出。运行器须保证错误日志脱敏，做不到时停止认证步骤并交编排方处理。远端查询需要额外认证时仍按该作业授权方式，禁止寻找其他凭据。

5. 只有推送退出码为 0 且远端该分支完整 SHA 等于本地候选 HEAD，才报告已交付。输出文件路径、完整提交号、内容基线、文件 SHA-256 与检查结果；最后一行单独输出 `DXAGIMPL-DONE-<tip7>`，其中 `<tip7>` 取远端已核对 SHA 的前 7 位。失败时不输出完成哨兵，也不把本地 commit 当推送成功。

## 六、独立验收作业检查单

### 6.1 输入封定与机械检查

验收者使用独立的 A-验收作业，保持 codex/gpt-6-astra、reasoning high。先记录定义书版本、内容基线、实施候选完整 SHA、总结 SHA-256 和验收命令退出码。候选可来自编排方只读 checkout；不得为方便验收修改实施文件。以下代码只用 Python 标准库，既供实施自检，也供验收复跑；验收时当前 HEAD 必须是已封定候选。

```bash
python3 - <<'PY'
import hashlib, pathlib, re, subprocess
base = '92573f1cca40f37cee04d2beb8708ff33ba603d6'
p = pathlib.Path('outputs/duanxian-audit/goals-summary.md')
assert p.is_file() and not p.is_symlink(), 'not-regular-file'
b = p.read_bytes()
t = b.decode('utf-8')
assert b and '\x00' not in t, 'empty-or-NUL'
ranges = ((0x3400, 0x4DBF), (0x4E00, 0x9FFF), (0xF900, 0xFAFF),
          (0x20000, 0x2EE5F), (0x2F800, 0x2FA1F), (0x30000, 0x323AF))
n = sum(any(lo <= ord(c) <= hi for lo, hi in ranges) for c in t)
assert 2000 <= n <= 4000, f'Chinese-count={n}'
heads = re.findall(r'^## (.+)$', t, re.M)
expected = ['一、要写一本什么小说', '二、为何写', '三、为谁写',
            '四、怎么写', '五、写成什么样算合格', '六、当前进度与断点']
assert heads[:6] == expected, 'six-question-headings'
assert base in t, 'missing-frozen-baseline'
assert not re.search(r'gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|glpat-[A-Za-z0-9_-]{15,}', t), 'secret-pattern'
assert not re.search(r'(?im)^\s*(TODO|TBD)\b', t), 'unfinished-placeholder'
assert '这本小说' in t, 'missing-narrative-subject'
subprocess.run(['git', 'cat-file', '-e', base + '^{commit}'], check=True)
print('FILE-PASS', 'Chinese-count=' + str(n), 'bytes=' + str(len(b)),
      'sha256=' + hashlib.sha256(b).hexdigest())
PY
```

“出现主语”只证明字符串存在，拟人化是否贯穿六问由语义门裁定。未使用的历史口径不强迫凑标签，但所有实际引用的口径必须正确。文末索引可用三级标题或第七个二级节，不能把六问分散成无法定位的隐含结构。

已提交候选另执行以下只读检查；首次自检提交前先运行文件检查，再用第五节暂存范围检查，不能把未提交文件误判为已交付。

```bash
python3 - <<'PY'
import pathlib, subprocess
base = '92573f1cca40f37cee04d2beb8708ff33ba603d6'
p = 'outputs/duanxian-audit/goals-summary.md'
def git(*args):
    return subprocess.check_output(['git', *args])
subprocess.run(['git', 'merge-base', '--is-ancestor', base, 'HEAD'], check=True)
assert git('diff', '--name-status', base, 'HEAD').decode().splitlines() == ['A\t' + p], 'scope-not-single-addition'
assert not git('status', '--porcelain', '--untracked-files=all').strip(), 'dirty-worktree'
assert git('show', 'HEAD:' + p) == pathlib.Path(p).read_bytes(), 'candidate-file-mismatch'
# 不仅比较最终树，也检查候选历史没有曾提交后又恢复的越界文件。
commits = git('rev-list', '--reverse', base + '..HEAD').decode().splitlines()
assert commits, 'missing-delivery-commit'
for commit in commits:
    parents = git('rev-list', '--parents', '-n', '1', commit).decode().split()[1:]
    assert len(parents) == 1, 'unexpected-merge-or-root'
    rows = git('diff-tree', '--no-commit-id', '--name-status', '-r', commit).decode().splitlines()
    assert rows and all(row in ('A\t' + p, 'M\t' + p) for row in rows), 'history-scope-violation'
print('SCOPE-PASS', 'candidate=' + git('rev-parse', 'HEAD').decode().strip())
PY
```

此处“不得修改既有文件”指冻结基线已存在的文件；验收退回后可修改本作业新建的总结并追加提交，否则无法履行 Owner 的迭代协议。编排控制文件若已按初始化安排忽略，不作为业务新增文件；不得因此新增 `.gitignore` 规则或把其他业务产物藏入忽略目录。

| ID | 验收动作 | 通过标准 |
| --- | --- | --- |
| M01 | 核验输入版本与上述两个脚本 | 全部退出 0，UTF-8、六节、中文字数、基线、候选文件与提交一致；范围唯一新增。 |
| M02 | 逐条解析总结引用，在基线 `git cat-file -e <基线>:<路径>` 定位，并读小节或 JSON 字段 | 所有路径真实存在且内容支持断言；不能仅证明文件存在；旧运行内部路径不得冒充仓库路径。 |
| M03 | 检查目标分支远端 SHA、提交元数据、文件哈希 | 与编排交接一致；推送成功哨兵与远端候选匹配；缺远端证明不得认定已交付。 |
| M04 | 检查整个候选文件、候选 diff、提交信息与日志摘要 | 无秘密、占位符、伪造验收、额外报告或业务范围扩大；机械 token 模式只是一道辅助门。 |

### 6.2 六问语义覆盖检查

| ID | 问题 | PASS 条件；否则给出具体缺口 |
| --- | --- | --- |
| S01 | 要写什么 | 数字生命长篇、R-07 新主体、沈逾关系与外部危机能形成一条清晰承诺；没有把顾衡写成复生者。依据批准报告开头与人物节。 |
| S02 | 为何写 | 身份、记忆、使用与照护、同意与退出的代价落在具体选择上；无凭空作者动机、无“任务成功即伦理正当”。依据目标文档第一章及批准报告硬规则。 |
| S03 | 为谁写 | 目标读者未定如实保留；建议人群明确为推断，读者体验与市场事实分开。依据目标文档第一章第 3 小节、意图卡第 3 节。 |
| S04 | 怎么写 | 清楚描述构思/HLD/LLD/写作分工、版本、场景、受控修订与人类批准；不能把 A 总结充当正式 handoff。依据流程总则、HLD 第 2/4 节、开发 SOP。 |
| S05 | 怎样合格 | 有世界与人物硬门、因果与文学质量、机器/语义/人审区别；如引用 80 分和前四项 70%，须限定为开发规范中的场景门。依据开发第 6 节、最终交付契约及目标文档第六章。 |
| S06 | 进度与断点 | 构思 approved/ready 的范围明确；旧 HLD 待审、正文草稿、全量运行证据缺口不混为一谈；不得声称整部小说 released。依据两份批准 JSON、项目导览、旧 HLD manifest/gate。 |
| S07 | 拟人化与简洁 | 六节均以“这本小说”作叙述主体推进，无角色自述冒充项目总结；读者不靠代码或大表才能读懂；没有反复复述同一证据来凑字数。 |

### 6.3 权威口径抽查（以下高风险项全部覆盖）

每项记录“候选原文位置→候选短引→基线证据路径与定位→标注是否准确→PASS/FAIL”。没有相关错误断言不等于该必需主题已覆盖，主题覆盖另由 S01–S06 判定。

| ID | 核查对象与对照位置 | 必须保持 |
| --- | --- | --- |
| A01 | `duanxian/conception-approved/human-review-report.md`“R-07”“顾衡”“关系变化” | 记忆不等于人格；顾衡已死；R-07 新感情不是顾衡迟到的爱情。 |
| A02 | 同报告“文字会话隔离室”“R-07 隔离套间”“具身或接口边界” | R-07 无当前视听、身体和现实行动能力；记忆片段不当作当前感知或客观录像。 |
| A03 | 同报告“跨国威胁处置”“现实硬件控制室”“秦峥”“贺闻钧” | 情报须经专家、硬件和授权核验，现实团队阻断；权限不能由信息输出自行产生。 |
| A04 | 同报告“程予安”“周岚”“亲属保护、伦理监督与责任留痕” | 妻子在世且有同意边界；亲属非工具；保护原因层不能妨碍救人，公共安全不能取消全部隐私。 |
| A05 | 同报告“开放边界”“唐黎”“苏望舒” | 当前实例关停、无活动备份；静态封存不保证复活；法律身份、连续性与两国互信仍开放。 |
| A06 | `duanxian/conception-approved/author-decision.json` 的 approval_scope/decision/run_id；`duanxian/conception-approved/conception-completion.json` 的 status/run_id | approved/ready 限于 conception；本地绑定核验不是全生产链 validator 重跑。 |
| A07 | `duanxian/novel-goals.md` 第三至五章；旧 proposal 第 15、18 节；旧 HLD manifest | 旧系列钩子、四段式、C5 等不晋升为当前事实；规范冻结、文件生成、作者批准和正式完成彼此区分。 |
| A08 | 最终交付契约第 2–3 节；批准报告“三个试读场景” | 样片仅提供体验，不能以雨声、枪声等局部写法补入事实；人审 Markdown 不替代 P1 内容权威。 |
| A09 | 目标文档第一、五章及批准报告结构规模小节 | 无臆造读者定位、全书字数、最终章节数或现实科学结论；推断注明来源和不确定性。 |

### 6.4 越界、结论与修正循环

范围检查包括最终 diff、逐提交历史和未提交文件，不只看 `git status` 是否干净。拒绝修改来源文档、配置、依赖、既有代码或 `.kunora` 冻结契约；拒绝将实现审计、故事续写、ISSUE 提交混入总结。验收无需运行全仓库测试或破坏性负例；最终交付契约中的生产链负例是被总结的流程标准，不是本次 A 的执行任务。

PASS：M01–M04、S01–S07、A01–A09 及范围门全部通过，结论明确只针对封定候选。FAIL：存在可修正的内容、引用、字数或范围违例，列出所有已定位问题，不以整体“基本合格”放行。BLOCKED：关键输入/候选版本无法取得或必须由 Owner 裁决的矛盾未解决；写明缺口，不虚构失败修复。验收记录通过编排指定渠道交付，不擅自在实施分支新建文件。

每条修正指令使用以下模板，保证实施者无需猜测：

```text
候选：<完整提交 SHA>；文件 SHA-256：<值>；定义书版本：<值>
结论：FAIL / BLOCKED；失败检查 ID：<M/S/A/范围项>
问题定位：outputs/duanxian-audit/goals-summary.md → <节标题/段落/短引>
事实证据：<冻结仓库相对路径 + 小节/字段 + 必要短引>
错误与影响：<缺失、反向、历史升级、无来源或越界的具体说明>
修正动作：<只改本作业新增总结的哪个段落，补什么，删什么，保留什么>
禁止改变：<相关 Owner 原文约束、权威边界、开放项、模型分配>
复验：<需重跑的机械命令 + 受影响的语义/抽查 ID + 新候选 SHA>
```

实施者按指令修正并追加提交，同一唯一输出路径不变；验收者必须针对新 SHA 重跑机械与范围门，重审受影响断言及相邻因果，不能复用旧 PASS。涉及定义书本身不充分或 Owner 控制需变化时交编排方处理，不允许实施者回改本定义书或冻结材料。最终由编排方取得 Owner 对目标总结的明确确认，再启用 B 作业。
