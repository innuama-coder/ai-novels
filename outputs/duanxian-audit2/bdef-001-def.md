# 《断线》审视任务 R2：工作项 B 定义书

作业：`duanxian-audit2-bdef-001`。冻结内容基线 BASE：`92573f1cca40f37cee04d2beb8708ff33ba603d6`。本定义书只规定审视方法和验收条件，不替代 B-实施报告、不代表 B-独立验收或作者批准。以下路径均相对仓库根目录；除明确标注的输出路径外，材料证据均指 BASE 中的文件。定义书的提交号记为 DEF，由交接方填写完整 SHA；实施报告提交号记为 IMPL，每轮验收必须固定到具体 IMPL。

## 一、工作项 B 六要素

### 1. 目标

回答三个问题：批准构思是否与项目目标一致且内部自洽；现有设计是否忠实落实批准构思；正文及写作素材是否落实设计并符合当前目标，分别实现到什么程度。评价对象是小说的主题承诺、人物、关系、世界规则、因果、信息披露、场景功能、结局与阅读体验；交付可复核的证据链和适配缺口，不改写小说。

基准为 `duanxian/novel-goals.md` 全文与 `duanxian/conception-approved/` 批准包。项目导览 `duanxian/README.md` 明确批准包为当前权威、旧 proposal/PRD/HLD 为历史链；根 `README.md` 与 `engine/docs/ai-novel-workflow/README.md` 只提供资产分类、作者责任和构思/开发边界参照。

### 2. 工作方法

先固定版本和对象全集，再建立目标义务表；逐文件通读，按“目标要求 → 批准构思 → 设计承载 → 正文/素材表现”双向追溯。每一结论同时写内容判断、实现程度、材料权威和证据限度。正向查目标是否有承载，反向查设计和正文有没有无来源的新事实。历史材料可以提供可复用片段，但其自称 `pass`、`ready`、`已完成` 不等于当前目标已经落实。

### 3. 边界与防跑偏机制

本作业只新增本定义书并提交推送指定工作分支；不修改已有文件，不创建 ISSUE。B-实施只审视并产出报告，具体写入和推送权限须由其冻结契约授予；本定义书不跨作业授予权限。C 工作项在 B 验收通过后另行立项。

对候选发现先问：“它具体改变了哪个故事事实、人物选择、读者信息或文学目标？”能给出两侧内容证据才进入业务发现。纯工程基础设施类一律标记“移交工程线，不入本报告结论”，不把其细节、编号、修复建议复制到业务发现、摘要、实现程度统计或 C 候选表。此标签是分流动作，不是已经创建或发送了工程 ISSUE；本作业不执行外部移交。

故事内的实验设备、机构权限、日志与现实团队核验属于世界规则和因果设计，可以审视；构建这些文件的工具实现不属于小说审视。缺少当前设计或正文的留存证据，只能据实描述相应内容无法证明落地，不能扩写为工具缺陷或否定构思批准。正式开发条件仅作为内容版本状态，不能借此审查工程实现。

### 4. 约束：Owner 口径原文

- **审视对象（Owner 原话约束）**：本审视任务的目标是**评审小说的构思和设计**——即批准构思（conception-approved）、设计文档（design/specs、workflow-docs、runs 中的设计产物）、正文/素材实现（writing、novel-text）是否与项目目标一致、实现到什么程度。
- **明确排除**：构建小说的流程、工具、技能等工程基础设施问题（CLI 路径、技能计数、.gitattributes、CI/测试布局等）**不属于本审视对象**——此类发现已作为 ISSUE #1–#7 走工程线留存，本审视不得再产出或复述此类内容。
- **一致性基准**：项目目标 = `duanxian/novel-goals.md`（Owner 已确认的目标文档）＋ `duanxian/conception-approved/` 批准包（当前权威构思）。审视即回答：构思与设计文档是否忠实落实了这些目标？正文/素材实现是否与构思设计一致？实现程度如何？
- **三步协议**：B-定义（本作业，GPT-6-Astra/High）→B-实施（Kimi-K3.1-Pro）→B-独立验收（GPT-6-Astra/High）；验收不通过即回实施迭代，直至验收通过。
- **编排者角色**：编排者只做调度，不做事实认定与业务判断；一切结论以实施与验收 Agent 的产出为准。
- **历史教训（R1 跑偏）**：上一轮审视（ISSUE #1–#7 及其支撑报告）聚焦工程基础设施，被 Owner 判定跑偏；本定义书必须在六要素中显式设置防跑偏机制（如：任何发现若属工程基础设施类，一律标记『移交工程线，不入本报告结论』）。

补充执行约束：中文；不联网补充科学、历史、风格或市场结论，不访问 github.com 本仓库之外的外部服务。材料内的外链只视作历史引用。不得泄露凭据，不把凭据放入报告、命令日志或提交。不得替作者裁定未决身份、重载或续作内容；不得把参考作品的写法升级为作者批准要求。审视者可以提出修订方向，不能直接补写设定或替实施者预填最终结论。

### 5. 交付物

| 阶段 | 产出 | 必备内容与交接 |
| --- | --- | --- |
| B-定义 | `outputs/duanxian-audit2/bdef-001-def.md` | 本六节规程、BASE 对象清单、逐步指令、验收检查单；提交后交接 DEF |
| B-实施 | `outputs/duanxian-audit2/implementation-review-r2.md` | 8000–15000 中文字的正文、文件覆盖账、目标矩阵、三层结论、证据与未完成项；交接 IMPL |
| B-独立验收 | 对指定 IMPL 的独立验收记录 | 逐项 PASS/FAIL、实测证据、抽样集合、修正要求；记录位置由验收作业契约固定，不由实施者代写 |

定义书的字节下限与实施报告的中文字数不是同一标准。实施报告的账表放在同一文件，避免为审视擅自新增多份仓库文件。

### 6. 验收标准与方法

定义书须有六节，覆盖全部对象、三层一致性与实现程度，完整保留 Owner 原文；路径可定位、方法能独立执行、防跑偏规则明确。运行冻结机械检查，再由本作业作辅助语义核对；最终是否合格由验收者与 Owner 判定。本作业不得把自检写成独立验收通过。

实施报告的合格条件是覆盖完整、证据成立、版本和口径正确、结论可复验、无工程越界。小说存在缺口不等于审视报告不合格；相反，即使结论乐观，漏读材料、无证据或抹去反例也必须退回。

## 二、审视对象与一致性框架

### 1. 基线、权威与当前可见状态

`duanxian/novel-goals.md` 引用自身整理时的材料提交 `9baefb33cb999f1e92f318fe6ac22f0d1fe4d752`，它是该文的来源说明；本次实际读取和复验统一使用 BASE，不能静默切回该旧提交。目标文档与批准包共同构成比较基准，不把目标摘要当成替代原包的机器本体。

`duanxian/conception-approved/author-decision.json` 的 `approval_scope=conception`、`decision=approved`，`conception-completion.json` 的 `status=ready`，说明留存的构思批准范围。README 说明批准日期为 2026-08-17、run 为 `duanxian-conception-v2-20260811-18`，运行账本和历史尝试不入 Git。承认这项批准，同时区分能读取的内容和仅被路径/hash 引用、未在 BASE 留存的内容；不擅自补造引用目标。

| 对象与精确入口 | 与目标的关系 | BASE 当前可见状态及审视方法 |
| --- | --- | --- |
| `duanxian/novel-goals.md` | 目标、边界、质量和口径总表 | 已有六章及资料索引；逐条拆成目标义务，并回查批准包，不将其中的流程规范变成工程审计范围 |
| `duanxian/conception-approved/`（6 文件） | 当前批准构思的留存依据 | 作者决定、完成记录及报告 md/json/html 均在；机器报告是人审报告结构化版本，不能冒充完整 P1 本体；检查故事内容及呈现自洽 |
| `duanxian/design/specs/`（36 文件） | 早期方向、PRD/HLD/LLD 及角色、空间、场景设计 | 根部 10 篇，LLD 人物 7、场景 10、空间 9 篇；各自的完成字样只在历史版本中解释；逐一判断保留、适配、冲突或证据不足 |
| `duanxian/design/workflow-docs/`（11 文件） | 意图、主体、人物、因果、叙述、地图及覆盖的过程设计 | NDB 和交接审阅有“ready（待作者最终批准）”；旧 C1—C9、M01—M10 与当前批准构思需重新对应；不能把旧 covered 直接复制为本次结论 |
| `duanxian/design/runs/proposal/`（15 文件） | 历史构思展开及汇总 | 14 篇 artifacts 和 manifest；对照 reader promise、core concept、storyline、ending 的内容与批准版差异 |
| `duanxian/design/runs/prd/`（13 文件） | 历史场景主干、价值、信息流与冻结约束 | 含早期 blocked manifest、后续 manifest 与 11 个 artifacts；以内容逐条核对，不以旧 PRD 放行推断 V2 内容完成 |
| `duanxian/design/runs/hld/`（20 文件） | 历史世界、人物、环境、事件、线程、信息和视角组织 | 含 07-10 两文件及 07-13 十八文件；07-13 manifest 为 `pending_hld_human_review`，gate 仅说明入口及下一人审门；v2.0 事实集被 v3.0 标为废弃；“本包唯一事实源”只在该历史包内有效 |
| `duanxian/design/runs/lld/`（1 文件） | 历史 LLD 状态参照 | 只有 `2026-07-08-duanxian-lld-workflow-blocked/manifest.md`；不把该目录无设计正文等同于整个仓库没有 LLD，另须核对 specs/lld 26 篇 |
| `duanxian/writing/`（17 文件） | 人物、空间和场景的写作素材 | 人物 7、空间 9、场景 K1 一篇；有 prose 样本与历史自检，属于素材，不等于连续手稿或当前版批准 |
| `duanxian/novel-text/2026-06-07-duanxian-novel.md`（1 文件） | 已有连续正文草稿 | 包含序幕、她·1—6、它·1—3；应全文逐段核对，尤其信息可见性、主体、行动因果和终局；不以篇章标题或文件存在认定长篇已完成 |

上表计入目标 1、批准 6、specs 36、workflow-docs 11、runs 49、writing 17、novel-text 1，共 121 文件。逐文件清单见本节末尾。状态来源除各文件本身外，参见 `duanxian/README.md` 的“权威与状态”、`duanxian/novel-goals.md` 第二至五章。

辅助材料还有 `duanxian/design/design-tasks/2026-07-07-duanxian-hld-design-planning/design-task-package.md`、同目录 `manifest.md`，以及 `duanxian/design/reference/2026-06-07-style-reference-liu-cixin.md`。它们用于辨明规划/参考的身份及小说内容来源，单列为辅助阅读，不把其中工程任务矩阵纳入发现。根 README、项目 README、工作流 README 为另外三份必读参照，不混入 121 个小说审视对象的分母。

### 2. 必须建立的目标义务

实施者须完整拆解目标文档，以下为最低控制面，不是替代全文的封闭清单。为每条建立 `G-001` 起的审视工作编号；这是本报告的索引，不能伪称原包正式 ID。

| 控制面 | 应核对的小说事实/功能 | 基准定位 |
| --- | --- | --- |
| 主体与主题 | 顾衡已经死亡；R-07 继承记忆却是新生命，以自己的选择承担后果；任务成功不能抵销创造与照护责任 | 目标第一章、第四章；批准 MD“记忆怎样变成选择”“故事中心的人”；JSON `DCTRL-WORLD-ONTOLOGY` |
| 关系与同意 | 沈逾曾单向暗恋顾衡；R-07 新感情来自启动后交流；程予安在世，周岚为儿时守护者；亲属不自动获得对新主体的所有权 | 目标第一章；批准 MD 各人物条目；JSON `characters` 的 must_hold / must_not_imply |
| 感知与世界 | 当前无视听、身体和自主移动，仅文字与受限记忆；过去记忆不能写成现在感官或客观录像 | 目标第四章；批准 JSON `world/environments`、`world/systems` |
| 选择和责任 | 启动项目、接受职责、交互、核验、现实行动、关停执行、未来保管的责任分立；沈逾与 R-07 均不可被降为工具 | 目标第一、四章；批准 JSON `DCTRL-CHAR-AGENCY`、人物和环境条目 |
| 危机因果 | 顾衡遗留入口与沈逾接受职责汇流；人质/专家/硬件/授权提供独立核验；现实团队完成阻断 | 目标第一、四章；批准 MD“故事的八次推进”“跨国威胁处置” |
| 信息和悬念 | 行动层救人，原因层保护有边界；终止决定不得在告别前直接展示；误解、读者知识和事实分开 | 目标第四章；批准 JSON `DCTRL-STORY-SUSPENSE`；旧叙述契约仅作历史对照 |
| 结局与余波 | 袭击完全避免；沈逾执行当前实例关停；无活动备份；未来重载、法律身份及两国互信保持未决 | 目标第三、四章；批准 MD“开放边界”、唐黎、苏望舒条目 |
| 结构与体验 | 双前置汇入主体；支撑线不能取代主体；八次推进、十线、17 角色、43 主要事件是呈现中的结构规模，不能当章数 | 目标第五章；批准 MD 和 JSON `storylines`、`visual_models`、`characters` |
| 落地与质量 | 设计应有功能、选择、变化、依赖和信息边界；正文用行动及后果承载主题；未知读者画像、章数和全书字数不能补作作者决定 | 目标第一、五、六章；工作流 README“采用的设计原则” |

人物清点须覆盖批准报告中的 17 人：R-07、沈逾、顾衡、周岚、程予安、许曼青、秦峥、梁策、罗景明、唐黎、贺闻钧、伊利亚·萨温、德米特里·沃尔科夫、叶惟正、阿列克谢·奥尔洛夫、赵澄、苏望舒。姓名、功能和关系均回查批准 MD/JSON。不能将旧郑柏舟等角色仅凭“职位相似”映射为新版人物；允许一对多、多对一、无对应，但须解释功能和权限差别。

### 3. 三层一致性矩阵

构思层：以目标要求核对批准包内部同一人物、环境、事件和开放项的表述，检查 md/json/html 是否改变了事实、强调或范围。批准记录决定阶段身份，不豁免呈现中的可核对差异；内容问题也不允许审视者撤销作者批准。遇到基准两侧冲突，保留两侧原文和定位，标记“基准待裁决”，不要选择更方便的一侧继续推出确定结论。

设计层：把每个目标义务映射到 specs、workflow-docs 与 runs 的承载位置，分别判定相容、局部相容、冲突、未覆盖或无法判断。先确认文件的历史身份，再判断如果要承接当前批准构思需要保留什么、重设什么。不得因旧稿早于批准就跳过全文，也不得把所有历史差异称为当前构思错误。

实现层：先把 writing 素材和 novel-text 正文映射到其实际声明的上游设计，再与当前目标复核。分别给出“对历史设计的实现”与“对当前目标的适配”。素材片段、设定表、连续正文是不同载体；同一片段重复出现只计一项内容承载，不能累加成完整度。正文独有的知识、能力、人物关系或结局须反向找来源，无法证明授权时写为新增/适配待核，而非自动冻结。

每条矩阵最少字段：`G-ID｜层次｜目标路径+定位｜批准路径+定位｜设计路径+定位｜实现路径+定位｜材料版本/身份｜五种口径标签｜一致性｜程度｜证据限度｜关联发现 ID`。缺失位置写明查找范围和结果，不留空、不填“同上”。多份文件对应同一目标可分行，不把目录名当作全部文件的证据。

### 4. 一致性、实现程度与权威分开记

一致性采用五态：一致、部分一致、不一致、未覆盖、证据不足。判“不一致”须有明确相反命题；没有写到应判“未覆盖”，只持有引用却无正文应判“证据不足”。基准存在待裁决冲突时，在证据不足中注明原因，不强行归入一致。

实现程度对三层分别使用下表，另列权威状态：当前批准／历史材料／草稿／待确认。程度不是质量分，也不是阶段放行。

| 等级 | 构思层 | 设计层 | 实现层 |
| --- | --- | --- | --- |
| E0 未见承载 | 目标义务在可读构思内容中无承载 | 没有对应设计 | 没有相关素材或正文 |
| E1 只有声明 | 仅概括目标或规模，缺少可核对展开 | 仅重复要求，无具体功能、依赖和状态 | 只有计划、标签或对要写内容的说明 |
| E2 局部落实 | 有若干人物/事件/约束，但链条或边界未完整呈现 | 有局部角色、场景或系统设计，关键对应仍缺 | 有素材、样片或少量正文，尚不能证明全过程 |
| E3 在该层完整可核对 | 该义务的事实、选择、后果及例外均能定位并自洽 | 功能、角色、因果、信息与承接关系均覆盖且无硬冲突 | 当前目标下连续叙事已呈现选择及后果，无相反证据 |
| EU 无法评定 | 必要内容不可读、仅有引用或基准待裁决 | 正式对应无法建立 | 无法区分设定、样片、正文身份或缺少必要上下文 |

E3 必须限定到具体目标义务，不能以某一角色写得完整推出全层完成；出现明确硬约束冲突时不得给该义务 E3，标记冲突并说明已有覆盖。汇总只给每层各等级数量、明确分母和未知数量；禁止将等级平均成“小说完成百分比”。内容覆盖率若使用，公式为“有实质承载义务数/适用义务数”，必须注明历史承载是否计入，并单列完全一致数量、冲突数量和 EU；不得命名为整体完成率。

### 5. 已定位的核对样例与误判防护

以下是定义规程的取证样例，B-实施必须在 BASE 重读上下文后独立判断，不能复制为已验收发现。

- 旧稿终止：`duanxian/novel-text/2026-06-07-duanxian-novel.md`“它·3”写出“选择：终止”及熄灯、感知场关闭；批准 JSON 的 `world/environments/7/must_hold` 明确当前实例不能自行终止，`characters/core_characters/1` 将最终关停执行交给沈逾。核对选择与执行是否混同、终止内心披露是否提前，结论须限定旧正文适配，不外推为批准构思失败。
- 主体是否未决：旧 `duanxian/design/workflow-docs/duanxian-coverage-matrix.md`“信息义务矩阵”把“R-07 是否为新主体”的终局标为 preserved-open；当前目标第一章与批准报告区分 R-07 和顾衡。检查这是否仅是读者得知阶段的设计，或会让已定人物事实重新变为未决；不能只抓一个标签定错。
- 亲属定位：旧 `duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/canonical-world-facts-v3.0.md`“人物边界”有周岚参与维护例外及复杂依恋表述；批准 JSON `characters/supporting_characters/1/must_not_imply` 禁止写成顾衡恋人、禁止用亲属保护暗示她参与袭击。应核对具体关系和因果是否冲突，不能仅以姓名相同证明可直接沿用。
- 呈现范围：批准 JSON `decision_controls/7/statement` 写“六个样章片段”，其 `fragments` 实际列 FRAG-DX-01—03；批准 MD“三个试读场景”呈现三段。另 `decision_controls/1/statement` 提及十个环境，而 `world/environments` 列十二项。要求区分统计口径、可见呈现和真实构思内容：只有在厘清范围后才判定是否构成一致性问题，不据此虚构缺失场景或认定生产工具错误。

### 6. BASE 逐文件对象清单

以下由 BASE 的 Git 树逐路径列出，文件计数为阅读和覆盖核对用，不是质量结论。每个前缀下逐行文件名与前缀拼接即精确路径；无省略通配符。每个对象的角色和版本初始判断按本节第一表继承，实施报告必须再补逐文件实际结论和证据定位。

前缀 `duanxian/`（1 文件）：

```text
novel-goals.md
```

前缀 `duanxian/conception-approved/`（6 文件）：

```text
README.md
author-decision.json
conception-completion.json
human-review-report.html
human-review-report.json
human-review-report.md
```

前缀 `duanxian/design/runs/hld/2026-07-10-duanxian-hld-workflow/`（2 文件）：

```text
gate-report.md
manifest.md
```

前缀 `duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/`（5 文件）：

```text
HLD-断线设计稿.md
canonical-world-facts-v2.0.md
canonical-world-facts-v3.0.md
gate-report.md
manifest.md
```

前缀 `duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/artifacts/`（13 文件）：

```text
01-world-entity-inventory.md
02-prd-support-matrix.md
03-world-rules.md
04-character-system.md
05-environment-system.md
06-event-system.md
07-time-information-system.md
08-thread-system.md
09-style-pov-system.md
10-inventory-reconciliation.md
11-hld-integrator.md
12-hld-integrity-report.md
final-hld-package.md
```

前缀 `duanxian/design/runs/lld/2026-07-08-duanxian-lld-workflow-blocked/`（1 文件）：

```text
manifest.md
```

前缀 `duanxian/design/runs/prd/2026-07-06-duanxian-prd-workflow-blocked/`（1 文件）：

```text
manifest.md
```

前缀 `duanxian/design/runs/prd/2026-07-07-duanxian-prd-workflow/`（1 文件）：

```text
manifest.md
```

前缀 `duanxian/design/runs/prd/2026-07-07-duanxian-prd-workflow/artifacts/`（11 文件）：

```text
00-proposal-risk-report-human-confirmed.md
01-part-scope.md
02-part-goal.md
03-trunk-scenes.md
04-conflict-value.md
05-information-flow.md
06-freeze-boundaries.md
07-hld-expansion-requirements.md
08-prd-integrator.md
09-prd-risk-report.md
final-prd-package.md
```

前缀 `duanxian/design/runs/proposal/2026-07-05-duanxian-proposal-workflow/`（1 文件）：

```text
manifest.md
```

前缀 `duanxian/design/runs/proposal/2026-07-05-duanxian-proposal-workflow/artifacts/`（14 文件）：

```text
01-intake-boundary-ledger.md
02-reader-promise-pre-story.md
03-core-concept-pre-story.md
04-storyline-design.md
05-storyline-quality-report.md
06-reader-promise-final.md
07-core-concept-final.md
08-final-promise-concept-consistency.md
09-macro-structure.md
10-core-character-frame.md
11-world-premise.md
12-ending-direction.md
13-proposal-integrator.md
14-proposal-risk-checker.md
```

前缀 `duanxian/design/specs/`（10 文件）：

```text
2026-06-06-digital-life-novel-design.md
2026-06-06-first-meeting-digital-life-novel.md
2026-06-06-hld-digital-life-novel.md
2026-06-06-lld-digital-life-novel.md
2026-06-06-prd-digital-life-novel.md
2026-06-06-reference-survey.md
2026-06-06-science-background-digital-life-novel.md
2026-06-06-technical-systems-digital-life-novel.md
2026-07-05-duanxian-intake.md
2026-07-05-duanxian-proposal.md
```

前缀 `duanxian/design/specs/lld/characters/`（7 文件）：

```text
2026-06-07-character-betrayer.md
2026-06-07-character-colleagues.md
2026-06-07-character-it.md
2026-06-07-character-jiling.md
2026-06-07-character-qianxu.md
2026-06-07-character-shenyu.md
2026-06-07-character-zhengbozhou.md
```

前缀 `duanxian/design/specs/lld/scenes/`（10 文件）：

```text
2026-06-07-scene-K1.md
2026-06-07-scene-K10.md
2026-06-07-scene-K2.md
2026-06-07-scene-K3.md
2026-06-07-scene-K4.md
2026-06-07-scene-K5.md
2026-06-07-scene-K6.md
2026-06-07-scene-K7.md
2026-06-07-scene-K8.md
2026-06-07-scene-K9.md
```

前缀 `duanxian/design/specs/lld/spaces/`（9 文件）：

```text
2026-06-07-space-apartment.md
2026-06-07-space-city.md
2026-06-07-space-corridor.md
2026-06-07-space-digital-realm.md
2026-06-07-space-hotel-room.md
2026-06-07-space-meeting-room.md
2026-06-07-space-operation-room.md
2026-06-07-space-security-hall.md
2026-06-07-space-server-room.md
```

前缀 `duanxian/design/workflow-docs/`（11 文件）：

```text
duanxian-causal-storyline.md
duanxian-conception-review.md
duanxian-core-character-design.md
duanxian-coverage-matrix.md
duanxian-development-map.md
duanxian-intent-card.md
duanxian-interview-review-brief.html
duanxian-map-check.md
duanxian-narrative-contract.md
duanxian-novel-design-brief.md
duanxian-subject-definition.md
```

前缀 `duanxian/novel-text/`（1 文件）：

```text
2026-06-07-duanxian-novel.md
```

前缀 `duanxian/writing/characters/`（7 文件）：

```text
2026-06-07-writer-R07.md
2026-06-07-writer-betrayer.md
2026-06-07-writer-colleagues.md
2026-06-07-writer-jiling.md
2026-06-07-writer-qianxu.md
2026-06-07-writer-shenyu.md
2026-06-07-writer-zhengbozhou.md
```

前缀 `duanxian/writing/scenes/`（1 文件）：

```text
2026-06-07-scene-K1.md
```

前缀 `duanxian/writing/spaces/`（9 文件）：

```text
2026-06-07-writer-apartment.md
2026-06-07-writer-city.md
2026-06-07-writer-corridor.md
2026-06-07-writer-digital-realm.md
2026-06-07-writer-hotel-room.md
2026-06-07-writer-meeting-room.md
2026-06-07-writer-operation-room.md
2026-06-07-writer-security-hall.md
2026-06-07-writer-server-room.md
```

## 三、总体方案

### 1. 三步协议与独立性

| 阶段 | 环境与模型 | 输入 | 工作与输出 | 放行条件 |
| --- | --- | --- | --- | --- |
| B-定义（本作业） | 本作业独立 worktree；计划角色 GPT-6-Astra/High | 冻结任务、BASE 材料 | 定义规程、对象全集、交接与验收标准 | 定义书自检及 Owner/验收流程确认后交接 DEF |
| B-实施 | 编排方分配的独立 worktree；Kimi-K3.1-Pro | BASE、DEF、实施冻结契约 | 全量阅读、矩阵、发现、实现程度和报告 | 自检合格并提交推送 IMPL；等待独立验收 |
| B-独立验收 | 与实施分离的上下文/作业；GPT-6-Astra/High | 同一 BASE、DEF、指定 IMPL、验收契约 | 独立重建关键比较和抽查，形成 PASS/FAIL | 全检查通过才 PASS；不通过逐项回实施修订 |

表中模型为冻结任务规定的角色配置，不是本文件对实际运行模型的检测结果。沿用“定义 → 实施 → 独立验收 → 失败回实施”的 R1 调度形式，内容基线与审视对象按 R2 重建；不得继承 R1 工程结论。编排方负责安排环境、传递提交和记录状态，不替代实施者和验收者认定事实。

### 2. 交接信封

每次交接必须携带作业标识、BASE 完整 SHA、DEF 完整 SHA、报告路径及 IMPL 完整 SHA、工作分支、文件 SHA-256、检查命令与结果摘要、适用义务数和文件覆盖数、未决项。验收修订时保留 BASE 和 DEF，新增 IMPL 版本，列清受影响的 G-ID 与发现 ID。若材料或定义必须变更，先形成范围变更请求并由相应责任方冻结新版本；禁止在原结论中偷换 BASE。

独立验收者先从目标和批准包重新提取关键约束、固定抽样表，再对照实施结论，避免把实施者的摘要当作事实源。不可访问的运行期文件只记录证据限度，不向外部系统取回、不从报告重建原包；如果因此无法得出某项内容结论，给 EU 并明确影响，而非无限等待或伪造完成。

## 四、任务路线图

| 里程碑 | 执行责任 | 完成条件 | 不通过的返回点 |
| --- | --- | --- | --- |
| B-D0 初始化与范围确认 | B-定义 | 已固定 BASE、工作分支、ACK 和只读材料边界 | 环境/冻结信息问题交编排方，业务不得猜测 |
| B-D1 定义交付 | `duanxian-audit2-bdef-001` | 本文六节、自检证据、DEF 已提交推送 | 只修定义书，重新检查 |
| B-I1 阅读与基准建账 | `duanxian-audit2-bimpl-001` | 121 对象与辅助材料阅读清单、G-ID 及版本分类完成 | 漏项回阅读；基准冲突标待裁决 |
| B-I2 三层核对与报告 | B-实施 | 全部义务有矩阵处置，正文及全部素材纳入，报告符合字数和结构 | 回具体层、文件和义务，不只润色结论 |
| B-I3 自检与交接 | B-实施 | 机械与语义自检合格、IMPL 提交推送、交接信封齐全 | 修订后重跑相关检查 |
| B-A1 独立验收 | `duanxian-audit2-bacc-001` | 本文第六节逐项 PASS、抽查可复现、无阻塞问题 | FAIL → B-I1/B-I2/B-I3 → 新 IMPL → 再验收，直至通过 |
| C 预告 | 另行冻结的 C 作业 | 仅以已验收报告为输入，将有证据的构思/设计层不一致整理成 ISSUE 候选 | 未验收结论不得直接转 ISSUE；本作业不创建 |

C 候选至少携带发现 ID、目标、两侧内容证据、版本、影响和建议责任层；正文适配问题先归到其设计依据和修订责任，不把所有草稿差异等同于构思缺陷。属于有意保留的开放问题、只有证据不足的项和纯工程分流项不自动生成缺陷 ISSUE。没有实质不一致时允许 C 候选为空，禁止为凑数造问题。

## 五、实施作业工作指令

### 步骤 0：固定输入与写入边界

确认实施冻结契约已授权报告路径及本作业分支；记录 BASE、DEF 和开工 HEAD。用 `git status --porcelain` 检查已有改动，不能清理他人文件。检查对象能由 `git show BASE:路径` 读取；后文命令中的 BASE 使用完整字面 SHA。若工作树材料与 BASE 不同，直接从 BASE 读取，不 reset、checkout 覆盖用户内容。DEF 用于规程，不加入故事证据。

预期：输入版本明确、工作树起始状态可追溯；不满足则只记录阻塞并交编排方，不擅自扩大权限或改冻结文件。

### 步骤 1：按顺序全文阅读并登记

1. 读 `duanxian/novel-goals.md` 全文；再读根 `README.md`、`duanxian/README.md`、`engine/docs/ai-novel-workflow/README.md`。规范只取小说内容与作者决定边界。
2. 读批准目录 README、作者决定、完成记录，随后 MD 全文、JSON 全部内容和 HTML 全部正文（含折叠内容）。JSON 的 must_hold、must_not_imply、decision_controls、人物、环境、事件、样片均要读；大量重复追溯条目可程序化遍历去重，但保留所有原始定位并核对来源范围，不把标题扫描当全文审视。
3. 读 workflow-docs：意图卡 → 主体定义 → 核心角色 → 因果故事线 → 叙述契约 → 开发地图 → 覆盖矩阵 → 地图自检 → 构思交接审阅 → NDB → HTML 访谈简报。具体文件名以第二节清单为准；辨明每份材料声明的版本和它引用的版本。
4. 读 specs 根部十篇，再读 LLD 人物七篇、空间九篇、场景 K1—K10 十篇；日期和“已完成”不决定权威。阅读科学/技术稿时只问小说设定相容性，不对现实科学作新研究。
5. 读 runs 的 proposal → PRD → HLD → LLD。每个 run 先读 manifest、入口或汇总说明，再读所有 artifacts；HLD 同时核对 v2/v3、主稿和整合稿。保留它们自己的历史状态，只把小说设计内容送入一致性判断。
6. 读 writing 全部人物、空间、K1 场景素材；再从首至尾读 novel-text 唯一草稿，建立段落/标题定位。最后读第二节列出的三份 design 辅助材料，只核对小说设计/参考身份。

预期：覆盖账逐文件记录“路径、blob/SHA-256、全文读取完成、材料角色、对应目标、初步状态、证据定位”；三份 README 参照和三份 design 辅助材料单列。重复内容也不能跳过所属文件的版本与差异核对。冻结材料有旧路径引用时记录原文，引用本次证据用实际存在路径；不要由旧路径联想到工程问题。

### 步骤 2：拆目标、固定口径和正式 ID 边界

将目标六章所有内容要求拆成可判定的 G-ID；区分硬约束、结构/质量目标、作者开放项及仅供参照的流程规范。每条必须能回答“什么事实或表现会支持它，什么反例会推翻它”。将批准包现有 ID 和 JSON Pointer 原样保存；自己的 G-ID、F-ID 不替代正式内容 ID。

沿用目标文档的五种标签，精确写为：

| 标签 | 使用规则 |
| --- | --- |
| 【当前权威口径】 | 只标当前目标/批准材料可证明的事实或状态；须引用批准范围，不给历史内容升级 |
| 【历史/旧链口径】 | 标旧稿、旧链设计及其当时结论；对当前版的适配另列判断 |
| 【未完成项】 | 在指定 BASE 范围内尚未证明完成、缺少可核对内容或缺少明确对应；避免写成“绝对不存在” |
| 【流程规范】 | 标应该如何区分构思、设计、写作和作者责任；不能拿规范存在证明作品已达到，也不审查其工具实现 |
| 【推断】 | 标审视者从证据作出的解释、建议或适配判断；同时列依据、反证条件和不确定性，不能伪称作者决定 |

一段同时涉及多种来源时拆段或逐句标注；报告中的审视结论通常包含来源标签及【推断】判断，不能仅贴一个“当前权威”标签把分析升级为批准。目标未指定的读者、篇幅、章数、续作不能自行补齐。

预期：G-ID 总表、适用层次、最低正反证条件和五标签映射齐全。

### 步骤 3：构思层核对

按人物、关系、世界/环境、事件因果、主体/支线、披露、终局顺序，核对目标与批准包；对每个核心约束检查 MD、JSON 与 HTML 的表达是否同义。尤其核对“选择结束”和“能自己关停”、“旧情”和“新感情”、“片段记忆”和“现实感知”、“危机解除”和“伦理解决”的区别。

对 17 人逐一建条目，按批准文实际列出的环境逐一核对，检查故事线的功能与八次推进关系。对于“43 主要事件”等呈现规模，先找本地明确内容与来源 ID；若无法逐事件重建，列明实际可核对范围，不能凭数字捏造事件清单或从样章逆推事实。三种呈现之间的数量差异先查统计对象，再判断内容影响。

预期：构思层矩阵每个适用 G-ID 有结论；任何批准包内部疑点有双侧定位和受影响范围；承认构思已获批准但不将其推成所有后续层均完成。

### 步骤 4：设计层核对

逐文件提取实际承载的目标、人物、关系、事件、空间、能力和 POV。建立“历史 ID/名称 → 当前内容对象”的显式映射，分类为保留、需适配、无对应、待确认；每条说明证据。对 C/M/K 等旧编号保留源前缀和文件版本，禁止把 K1=M01=当前第一章。

重点追踪：主体是否被危机行动取代；沈逾是否被赋予启动全权；亲属是否被改成恋人或单纯情报筹码；R-07 是否获得实时感官、自行关停或外网能力；人质、专家、硬件和授权链是否有具体承载；关停前后的知情者是否一致；历史章数/幕数/系列计划是否越过当前开放边界。任何“未覆盖”都要给出读过的完整范围，不以一次关键词未命中定缺失。

预期：全部 96 个设计对象均有处置，其中状态型 manifest/gate 允许注明“仅作历史身份参照”，但须检查是否含小说设计内容；所有关键功能在三层矩阵中可追踪。建议只说明需调整的设计责任和约束，不直接替作者重设情节。

### 步骤 5：实现层核对

对 17 份 writing 区分人物素材、空间素材和场景 prose；逐项列其能支持哪些目标、仍缺哪些条件。对 novel-text 逐段记录当前叙述者、可获信息、实际动作、状态变化、上下文触发和退出结果。先对照历史设计解释文本来源，再对照当前目标判断适配，不能因为文本源于旧设计就免查。

至少完整复核主体形成、沈逾接受/承担职责、关系形成、记忆调用、行动线索交付与核验、终止选择及执行、终局余波。对正文中时间、姓名、空间与知情状态作内容连续性核对；缺少某链条时说明它在哪些段落或素材中有部分出现，不一概判零。三段批准样片只验证构思阅读体验，不能作为 novel-text 已完成的证据，更不能替代未写出的关停和危机闭环正文。

预期：每一目标在素材与连续正文中分别有状态；所有相反证据能定位到标题和相邻段落，避免仅引用单句造成误判。

### 步骤 6：归并发现、分级与程度统计

为实质问题建立 `F-001` 起的稳定编号，字段为：层次、G-ID、版本、来源标签、目标侧证据、对象侧证据、判断与反例检查、影响、实现等级、建议责任层、是否可供 C 后续整理。内容重复只保留一个主发现并列影响文件，不重复计数。

优先级：P0 为破坏主体、关键能力、危机闭环或终局等硬约束的冲突；P1 为关键动机/因果/关系/披露缺口；P2 为局部表达、连续性或呈现范围不一致。优先级衡量小说内容影响，不是工程故障等级，也不代替证据置信度。证据不足独立列示，不因不确定就一律标 P0。区分“历史版本差异”“当前基准内部疑点”“当前目标未落实”三种性质，不能合并成一个笼统失败。

预期：每层程度分布有分母、EU 和历史材料说明；工程候选已分流且无业务明细；C 候选不包含仅有猜测的事项。

### 步骤 7：按固定章节撰写报告

报告路径固定为 `outputs/duanxian-audit2/implementation-review-r2.md`，一级标题自定，以下九个二级标题逐字使用，不加同级额外章节：

1. `## 一、审视摘要与范围`
2. `## 二、基线、权威与目标义务`
3. `## 三、对象覆盖与版本关系`
4. `## 四、构思层一致性`
5. `## 五、设计层一致性`
6. `## 六、实现层一致性`
7. `## 七、实现程度与未完成项`
8. `## 八、发现、修订优先级与交接`
9. `## 九、证据索引与自检记录`

第一节给三层主要结论及限制，不给空泛评分。第二节放 G-ID、标签和基准冲突。第三节解释文件版本映射及覆盖情况。第四至六节分别给矩阵、支持证据、反例和结论。第七节列每层等级、分母、未知及下一步创作条件。第八节放 F-ID、责任层与 C 候选。第九节集中保存逐文件账、证据索引、命令结果和提交交接说明。

字数规则：第一至八节正文中的汉字字符（U+3400–U+4DBF、U+4E00–U+9FFF）计为中文字；范围 8000–15000。标题、表格中的汉字计入，代码块、行内代码和第九节不计。第九节的路径清单不能用来凑字数；同样禁止通过复制大段源文填充篇幅。引用以短引文加解释为主，保留定位。

证据规则：每条实质结论至少一个明确目标来源和一个对象来源；跨层结论补齐经过的中间层。Markdown 使用路径+小节/稳定行号，JSON 使用路径+JSON Pointer，HTML 使用路径+标题/元素 ID 及文本定位。行号按 BASE 计算；推荐 `git show BASE:路径 | nl -ba`。推断必须写推导桥梁；“不存在”必须说明完整检索范围、方法和例外，不能用输出截断或 grep 未命中证明不存在。

### 步骤 8：自检、提交推送与哨兵

先运行第六节机械命令，再逐条自查语义检查单，核对全部文件覆盖和 G-ID。检查 `git diff --check`，以及从开工 HEAD 至待提交的变更只包含报告；若另有用户改动，不暂存、不撤销、不混入提交。只对报告路径执行 `git add -- outputs/duanxian-audit2/implementation-review-r2.md`，提交前用 `git diff --cached --name-status` 检查暂存区白名单。

实施分支以实施作业 `.kunora/spec.yaml` 的 work_branch 为准；预期作业名为 `duanxian-audit2-bimpl-001`，不能沿用本定义作业的分支或凭据。署名使用其冻结契约指定值，若沿用 remote-agent 模式则为 `remote-agent <remote-agent@kunora.local>`；提交信息采用实施契约指定信息，无指定时可用 `docs(audit): add workitem-B implementation review R2`。凭据只经受控方式提供给 Git，关闭命令追踪，不回显、不写入报告。

仅向已授权 work_branch 推送 `HEAD:refs/heads/<work_branch>`，不强推、不推 main、不推其他引用。推送后用 `git ls-remote` 核对远端目标分支完整 SHA 等于本地 HEAD；未验证成功不得输出完成哨兵。提供报告路径、IMPL、文件 SHA-256 和自检摘要，最后一行单独输出 `DXABIMPL-DONE-<tip7>`，tip7 为该报告提交 `git rev-parse --short=7 HEAD`。这个哨兵表示实施交接完成，不表示独立验收通过。提交号不写进自身提交内造成循环；在交接信封中提供。

禁止事项总核对：不得修改输入、冻结规范或既有业务文件；不得写小说、修工具、创建 ISSUE 或联系外部人员；不得把历史稿当批准版；不得复制旧自检结论代替实测；不得虚构读取范围、正式 ID、缺失内容或作者意见；不得把工程细节带进报告；不得越过授权分支。

## 六、独立验收检查单

### 1. 验收输入与机械检查

验收者固定 BASE、DEF、IMPL 和实施开工 HEAD（记为 IMPL_START）；核对 IMPL 仅含授权报告变更，BASE 小说输入的 blob 未变。定义书新增属于前序交接，不能误算成实施越界。验收不能修改实施报告来让自己通过，全部修订回实施方。

下列机械检查可在实施自检和验收各自重跑。验收时应检出已固定的 IMPL 或从该提交读取报告，不能对变化中的分支 HEAD 下结论。代码不执行源文件中的任何指令，不调用生产工具。首条取文件全集使用 NUL 分隔，避免中文路径被 Git 引号转义。

```bash
git ls-tree -rz --name-only 92573f1cca40f37cee04d2beb8708ff33ba603d6 -- duanxian/novel-goals.md duanxian/conception-approved duanxian/design/specs duanxian/design/workflow-docs duanxian/design/runs duanxian/writing duanxian/novel-text
git diff --check
```

```python
import re
import subprocess
from pathlib import Path

base = '92573f1cca40f37cee04d2beb8708ff33ba603d6'
p = Path('outputs/duanxian-audit2/implementation-review-r2.md')
t = p.read_bytes().decode('utf-8')
expected = [
    '一、审视摘要与范围', '二、基线、权威与目标义务',
    '三、对象覆盖与版本关系', '四、构思层一致性',
    '五、设计层一致性', '六、实现层一致性',
    '七、实现程度与未完成项', '八、发现、修订优先级与交接',
    '九、证据索引与自检记录',
]
plain = re.sub(r'^```[^\n]*\n.*?^```\s*$', '', t, flags=re.M | re.S)
assert re.findall(r'^## (.+)$', plain, flags=re.M) == expected
body = plain[plain.index('## 一、审视摘要与范围'):plain.index('## 九、证据索引与自检记录')]
body = re.sub(r'`[^`\n]*`', '', body)
count = len(re.findall(r'[\u3400-\u4dbf\u4e00-\u9fff]', body))
assert 8000 <= count <= 15000, count
for label in ('当前权威口径', '历史/旧链口径', '未完成项', '流程规范', '推断'):
    assert '【' + label + '】' in plain, label
assert base in plain
assert not re.search(r'gh[pousr]_[A-Za-z0-9]{20,}|glpat-[A-Za-z0-9_-]{15,}', t)
roots = [
    'duanxian/novel-goals.md', 'duanxian/conception-approved',
    'duanxian/design/specs', 'duanxian/design/workflow-docs',
    'duanxian/design/runs', 'duanxian/writing', 'duanxian/novel-text',
]
raw = subprocess.check_output(['git', 'ls-tree', '-rz', '--name-only', base, '--', *roots])
files = [x.decode('utf-8') for x in raw.split(b'\0') if x]
assert len(files) == 121, len(files)
# 实施报告的证据账必须逐条写完整路径，不用目录别名替代。
missing = [x for x in files if x not in t]
assert not missing, missing
print('MECHANICAL-PASS', 'Chinese_chars=', count, 'inventory=', len(files))
```

代码只检查格式、计数和路径出现，不证明实际读过、引文正确或文学判断成立；秘密模式扫描也只是辅助，不替代人工检查。记录真实命令、输入提交、退出码和输出，不把代码块本身当执行证据。另以 `git diff --name-status IMPL_START IMPL` 与 `git show --stat IMPL` 检查提交范围；其中两个符号须替换为交接中实际完整 SHA。

### 2. 逐项语义与边界验收

| 编号 | 检查动作 | PASS 条件 | FAIL 与返回位置 |
| --- | --- | --- | --- |
| A01 版本固定 | 独立读取 BASE、DEF、IMPL，核对报告中的版本与路径 | 所有小说事实来自 BASE；定义规则来自 DEF；报告锁定 IMPL | 混版、拿当前工作树代 BASE：回步骤 0 |
| A02 完整覆盖 | 由 BASE 重建 121 文件全集，与逐文件账做集合差；再核对六份参照/辅助材料 | 无漏项、无重复凑数；状态型文件有说明，正文和全部素材有实质核对 | 只有目录标题或路径堆砌：回步骤 1、4、5 |
| A03 目标完整 | 从目标六章独立抽取义务，逐条对照 G-ID | 最低控制面全部覆盖，新增义务有来源；开放项未被擅定 | 漏目标或把规范当已完成：回步骤 2 |
| A04 构思自洽 | 重读批准人物、世界、故事、样片及控制条目，对照三种呈现与目标 | 有支持与反例，范围差异经核实；未无证据撤销批准或填补缺失本体 | 只读 MD 摘要或直接判批准无效：回步骤 3 |
| A05 设计落实 | 复验历史文件到当前义务的映射与适配判断 | 每条主干有承载或明确缺口，旧 ID/角色映射有理由 | 文件名相似即当同版、旧 pass 即完成：回步骤 4 |
| A06 正文落实 | 全文复读唯一 novel-text，并按素材类别抽查 | 选择、感知、知情、核验、关停和余波判断与上下文相符；素材与正文分列 | 单句断章、片段冒充全书或漏终局：回步骤 5 |
| A07 实现程度 | 按 E0—E3/EU 重新计算汇总及分母 | 一致性、程度、权威分离；硬冲突无 E3；未知和历史承载独立列示 | 无依据完成率、一个文件推出全层完成：回步骤 6 |
| A08 证据与口径 | 逐项打开所有关键发现的双侧证据，检查五种标签 | 路径/定位可复验，推断可推翻，缺失结论有限定范围 | 虚构引文、断言超出证据或标签误用：回对应内容步骤 |
| A09 防跑偏 | 人工通读全部摘要、发现、建议、程度统计及 C 候选 | 无工程基础设施类结论或旧工程问题复述；仅允许范围排除声明与取证命令 | 工程修复清单混入：删除越界内容并重做受影响结论，回步骤 6、7 |
| A10 作者边界 | 检查主体、关系、终局、续作、读者与结构数量 | 不替作者裁定开放项，不由样片或旧稿新增批准事实 | 擅自冻结故事：回步骤 2—6 |
| A11 交付范围 | 核对提交差异、凭据风险、推送分支与 SHA | 只交付授权报告，未修改旧文件、未创建 ISSUE；远端对应 IMPL | 越界写入/推送需停止收口，由责任方处理，禁止验收者掩盖 |
| A12 独立性与可交接 | 检查抽样重建、命令实测、修订闭合和信封 | 有独立证据，不把实施自评或编排者意见当验收；C 候选有来源 | 无实测或只改措辞：继续 FAIL 并给具体修正项 |

A09 不采用关键词一票否决：小说世界中唐黎、硬件、授权和日志本来就是内容对象；要看结论指向小说的因果和责任，还是指向构建小说的工程设施。对后者只允许范围分流声明，不允许隐藏在脚注或附录继续复述。

### 3. 可复现抽查方案

先完整复读目标、批准 MD/JSON 的业务条目及唯一正文；这是必查，不是随机抽样。然后对报告全部 P0/P1、全部“不一致”、全部基准待裁决和全部“当前版 E3”结论逐项复验。其他结论按层次分别按 G-ID 字典序排序，每层取首项、末项及每第五项；不足五项全查。额外从每个对象类别选至少一条“相容”判断和一条“未覆盖/证据不足”判断，如该类没有相应结论则注明无样本，不能虚造。

对 writing 至少覆盖人物、空间、场景三类；对设计至少覆盖 specs 根稿、LLD 人物/空间/场景、workflow-docs 和 runs 的 proposal/PRD/HLD/LLD。对每个样本记录 G-ID/F-ID、两侧路径与定位、独立判断、与实施结论是否一致、理由。若任一样本出现假引文、错版本或漏掉实质反例，扩大到同层同类结论全查；系统性错误返回重做，不能抽到一个正确样本后停止追查。

对“未覆盖”的复验必须结合全文件账、完整相关文本和同义功能检索；搜索只是定位工具。发现反例后更新整条证据链及程度统计，不仅修一段文字。对历史稿与新版之间的差异，额外检查报告有没有把历史适配风险误述为当前构思自相矛盾。

### 4. 结论规则与迭代修正模板

验收记录逐项给 PASS/FAIL/不适用及理由；核心检查不得以“不适用”绕过。只有 A01—A12 和机械要求全部满足、修正项全部闭合，才给该 IMPL 的审视报告 PASS。内容上的未完成项或 EU 可以保留，只要证据限度真实且报告没有作出超过证据的结论。无法读取必要输入导致验收无法进行时，记录阻塞和缺失输入，不误报 PASS。

修正指令采用下列模板，由独立验收者填写，编排者只负责转交：

```text
验收轮次：R<n>
结论：FAIL
固定版本：BASE=<完整 SHA>；DEF=<完整 SHA>；IMPL=<完整 SHA>
失败检查项：Axx
关联对象：<完整路径与定位>；G-ID=<编号>；F-ID=<编号或无>
实测事实：<目标侧内容、对象侧内容、复现命令/阅读范围>
错误性质：<漏读/错版/缺证/因果判断/口径/程度统计/越界>
必须修正：<补读范围、需重建的比较、需撤回或限定的结论>
影响扩展：<同类文件、关联目标、汇总和 C 候选需要同步更新>
允许改动：仅本实施作业授权报告；不改 BASE、DEF 或小说源材料
复验条件：<逐条可验证条件；重跑哪些机械与语义检查>
下一交接：<新 IMPL、报告 hash、差异摘要、未决项>
```

修订后的验收既复查上一轮所有失败项，也按固定方案重新抽查受影响层次及汇总。保留各轮 IMPL 与结果的对应，不能删除失败记录使历史看似一次通过。最终 PASS 仅表示这份小说构思/设计一致性审视报告可供 Owner 与 C 工作项使用，不表示小说已定稿、工程已合格或后续 ISSUE 已创建。
