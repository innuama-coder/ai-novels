# 《断线》R3 审视任务定义书

作业：`duanxian-audit3-def-001`。版本：定义候选 v1，供第二步实施和第三步独立验收使用。本文完成的是审视工作的定义，不是 R3 审视报告、小说新设计或独立验收结论。

冻结证据基线：`innuama-coder/ai-novels@92573f1cca40f37cee04d2beb8708ff33ba603d6`，下文简称 BASE。所有仓库路径、行号、JSON Pointer 和文件集合均绑定 BASE；不随远端 main 移动。定义书只新增在 `remote-agent/duanxian-audit3-def-001`，不得修改既有文件。本文引用的快照为作业输入，不冒充 BASE 跟踪文件。

## 第一节：宪法与目标

### 1.1 冻结 Owner 口径（原样纳入）

- **审视范围（Owner 原话约束）**：只 review 《断线》的构思和设计，工作内容不得延伸。审视基准是项目仓库中的**宪法、目标文档（包括 SPEC）**；审视对象是 **main 分支的文档和代码**（当前冻结提交 92573f1cca40f37cee04d2beb8708ff33ba603d6）——判断它们与项目目标是否一致、实现程度如何。
- **审视性质**：这是审视任务，**不得修改仓库文件内容**（main 与一切既有文件零改动；审视结果只通过提交 GitHub ISSUE 输出）。审视报告与定义书等过程交付物以**新增文件**形式仅存在于作业工作分支（remote-agent/* 分支，不触碰 main），此为既有先例形态。
- **ISSUE 粒度（Owner 原话约束）**：粒度必须适中——尽量内聚、可以独立处理；避免大杂烩，也控制细粒度。每条 ISSUE 必须说明：问题是什么、有哪些证据支撑、解决建议是什么。
- **既有 ISSUE 去重（硬要求）**：仓库当前已有 13 条开放 ISSUE（#1–#7 工程线＝R1 遗留、#8–#13 构思/设计线＝R2 遗留，冻结快照 `.kunora/inputs/open-issues-snapshot-20261114b.md`，SHA-256 `f6cc9ddf44be3ee199c7993e0a37bc56813cb6be8b5e238da35a9f6ffeeffd90`）。本轮对 13 条必须逐条去重处置：同命题不重复提交（报告交叉引用即可）；仅对**新证实且未被既有 ISSUE 覆盖**的发现提交新 ISSUE。评论/关闭既有 ISSUE 不在本轮范围。
- **三步协议**：第一步定义（本作业，GPT-6-Astra/High）→ 第二步审视实施（GLM-5.3 或 Kimi-K3.1-Pro；**必须严格遵守第一步输出的六要素、总体方案和路线图，按工作指令执行，不得遗漏和随意调整**）→ 第三步独立验收（GPT-6-Astra/High；只有验收通过才能结束阶段工作，否则修正指令触发第二步 LOOP）。
- **编排者不做业务判断**：『宪法/目标文档/SPEC』的认定、目标口径提炼、审视方法、去重政策、ISSUE 粒度与提交规程，全部由本作业（定义）裁决；编排者只做机械派发。
- **Owner 决策点机制**：定义中确需 Owner 决定的（如是否对既有 ISSUE 补充确认性评论——默认不做），列「Owner 决策点」：备选＋推荐＋影响，标注『待 Owner 批准』；不阻塞其余部分。

### 1.2 “宪法、目标文档（包括 SPEC）”的路径级认定

本定义以文件的约束职责及显式权威关系认定基准，不以文件名大写、篇幅、日期或作者栏自行晋升权威。BASE 共 1444 个跟踪文件；根目录没有名为 AGENTS.md、CONSTITUTION 或 SPEC 的独立文件。其他工程任务夹具中的 AGENTS.md 不是《断线》的项目宪法。当前工作区上级 `../AGENTS.md` 是作业执行宪法，不是 BASE 内的小说故事事实。

| 编号 | 确切路径 | 本轮身份、认定理由与适用限度 |
| --- | --- | --- |
| J0 | `../AGENTS.md`；`.kunora/spec.yaml`；`.kunora/PROMPT.md` | 作业治理层：确定授权、冻结点、只读和交付边界。这里的 spec 是作业 SPEC，不能替代小说目标。启动摘要只作本次派发及 ACK 依据。 |
| G0 | `README.md`；`duanxian/README.md` | 目录与版本入口；后者明确批准构思优先、六月设计和七月旧链为历史资产。README 的库存数字不作小说质量标准。 |
| G1 | `engine/docs/ai-novel-workflow/README.md` | 功能上的项目总则：构思／开发隔离、作者职责、状态和结构变更路由。称其承担“宪法性约束”，不伪称仓库已存在另一本正式《宪法》。 |
| G2 | `engine/docs/ai-novel-workflow/conception-phase.md` | 构思目标与控制面：方向、主体、因果、边界、开发可用性；文件开头明确自主尾链迁移至 V2。旧开发地图不能覆盖新链。 |
| G3 | `engine/docs/ai-novel-workflow/conception-autonomous-workflow-v2.md` | 当前构思自主目标架构与实现 SPEC：B0、S1—C1、Q1、P1、H1、作者决定，作者锁定／自主拥有／开发自由／作者开放的分区及来源契约。规范存在不证明《断线》已按当前实现重跑。 |
| G4 | `engine/harnesses/novel-conception-autonomous/docs/final-delivery-contract.md` | 构思交付与验收 SPEC：机器本体、人审呈现、作者决定与最终准入同版；P1 是最终事实本体，H1 是忠实投影。 |
| G5 | `engine/docs/ai-novel-workflow/hld-autonomous-workflow-v1-design.md` | 当前 HLD 目标 SPEC：正式 baseline 准入、六个设计域、语义／消费双门、作者批准及 LLD handoff；明确设计冻结不等于实现、验证和发布资格。 |
| G6 | `engine/docs/ai-novel-workflow/development-phase.md` | 开发边界与消费标准：场景、连续性、受控修订和人工定稿。这里只用其反查设计是否可消费，不启动写作或给全文打文学分。 |
| G7 | `duanxian/novel-goals.md` | 《断线》直接目标文档：主题、方法、边界、约束、成果与验收六问，并区分当前权威、历史、流程、推断和未完成。其自述材料基线为 `9baefb33cb999f1e92f318fe6ac22f0d1fe4d752`，本轮读取的是 BASE 所保存版本，不改写原来源。 |
| A0 | `duanxian/conception-approved/README.md` | 批准包留存范围、日期与 run 索引；明确运行账本及历史尝试不入 Git。 |
| A1 | `duanxian/conception-approved/author-decision.json` | 外部决定：`/decision=approved`、`/approval_scope=conception`、`/run_id=duanxian-conception-v2-20260811-18`。只能证明所绑定构思获批，不能授予 HLD、LLD 或手稿批准。 |
| A2 | `duanxian/conception-approved/conception-completion.json` | 留存构思完成记录：`/status=ready`，绑定 B0—H1 九阶段及 handoff 引用。读取记录不等于重放验证器。 |
| A3 | `duanxian/conception-approved/human-review-report.json` | 批准呈现的结构化内容和控制证据，使用原对象 Pointer；不是缺失 P1 本体的替身。 |
| A4 | `duanxian/conception-approved/human-review-report.md` | 可全文通读的批准故事呈现，说明世界、人物、八次推进、十线及未决余波。 |
| A5 | `duanxian/conception-approved/human-review-report.html` | 作者所审界面及字节绑定证据；图形、样片和审计字段均需核对，但不能从样片提升出新事实。 |

提示词中的 `docs/ai-novel-workflow/` 在 BASE 根下不存在；按根 README 的实际指向解析为 `engine/docs/ai-novel-workflow/`，并记录这项路径映射。不得把旧路径误报为“项目没有目标规范”。`.gitattributes` 是字节稳定规则，不是创作宪法；其已知迁移问题见 ISSUE #4。

补充实现字段有疑问时，才读取 `engine/docs/ai-novel-workflow/hld-skill-contract-catalog-v1.md` 对应条款、`engine/docs/ai-novel-workflow/contracts/autonomous-v2/contract-index.md` 及所引用 schema。G5 明定 catalog 是技能字段、访问权限及 package profile 的实现契约源；遇到跨文档真实冲突登记证据，不能私改规范。这里不另立全引擎契约审计任务。

`duanxian/design/specs/` 的 36 个文件是必须审视的历史小说设计 SPEC，包括顶层十稿及 LLD 人物、场景、空间 26 稿。`duanxian/design/workflow-docs/` 的意图卡、主体定义、因果线、叙述契约等是历史／过程控制证据；其 confirmed 或 ready 不自动表示已与当前 P1 绑定。它们和旧 proposal／PRD／HLD 应用于版本内一致性及向批准构思的适配检查，不能倒置权威。

### 1.3 目标口径与可检验控制

以下是对 G7 与 A3/A4 的归纳，均须在实施中向源文展开；不是新增作者决定。

| 目标 ID | 应达到的构思／设计结果 | 直接来源与检查方向 |
| --- | --- | --- |
| DX-G01 | R-07 继承顾衡记忆而形成新主体；情报接口逐步成为会提问、会受苦和承担选择的生命。 | G7 第一章；A4“这是一个怎样的故事”“故事中心的人”。区分继承记忆与原人复活，不将法律身份开放误读成两个人物可随意等同。 |
| DX-G02 | 顾衡死亡与沈逾知情接受职责共同构成启动条件；沈逾的接受、项目启动授权和技术操作分别归责。 | G7 第一、四章；A4 顾衡、沈逾、秦峥、罗景明、唐黎条目。不能从旧正文 M1—M6 操作推出她拥有项目启动决策权。 |
| DX-G03 | R-07 无当前视听、身体、移动及现实行动能力；文字是外界接口，过去感官仅能作为受限记忆片段。 | G7 四章硬约束表；A3 `/world/environments/2`、`/world/environments/10`，以及 `/characters/core_characters/0`。每项角色知识追到实际输入。 |
| DX-G04 | 记忆只提供主观线索；情报须经专家、硬件与授权复核，由现实团队阻断袭击。 | G7 第一、四章；A3 `/world/environments/8/must_hold`、`/world/environments/8/must_not_imply`；A4“跨国威胁处置”。不得把自述“可验证”当作已验证。 |
| DX-G05 | 沈逾与 R-07 的新关系独立于顾衡旧记忆；程予安与周岚有各自主体性、同意与保护边界。 | G7 第一章第二小节；A3 `/characters/supporting_characters/1`（周岚）；A4 程予安、周岚条目。不能把婚姻变成所有权或把无辜亲属变为袭击参与者。 |
| DX-G06 | 行动层与原因层分离，救人与亲属保护同时成立；国家合作不等于全面共享或恢复互信。 | G7 第三、四章；A4 原因层保护单元、两国安全联络通道、叶惟正、阿列克谢、赵澄。查信息持有人、接收者、时点及权限。 |
| DX-G07 | 公共危机先得到现实阻断；R-07 选择结束，沈逾执行最终告别，当前实例关停且无活动备份。 | G7 第一、三、四章；A3 `/world/environments/7/must_hold`；A4 第七、八推进阶段及唐黎、苏望舒。选择和执行不能合并成自行关闭。 |
| DX-G08 | 告别前不直示决定性终止意图，后果不能被无损复活保证或伦理旁白消除；法律身份、未来重载与长期互信仍开放。 | A3 `/decision_controls/4/must_hold`；G7 第三、四章；A4“开放边界”。旧叙述契约的 C5 和旧 K9 等编号必须先映射，禁止直接画等号。 |
| DX-G09 | 从已批准构思经正式开发基线到 HLD／LLD，保持来源与授权；高层设计能被下游消费且不替下游预写正文。 | G1—G6；G7 第二、五、六章。HLD 的结构、人物弧、信息、时空、节奏、关键场景功能须与构思相容。 |

A4 所说八个推进阶段、十条故事线、17 名角色、43 个主要事件属于呈现中的规模信息，不是幕数、章数或篇幅配额；G7 明确最终章数、字数、读者定位不能据此冻结。市场建议、现实科学可行性研究、续作补写与最终手稿质量评奖都不在本轮范围。

### 1.4 已知状态与证据限度

定义阶段已通读 G1—G7、目录与批准说明、A4 和冻结 ISSUE 原文；已解析 A1—A3，核对本节及第二节所引 Pointer，回读六条内容 ISSUE 的关键双侧原文。这里不声称完成第三节的 127 文件全量语义审视，也不把解析 JSON 或计算哈希记为全文阅读。

本地重算得到 A1 SHA-256 `4f5a070d22a92fb211b9e99709e04e05b16460aa52ae40c7ebb0eaf49249e2bd`、A2 SHA-256 `4eabd4af2b249493f3aae1a2668c4de9b37dea7f61628e1b454293e49587d127`、A5 SHA-256 `80cfc4d82d77683324808ba3f96817914c24fd1de007fae70641789dedf65e36`，分别与 A2 作者决定引用、A0 完成记录说明、A1 HTML 引用一致。仅证明这些留存字节的相应绑定，不证明全部生产状态、P1 或 validator 已复验。

G7 第二、五、六章及 ISSUE #7 已说明本树未留存三个精确 basename：`novel-conception-package.json`、`development-handoff.json`、`hld-completion.json`。对此只能写“本冻结 Git 树证据不足以复验”，不能写“从未生产”“作者批准无效”或“外部受控渠道不存在”。旧 HLD 的 `pending_hld_human_review` 不等于当前 V2 HLD 的进度。

## 第二节：ISSUE 去重

### 2.1 冻结集合与处置含义

输入为 `.kunora/inputs/open-issues-snapshot-20261114b.md`，SHA-256 必须为 `f6cc9ddf44be3ee199c7993e0a37bc56813cb6be8b5e238da35a9f6ffeeffd90`。全文 13 条，快照时均 open、无评论；定义阶段只读 API 列表亦返回 #1—#13 open。线上状态只作发布防重补充，不改变 BASE 与冻结原文。

“仍成立”仅指该冻结树中保留了既有问题的限定事实／适配义务，不是判定现实今天仍未修复，不是 R3 已完成独立审视。“不在本轮范围”只排除新开展工程审计和修复，不否定既有发现。“已过时”须有同命题替代或关闭证据；不能只因材料较旧或上轮总验收 FAIL 就如此标记。本定义没有足够证据把任何一条列为已过时。

### 2.2 13 条逐条处置与交叉引用

第二步报告必须保留 DEDUP-01—13，逐条回读快照正文及所用源证据；不得以“工程七条略”或“六条均重复”代替。

| 记录 | ISSUE／命题 | 处置 | 理由、内容边界与报告交叉引用方式 |
| --- | --- | --- | --- |
| DEDUP-01 | [#1](https://github.com/innuama-coder/ai-novels/issues/1)：CLI 七路径与三测试入口 | 不在本轮范围 | 快照指向 `duanxian/conception-production/run.py:14,41–47,54–133` 及三测试。属于装载／布局，不是故事因果。报告“代码取证限制”交叉引用 #1；不启动 CLI 证明全链失败、不再提交路径问题。 |
| DEDUP-02 | [#2](https://github.com/innuama-coder/ai-novels/issues/2)：81／82 技能计数 | 不在本轮范围 | 根 README 和 `engine/README.md` 的库存说明不决定《断线》构思是否成立。报告“排除项”引用 #2；不重新开展技能清点，不与小说覆盖率混算。 |
| DEDUP-03 | [#3](https://github.com/innuama-coder/ai-novels/issues/3)：17 份素材来源路径及 R07 小节映射 | 不在本轮范围 | 工程追溯命题已有明确 17 项及风格指称边界。阅读素材时可按快照映射回实际 LLD，报告“来源解析”引用 #3；真正的内容矛盾另判，不能把路径修复等同于 #12 的披露一致性。 |
| DEDUP-04 | [#4](https://github.com/innuama-coder/ai-novels/issues/4)：Git 属性未匹配 engine 路径 | 不在本轮范围 | `.gitattributes` 字节策略风险已有覆盖，不证明实际 hash 损坏。报告“证据字节口径”引用 #4；以 BASE blob 保证本次引用，不调整属性或重做跨平台实验。 |
| DEDUP-05 | [#5](https://github.com/innuama-coder/ai-novels/issues/5)：历史 HLD 追踪门 open | 不在本轮范围 | `duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/artifacts/12-hld-integrity-report.md:25,32–34,57` 与 final package 是历史门证据。报告“阶段状态”引用 #5，保留其语义自述通过、形式追踪失败、人审待定三者区别；不重跑工程 validator，不重开同门问题。 |
| DEDUP-06 | [#6](https://github.com/innuama-coder/ai-novels/issues/6)：旧 HLD 人审 v2／v3 标签混用 | 不在本轮范围 | 同 integrity `:8,11,33` 与旧 manifest 涉及评审版本指称；不证明实际审错版本。报告“版本账”引用 #6；与 #5 门闭合及 #8 周岚内容均不可相互替代。 |
| DEDUP-07 | [#7](https://github.com/innuama-coder/ai-novels/issues/7)：机器交付本体未留存的取证请求 | 不在本轮范围 | A0、A1、A2、G7 已把运行链留存政策与批准区别开。报告“证据不足”引用 #7；不生成第二条缺包请求，不要求本体入 Git，不假定渠道缺位。 |
| DEDUP-08 | [#8](https://github.com/innuama-coder/ai-novels/issues/8)：周岚维护例外参与链 | 仍成立（冻结适配问题） | A3 `/characters/supporting_characters/1/must_not_imply` 禁止以保护暗示参与袭击；旧 `duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/canonical-world-facts-v3.0.md:38–44,59–60,67–73` 与 `artifacts/04-character-system.md:20,34` 保留主动例外参与。报告 DX-G05／历史适配行引用 #8；不再开“周岚责任”同族条目，不扩大成恋人或全知共谋。 |
| DEDUP-09 | [#9](https://github.com/innuama-coder/ai-novels/issues/9)：旧 PRD 当前视听 | 仍成立（冻结适配问题） | A3 `/world/environments/2`、`/world/environments/10` 对照 `duanxian/design/runs/prd/2026-07-07-duanxian-prd-workflow/artifacts/03-trunk-scenes.md:23,30` 的初醒光声／听见沉默。报告 DX-G03 引用 #9；新找到同能力越界段只补报告证据，不按场景另开。过去感官记忆不能仅凭视觉词判违例。 |
| DEDUP-10 | [#10](https://github.com/innuama-coder/ai-novels/issues/10)：自行关停及提前披露 | 仍成立（冻结适配问题） | A3 `/world/environments/7/must_hold`、`/decision_controls/4/must_hold` 对照六月 K9、R07 素材、数字空间素材及旧正文 `:331–460`。七月 PRD `artifacts/05-information-flow.md:26–28` 由研究员执行，但提前披露。报告 DX-G07／08 引用 #10；不得将两个版本混称“全都自行关闭”，不再把 F-010 拆出新条。 |
| DEDUP-11 | [#11](https://github.com/innuama-coder/ai-novels/issues/11)：十秒沉默缺文字来源 | 仍成立（冻结适配问题） | A3 `/world/environments/10` 对照 `duanxian/novel-text/2026-06-07-duanxian-novel.md:284–341`；会议室十秒进入 R-07 推断但上下文未建立输入。报告 DX-G03／04 信息链行引用 #11；描述来源缺口，不捏造麦克风或读心事实。 |
| DEDUP-12 | [#12](https://github.com/innuama-coder/ai-novels/issues/12)：郑柏舟显名与旧素材不一致 | 仍成立（旧链内部及适配问题） | `duanxian/writing/characters/2026-06-07-writer-betrayer.md:15,40,76–102`、`2026-06-07-writer-zhengbozhou.md:211,260` 限制披露，旧正文 `:193–199,365–369,464–466` 显名。R07 素材 `:90,325,338` 和 LLD betrayer `:28–29` 是必须并列的不同旧方案。报告“版本内知识设计”引用 #12；不将旧禁令升级为当前作者决定，不因当前人物表没有此名就删除角色。 |
| DEDUP-13 | [#13](https://github.com/innuama-coder/ai-novels/issues/13)：完整记忆／像素重建 | 仍成立（冻结适配问题） | A3 `/world/environments/8` 对照 `duanxian/design/specs/2026-06-06-digital-life-novel-design.md:12,25–26` 和旧正文 `:95,187–199,343,363–369`。报告 DX-G04 引用 #13；“这是回忆”不能洗去数据库化，未演出核验也不能外推伪造结果。姓名是否公开仍归 #12。 |

表中 `artifacts/...` 等短称只在同格已给出的 run 目录内解析；实施报告证据账必须展开成完整路径。六条内容 ISSUE 的“仍成立”不能替代实施者的上下文复核和反证记录。

保留上轮采纳边界：快照记载 R1、R2 的整体验收仍有 FAIL；Owner 采纳的是限定工作基础及交叉确认事实。既不能声称上轮整份报告 PASS，也不能据总 FAIL 推翻所有逐项已确认事实。R3 自建证据，不把未取得的历史报告引用当成本轮已阅读材料。

### 2.3 新 ISSUE 的准入与粒度

每个候选依次通过五门，任一未过不得发布：①明确属于 DX-G01—09 的构思／设计命题；②应然与实然均有 BASE 原文证据，写明版本、上下文及反证；③与 13 条逐一语义比较，并与发布前实时全状态 ISSUE 比较；④有单一可说明的修订目标、责任阶段和独立验收条件；⑤建议只提出后续设计改进方向，不在本轮改故事或补写正文。

同命题判断用“受约束对象＋违反的控制＋因果／信息机制＋关闭条件”，不看标题是否相同。已覆盖发现标 `existing:#N`，记录更多证据只进入报告。证据增加、严重度变化、从设计换到素材或另一场景，不自动成为新命题。一个发现同时落入数条时记录主 ISSUE 与交叉 ISSUE，不能把交集再开一条。确有不可由既有关闭条件覆盖的独立差异时，先写差异对照和单独修复／验收理由，才可列新候选。

同一根因须同步修订多个载体的，合并为一条；两个问题可分别修复、分别验收的，拆分。例如 #10 的终局执行／意图披露需一个场景方案统筹，#11 的信息输入、#12 的身份披露、#13 的记忆能力则各有不同关闭条件。不把“全部旧稿不一致”做成大杂烩，也不按每行、每文件、每感官词拆碎。允许最终新 ISSUE 数为零；禁止设定发现数量指标。

## 第三节：升级工作六要素

### 3.1 目标

给出 BASE 内《断线》构思与设计对 DX-G01—09 的一致性、实现程度及证据限度；发现实际不一致时只通过 GitHub ISSUE 形成可处理的外部审视结果。报告、阅读账和去重账是工作分支上的过程证据，不替代 ISSUE，也不替代作者批准。第一步只交付本定义书；第二、三步必须另行启动。

### 3.2 工作方法与阅读范围

采用“权威认定→全量内容阅读→目标与对象映射→跨版本适配／同版一致性→反证挑战→去重→发布→独立验收”的顺序。冻结树文件清单通过 `git ls-tree -r -z --name-only BASE` 取得；读取用 `git show BASE:<path>` 或先证明工作文件字节与 BASE blob 一致。工作分支后续提交不能改变源证据 SHA。

内容必读集 R：BASE 中 `duanxian/` 的全部非工程目录文件，精确排除 `duanxian/conception-production/` 与 `duanxian/testing/`，共 **127** 个。组成是项目根四文件、批准包六文件、设计 99 文件、写作素材 17 文件、旧正文一文件。设计 99 件含 specs 36、runs 49、workflow-docs 11、design-tasks 2、reference 1。数字用于本树集合核对，不代表创作质量或下次版本的配额。

全读范围包括看起来重复的旧版、blocked manifest、HTML、JSON、样片、设计参考及 `design-scenes-draft.md`。阅读 writing／novel-text 只用于验证设计承接、信息因果及版本冲突；不做语言润色、全书文学评价、续写或发表审查。参考稿只核对其所声明的创作边界，不访问其中外部科学／方法论文献。

必须逐文件登记 `path、BASE blob OID、SHA-256、字节数、读取区间或 JSON Pointer、版本身份、内容摘要、关联目标、支持／反例、未覆盖部分`。大文件按连续块读取，工具截断必须补读，不能把一次 cat、字节哈希或关键词扫描当全读。A3 是单行约 2.84 MB JSON，应解析后按顶层域和数组对象分块列出原值及 Pointer，保留每个叶节点的阅读覆盖；不能只抽 must_hold 就宣布全文完成。HTML 同时核对可见文本与结构／嵌入数据，不能只读标题或以 Markdown 替代。相同文本可记录复用理解，但仍需逐文件／逐 Pointer 核对版本与语境，不能合并删除覆盖记录。达到上下文上限时保存已读区间和下一起点，继续后续批次，不降低全读门。

基准必读集 N：第一节 G1—G7 七份全文，外加根 README；G7 已包含在 R，去重后 **R∪N=134** 件。A0—A5、项目 README 已在 R。`.kunora/spec.yaml`、`.kunora/PROMPT.md`、本定义书和 ISSUE 快照是另外的任务输入，必须全文读，但不计入 BASE 134 件。

工程候选集 E 共 **21** 件，见下面列表。对 21 件建立路径和用途索引；只对影响《断线》故事事实、权威来源、版本及交接的代码展开阅读，不运行生产器或测试。优先从 `duanxian/conception-production/run.py` 的阶段输入／输出和 `duanxian/testing/` 中 story builder 的故事数据、报告投影、字段绑定查起。若发现生成逻辑影响一个内容结论，读取完整相关函数、常量及其调用／导入依赖闭包，记录为何纳入、读到哪里、哪些结论不能据此成立。工程工具通用算法、打包、适配器、greeting-cli、发布 zip 和无关任务夹具不做全仓审查。若需要追到 engine，先记录目标 ID 与触发证据，再读取具体 runtime／schema／validator；不得因目录名 novel-* 就扩成所有技能审计。静态源码只证明写法，测试文件只证明测试意图，不声称测试已执行或生产结果已通过。

#### 3.2.1 内容必读集 R 的精确清单（127 件）

以下每行一件，禁止用目录抽样替代。

```text
duanxian/README.md
duanxian/conception-approved/README.md
duanxian/conception-approved/author-decision.json
duanxian/conception-approved/conception-completion.json
duanxian/conception-approved/human-review-report.html
duanxian/conception-approved/human-review-report.json
duanxian/conception-approved/human-review-report.md
duanxian/design-scenes-draft.md
duanxian/design/design-tasks/2026-07-07-duanxian-hld-design-planning/design-task-package.md
duanxian/design/design-tasks/2026-07-07-duanxian-hld-design-planning/manifest.md
duanxian/design/reference/2026-06-07-style-reference-liu-cixin.md
duanxian/design/runs/hld/2026-07-10-duanxian-hld-workflow/gate-report.md
duanxian/design/runs/hld/2026-07-10-duanxian-hld-workflow/manifest.md
duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/HLD-断线设计稿.md
duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/artifacts/01-world-entity-inventory.md
duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/artifacts/02-prd-support-matrix.md
duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/artifacts/03-world-rules.md
duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/artifacts/04-character-system.md
duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/artifacts/05-environment-system.md
duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/artifacts/06-event-system.md
duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/artifacts/07-time-information-system.md
duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/artifacts/08-thread-system.md
duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/artifacts/09-style-pov-system.md
duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/artifacts/10-inventory-reconciliation.md
duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/artifacts/11-hld-integrator.md
duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/artifacts/12-hld-integrity-report.md
duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/artifacts/final-hld-package.md
duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/canonical-world-facts-v2.0.md
duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/canonical-world-facts-v3.0.md
duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/gate-report.md
duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/manifest.md
duanxian/design/runs/lld/2026-07-08-duanxian-lld-workflow-blocked/manifest.md
duanxian/design/runs/prd/2026-07-06-duanxian-prd-workflow-blocked/manifest.md
duanxian/design/runs/prd/2026-07-07-duanxian-prd-workflow/artifacts/00-proposal-risk-report-human-confirmed.md
duanxian/design/runs/prd/2026-07-07-duanxian-prd-workflow/artifacts/01-part-scope.md
duanxian/design/runs/prd/2026-07-07-duanxian-prd-workflow/artifacts/02-part-goal.md
duanxian/design/runs/prd/2026-07-07-duanxian-prd-workflow/artifacts/03-trunk-scenes.md
duanxian/design/runs/prd/2026-07-07-duanxian-prd-workflow/artifacts/04-conflict-value.md
duanxian/design/runs/prd/2026-07-07-duanxian-prd-workflow/artifacts/05-information-flow.md
duanxian/design/runs/prd/2026-07-07-duanxian-prd-workflow/artifacts/06-freeze-boundaries.md
duanxian/design/runs/prd/2026-07-07-duanxian-prd-workflow/artifacts/07-hld-expansion-requirements.md
duanxian/design/runs/prd/2026-07-07-duanxian-prd-workflow/artifacts/08-prd-integrator.md
duanxian/design/runs/prd/2026-07-07-duanxian-prd-workflow/artifacts/09-prd-risk-report.md
duanxian/design/runs/prd/2026-07-07-duanxian-prd-workflow/artifacts/final-prd-package.md
duanxian/design/runs/prd/2026-07-07-duanxian-prd-workflow/manifest.md
duanxian/design/runs/proposal/2026-07-05-duanxian-proposal-workflow/artifacts/01-intake-boundary-ledger.md
duanxian/design/runs/proposal/2026-07-05-duanxian-proposal-workflow/artifacts/02-reader-promise-pre-story.md
duanxian/design/runs/proposal/2026-07-05-duanxian-proposal-workflow/artifacts/03-core-concept-pre-story.md
duanxian/design/runs/proposal/2026-07-05-duanxian-proposal-workflow/artifacts/04-storyline-design.md
duanxian/design/runs/proposal/2026-07-05-duanxian-proposal-workflow/artifacts/05-storyline-quality-report.md
duanxian/design/runs/proposal/2026-07-05-duanxian-proposal-workflow/artifacts/06-reader-promise-final.md
duanxian/design/runs/proposal/2026-07-05-duanxian-proposal-workflow/artifacts/07-core-concept-final.md
duanxian/design/runs/proposal/2026-07-05-duanxian-proposal-workflow/artifacts/08-final-promise-concept-consistency.md
duanxian/design/runs/proposal/2026-07-05-duanxian-proposal-workflow/artifacts/09-macro-structure.md
duanxian/design/runs/proposal/2026-07-05-duanxian-proposal-workflow/artifacts/10-core-character-frame.md
duanxian/design/runs/proposal/2026-07-05-duanxian-proposal-workflow/artifacts/11-world-premise.md
duanxian/design/runs/proposal/2026-07-05-duanxian-proposal-workflow/artifacts/12-ending-direction.md
duanxian/design/runs/proposal/2026-07-05-duanxian-proposal-workflow/artifacts/13-proposal-integrator.md
duanxian/design/runs/proposal/2026-07-05-duanxian-proposal-workflow/artifacts/14-proposal-risk-checker.md
duanxian/design/runs/proposal/2026-07-05-duanxian-proposal-workflow/manifest.md
duanxian/design/specs/2026-06-06-digital-life-novel-design.md
duanxian/design/specs/2026-06-06-first-meeting-digital-life-novel.md
duanxian/design/specs/2026-06-06-hld-digital-life-novel.md
duanxian/design/specs/2026-06-06-lld-digital-life-novel.md
duanxian/design/specs/2026-06-06-prd-digital-life-novel.md
duanxian/design/specs/2026-06-06-reference-survey.md
duanxian/design/specs/2026-06-06-science-background-digital-life-novel.md
duanxian/design/specs/2026-06-06-technical-systems-digital-life-novel.md
duanxian/design/specs/2026-07-05-duanxian-intake.md
duanxian/design/specs/2026-07-05-duanxian-proposal.md
duanxian/design/specs/lld/characters/2026-06-07-character-betrayer.md
duanxian/design/specs/lld/characters/2026-06-07-character-colleagues.md
duanxian/design/specs/lld/characters/2026-06-07-character-it.md
duanxian/design/specs/lld/characters/2026-06-07-character-jiling.md
duanxian/design/specs/lld/characters/2026-06-07-character-qianxu.md
duanxian/design/specs/lld/characters/2026-06-07-character-shenyu.md
duanxian/design/specs/lld/characters/2026-06-07-character-zhengbozhou.md
duanxian/design/specs/lld/scenes/2026-06-07-scene-K1.md
duanxian/design/specs/lld/scenes/2026-06-07-scene-K10.md
duanxian/design/specs/lld/scenes/2026-06-07-scene-K2.md
duanxian/design/specs/lld/scenes/2026-06-07-scene-K3.md
duanxian/design/specs/lld/scenes/2026-06-07-scene-K4.md
duanxian/design/specs/lld/scenes/2026-06-07-scene-K5.md
duanxian/design/specs/lld/scenes/2026-06-07-scene-K6.md
duanxian/design/specs/lld/scenes/2026-06-07-scene-K7.md
duanxian/design/specs/lld/scenes/2026-06-07-scene-K8.md
duanxian/design/specs/lld/scenes/2026-06-07-scene-K9.md
duanxian/design/specs/lld/spaces/2026-06-07-space-apartment.md
duanxian/design/specs/lld/spaces/2026-06-07-space-city.md
duanxian/design/specs/lld/spaces/2026-06-07-space-corridor.md
duanxian/design/specs/lld/spaces/2026-06-07-space-digital-realm.md
duanxian/design/specs/lld/spaces/2026-06-07-space-hotel-room.md
duanxian/design/specs/lld/spaces/2026-06-07-space-meeting-room.md
duanxian/design/specs/lld/spaces/2026-06-07-space-operation-room.md
duanxian/design/specs/lld/spaces/2026-06-07-space-security-hall.md
duanxian/design/specs/lld/spaces/2026-06-07-space-server-room.md
duanxian/design/workflow-docs/duanxian-causal-storyline.md
duanxian/design/workflow-docs/duanxian-conception-review.md
duanxian/design/workflow-docs/duanxian-core-character-design.md
duanxian/design/workflow-docs/duanxian-coverage-matrix.md
duanxian/design/workflow-docs/duanxian-development-map.md
duanxian/design/workflow-docs/duanxian-intent-card.md
duanxian/design/workflow-docs/duanxian-interview-review-brief.html
duanxian/design/workflow-docs/duanxian-map-check.md
duanxian/design/workflow-docs/duanxian-narrative-contract.md
duanxian/design/workflow-docs/duanxian-novel-design-brief.md
duanxian/design/workflow-docs/duanxian-subject-definition.md
duanxian/novel-goals.md
duanxian/novel-text/2026-06-07-duanxian-novel.md
duanxian/project-display-metadata.json
duanxian/writing/characters/2026-06-07-writer-R07.md
duanxian/writing/characters/2026-06-07-writer-betrayer.md
duanxian/writing/characters/2026-06-07-writer-colleagues.md
duanxian/writing/characters/2026-06-07-writer-jiling.md
duanxian/writing/characters/2026-06-07-writer-qianxu.md
duanxian/writing/characters/2026-06-07-writer-shenyu.md
duanxian/writing/characters/2026-06-07-writer-zhengbozhou.md
duanxian/writing/scenes/2026-06-07-scene-K1.md
duanxian/writing/spaces/2026-06-07-writer-apartment.md
duanxian/writing/spaces/2026-06-07-writer-city.md
duanxian/writing/spaces/2026-06-07-writer-corridor.md
duanxian/writing/spaces/2026-06-07-writer-digital-realm.md
duanxian/writing/spaces/2026-06-07-writer-hotel-room.md
duanxian/writing/spaces/2026-06-07-writer-meeting-room.md
duanxian/writing/spaces/2026-06-07-writer-operation-room.md
duanxian/writing/spaces/2026-06-07-writer-security-hall.md
duanxian/writing/spaces/2026-06-07-writer-server-room.md
```

#### 3.2.2 工程候选集 E 的精确清单（21 件，按需展开）

```text
duanxian/conception-production/run.py
duanxian/conception-production/tests/test_attempt_selection_cli.py
duanxian/conception-production/tests/test_line_sequence_review_cli.py
duanxian/conception-production/tests/test_topology_review_cli.py
duanxian/testing/build_run08_hi1_000230.py
duanxian/testing/build_run08_hi1_000237.py
duanxian/testing/build_run08_hi1_000238.py
duanxian/testing/duanxian_c1_builder.py
duanxian/testing/duanxian_e1_builder.py
duanxian/testing/duanxian_h1_assemble.py
duanxian/testing/duanxian_h1_fragments.py
duanxian/testing/duanxian_h1_html.py
duanxian/testing/duanxian_h1_plan.py
duanxian/testing/duanxian_q1_handoff.py
duanxian/testing/duanxian_q1_semantic.py
duanxian/testing/duanxian_t1_builder.py
duanxian/testing/duanxian_w1_model.py
duanxian/testing/generate_duanxian_editorial_review.py
duanxian/testing/run_duanxian_conception_v2.py
duanxian/testing/test_c1_determinism.py
duanxian/testing/test_duanxian_title_provenance.py
```

### 3.3 边界

可做：只读检索冻结树、解析文档／JSON／HTML、计算哈希、对照引用、获取 GitHub 公开仓库及 API 的只读资料；第二步在通过发布门后提交未覆盖的新构思／设计 ISSUE；在各自工作分支新增过程交付物。

不可做：修改／删除任何既有仓库文件，改作者决定或生产状态，重生成构思／HLD／LLD，补写小说，运行可能写盘的业务 CLI／validator／pytest，创建 PR，推 main 或其他作业分支，评估《断线》之外项目，评论／关闭既有 ISSUE。本定义阶段不创建任何 ISSUE。外部网络仅限 `github.com` 与 `api.github.com`；重定向到其他域名停止，不访问旧文档引用的其他站点。

### 3.4 约束

每个事实结论必须能回读 BASE 的具体段落／行或 JSON Pointer。报告区分“原文事实、规范要求、历史自述、推断、待证”；不得把文件名含 final／approved 或自评 pass 当独立验收。历史控制与当前批准冲突时明确适用层，不静默改来源。开放项、缺失的当前机器包、正常待开发内容不得冒充缺陷。凭据只能由预置路径在进程内读取，不回显、不写入正文、日志、URL、git remote、临时凭据文件或命令参数；禁止 set -x、HTTP debug 和异常对象全量输出。

### 3.5 交付物

| 阶段 | 新增交付路径与内容 | 交付责任 |
| --- | --- | --- |
| 定义 | `outputs/duanxian-audit3/def-001-definition.md` | 本作业只提交此文件，包含本七节；机械与内容自检不冒充 Owner／第三步验收。 |
| 实施首轮 | `outputs/duanxian-audit3/impl-001-review.md` | 冻结范围、权威与目标、一致性矩阵、实现程度、逐条去重、新发现与限制、发布结果、偏离与待决。主体中文至少 10000 UTF-8 字节；字数仅防空壳，内容完整优先。 |
| 实施证据 | `outputs/duanxian-audit3/impl-001-evidence.json` | 全读／代码按需账、版本账、目标—对象—证据映射、反证、13 条去重、候选及发布前检查、失败／续作记录。 |
| 实施 ISSUE 记录 | `outputs/duanxian-audit3/impl-001-issues.json` | 既有引用、候选去重结果、未发布原因、实际 issue number／URL、正文 SHA-256、发布及回读状态；零新 ISSUE 也必须有空集合及理由。 |
| 独立验收 | `outputs/duanxian-audit3/acc-001-acceptance.md` | 第六节逐项 PASS／FAIL／证据缺失、反例、总体 verdict、修正指令。 |

上述后三类是给未来作业的输出定义，不授权本定义作业创建它们。返工全部新增 `impl-001-r2-*`、`impl-001-r3-*` 或 `acc-001-r2-acceptance.md` 等带轮次文件；旧报告保持不变，前后版本在新文件中交叉引用。各作业只向自己获派的 remote-agent 分支提交，不借用定义分支覆盖交付。

### 3.6 验收标准与方法

定义书：UTF-8、至少 8000 字节、七节齐全、七项 Owner 原文逐字保留、路径真实、13 条各有处置及理由、六要素与工作步骤可执行、验收双线完整、无秘密。只新增允许路径并以指定署名提交推送。

实施：134 件必读集合精确闭合，21 件工程候选均有纳入／不展开说明；所有 DX-G 目标有对象、证据、状态及限制；任何缺读、截断未补或无据全称判断均 FAIL。13 条逐条去重及发布前增量去重完成。新 ISSUE 每条均过五门，并与报告／记录一一对应。没有新发现不构成 FAIL，未完成读取却声称无问题构成 FAIL。

验收：由独立第三步重新核证；报告质量与 ISSUE 质量都通过才总体 PASS。发现内容问题多少不决定审视作业 PASS；如实证明存在问题并合规登记，同样可 PASS。作业验收 PASS 不等于《断线》全部设计或小说生产 PASS。

## 第四节：总体方案与路线图

### 4.1 两条判断轴与证据矩阵

每个目标／对象记录两个独立字段：

| 判断轴 | 枚举 | 使用规则 |
| --- | --- | --- |
| 一致性 | 一致／部分一致／明确冲突／无法判定／不适用 | 一致须覆盖该对象完整义务并有反证挑战；部分一致逐子项列支持与缺口；明确冲突须双侧原文；无法判定写缺什么；不适用须边界理由。 |
| 实现程度 | 规范已定义／历史实现／当前批准呈现可证／当前机器链已复验／未完成／证据不足 | 先注明所属层级再给状态，可为同一目标列多对象行。仅有构思批准不能标 HLD／LLD 完成；本轮不运行生产 validator，因此不得无证写“机器链已复验”。 |

矩阵最低字段：`goal_id、object_id、version_class、baseline_source、actual_source、support、counterevidence、consistency、implementation_level、limitation、existing_issue、candidate_id`。每项“实现程度”只评价构思／设计承接，旧正文仅作反查样本。不得以 17 人表／10 线计数直接计算全书百分比，也不得用均分抵消硬约束冲突。汇总可统计各枚举行数，但必须给分母和对象粒度，不能混把规范条数、文件数与事件数相加。

版本账固定分四层：①批准构思留存包；②2026-07 访谈／过程控制；③2026-07 旧 proposal、PRD、HLD 运行链；④2026-06 早期 SPEC、LLD、素材、正文。每个文件按内容核实，不能只由目录推断其“当前”。跨层使用必须解释映射；没有明确同一性时保留“未建立映射”。例如 C5、K9、PRD-S15 和当前第八推进阶段不能按编号相似自动等同。

每项候选至少执行一次反证挑战：是否旧版本已隔离、是否只是待开发、是否在别段有来源、是否把回忆当当前感官、是否把技术执行当决策授权、是否把选择终止当关停权限、是否与既有 ISSUE 同命题。新发现若依赖“全文件没有 X”，必须给完整搜索范围和全文语义核对，不能用关键词零命中代替。

### 4.2 执行路线图与三步门

| 门 | 责任与输入 | 产出及退出条件 |
| --- | --- | --- |
| D 定义 | GPT-6-Astra／High，冻结作业材料 | 本定义书，机械／内容自检、指定分支提交推送；Owner 与编排验收通过后交第二步。模型名是冻结派工要求，不授权自行启动其他执行器。 |
| I0 准入 | 实施 Agent（GLM-5.3 或 Kimi-K3.1-Pro），定义提交 SHA、BASE、快照 | 版本与权限核对通过；不擅自 cherry-pick 更改故事源。 |
| I1 阅读与证据 | 134 件必读集合＋按需工程闭包 | 覆盖账闭合，目标矩阵有据，13 项去重完成。 |
| I2 发布前复核 | 全部候选、反证与实时 ISSUE 集合 | 每条新候选满足五门；未通过只保留为待证，不发布。 |
| I3 登记与交付 | 已通过候选 | 逐条 API 创建并 GET 回读，报告／记录一致，工作分支只新增过程文件。 |
| A 独立验收 | GPT-6-Astra／High，定义 SHA、实施 SHA、BASE、快照、实际 ISSUE | 第六节全项判定；PASS 才可结束阶段，FAIL 给可执行修正指令回 I1／I2／I3。 |

本审视 LOOP 预算由本定义规定为首轮实施＋最多两轮修正，各轮均重新独立验收；不把 G5 的小说生产返工预算误当自动授予本任务。第三轮仍 FAIL 时交 Owner 完整缺口及续作指令，保持未通过状态，不降标、不跳验收、不伪造 DONE。Owner 扩展预算后续跑；尚可独立推进的阅读／取证继续完成。网络无响应的只读重试和恢复相同已发 ISSUE 不计语义返工轮。

### 4.3 风险与控制

| 风险 | 触发证据／表现 | 处理 |
| --- | --- | --- |
| 权威倒置 | 旧 v3 自称“生效”，新目录明确旧链 | 限定旧 run 内生效；按 G0、A1 与 G3／G4 分层。 |
| 范围蔓延 | CLI、属性或技能库存问题吸引工程修复 | 交叉引用 #1—#7，停止工程缺陷扩写；只保留影响内容判断的限制。 |
| 全读名实不符 | 大 JSON／HTML 截断、只读目录或运行 grep | 阅读分块及覆盖并集，未完不发布完成信号。 |
| 缺包被误报 | 找不到 P1 或最新状态 | 记证据不足与 #7，不倒造本体，不撤销批准。 |
| 历史状态污染 | 将旧 pending 当新版失败 | 每行带 run／版本／层级，保留历史自述限定。 |
| 复述旧问题 | 新场景落入已有关闭条件 | 归 existing:#N；零新发现也可完成审视。 |
| 并发发布重复 | 列表读取后出现新 ISSUE，POST 超时 | 发布前再次分页去重；用稳定标记和正文回读恢复，不盲目重发。 |
| 无权纠错 | 发布后验收发现误报 | 停止后续发布，记录 FAIL；不得绕过禁评／禁关闭边界，向 Owner 提交具体纠错备选。 |
| 秘密／越域 | 带凭据 URL、调试输出或外部引用跳转 | 进程内认证、固定主机、脱敏日志；失败只记状态码与稳定错误类。 |

## 第五节：实施作业工作指令（实施指令）

实施作业必须严格遵守本节指令与第一至四节口径，不得遗漏和随意调整；偏离须在交付物中单独说明理由。

该声明不授权先偏离后补理由。涉及冻结点、范围、作者事实、发布权限或验收标准的偏离必须先停止受影响步骤并列 Owner 决策点。以下每步均有输入、动作、预期产出和自检点；不得跨步以模板化报告代替实际阅读。

### S01 接收与冻结

- 输入：派发的实施 job_ref／work_branch、已验收定义提交 SHA、BASE、快照及作业宪法。
- 动作：全文读输入；按启动要求先确认和写本次 ACK；记录 `git status --porcelain`、当前分支、HEAD；确认定义书确实来自给定提交。用 `git cat-file -e BASE^{commit}` 验证冻结对象存在；若实施分支包含定义提交，HEAD 可以不是 BASE，但小说源必须按 BASE 读取且未改。
- 预期产出：证据文件中 `input_binding`，包含 job_ref、definition_commit、base_commit、snapshot_sha256、work_branch、初始状态及允许新增路径。
- 自检：快照 hash 精确匹配；不是 main；无未归属变更；凭据只检查路径／可读性／权限，不打印内容。缺必需输入则记录阻塞，不能自行选分支或更换 BASE。

### S02 建清单与版本账

- 输入：BASE、第三节清单及第一节基准表。
- 动作：枚举 BASE 跟踪路径，重算 R、N、E；R∪N 应为 134，E 为 21。建立逐文件账及四层版本分类，记录旧路径→现路径的解析规则；任务输入另记。
- 预期产出：`read_ledger` 初始集合、`version_ledger`、`engineering_selection`。
- 自检：集合相等而非数量相同；每件初始状态为未读；不得把 .kunora 的注入文件算进冻结树，不继承旧 1444 全仓阅读硬门。

### S03 通读目标与批准证据

- 输入：G1—G7、A0—A5、根与项目 README。
- 动作：全文读基准；核对作者批准、完成记录、HTML 三项绑定；逐目标展开 DX-G01—09 的细则和开放项；A3 按 Pointer 分块读取，区分内容、控制、样片和追溯，不把派生报告当 P1 本体。
- 预期产出：`goal_register`、当前权威表、证据可得性表、基准文件全读记录。
- 自检：表中每个强制／开放判断有源；引用值一致仅写局部绑定；未实际重跑不得宣称 validator PASS。

### S04 全读历史构思与设计

- 输入：设计 99 件、根设计草稿及已确认目标。
- 动作：按 workflow-docs→specs→proposal→PRD→两轮 HLD→blocked LLD／任务包／参考的顺序逐件全读。读取每件的标题、版本、状态、正文、表格和附录；blocked／废弃文件仍登记其范围和限制。把人物、世界、事件、信息、终局、结构与交接逐项映射到目标。
- 预期产出：读账、对象索引、版本内一致性与向当前适配矩阵。
- 自检：不以 confirmed／pass 标记替代内容核对；同名异版不合并；当前没有编号映射时登记缺证，不直接判故事错误。

### S05 全读承接材料并按需追代码

- 输入：17 份 writing、旧正文、剩余 R 文件与 21 件代码索引。
- 动作：全读承接材料，追踪设计决定在素材／正文中的表达及相反规则。每个工程候选记录相关性；影响小说内容的，读完整相关定义与依赖并指明影响路径；仅通用运行缺陷的引用已知 ISSUE，不重演生产。
- 预期产出：R∪N 全读闭合、`code_evidence`、跨载体证据链和明确排除项。
- 自检：旧正文只是设计反查，不扩大为写作改进；测试源码不被写成运行结果；大文件每块都可证明阅读，没有截断未补。

### S06 判断一致性与实现程度

- 输入：全读记录、目标／版本／对象索引。
- 动作：按第四节两轴逐行判断；每个冲突形成应然—实然—影响—反证—限度；对每个一致结论也作反证挑战。区分已存在不一致、历史适配负债、正常待开发、开放选择和证据不足。
- 预期产出：完整矩阵和稳定候选 `DX3-F001` 起的本轮编号；编号一旦引用不重新排序复用。
- 自检：没有“全部”“从未”“一定”等超出取证集合的判断；没有无证补角色、科学结论、读者画像、章节与总字数。

### S07 逐条去重与组织候选

- 输入：冻结 13 条全文、本轮候选、S06 证据。
- 动作：逐项填 DEDUP-01—13，复核第二节处置；每候选对照全部 13 条，记录同命题／部分交集／不同命题及理由。落实粒度规则，明确修订责任阶段和关闭条件。
- 预期产出：`dedup_ledger` 与 `candidate_ledger`；每项最终为 existing、new_candidate、out_of_scope、insufficient_evidence 或 no_issue_needed。
- 自检：所有旧 ISSUE 均有记录；无仅换标题的重复；没有把“已过时”当关闭授权。若认为第二节某个事实不成立，先保存双侧反证供独立复核，不直接改冻结定义。

### S08 写报告与发布前审查

- 输入：读账、矩阵、去重账、候选正文。
- 动作：先完成报告草稿及每条候选正文；检查全文覆盖、源定位、秘密、范围和粒度。再按 5.1 API 规程分页读取 `state=all`，排除 PR，取得当前 issue body 及必要评论，补充实时去重。对全部新候选逐条完成五门 checklist，全部可证后才进入 S09。
- 预期产出：至少包含“范围与版本／目标基准／阅读证据／一致性矩阵／实现程度／13 条去重／新发现／限制与待决／发布账／偏离”的中文报告，以及正文已定稿的候选。
- 自检：本轮审视尚未独立验收；不得在报告自写第三步 PASS。未通过发布门的候选仍保留但标注未发布及原因；缺读阻断发布。

### S09 按 API 规程逐条登记并回读

- 输入：通过全部发布门的新候选、作业预置凭据路径。
- 动作：每条提交前再检查最新完整 ISSUE 列表与本地已发记录；无重复后创建一次；成功则立即 GET 回读并记录编号、URL、正文 hash。网络结果不确定时先查稳定标记，不自动重发。
- 预期产出：实际 ISSUE 和完整 `impl-001-issues.json`；零新条目时 `created=[]` 并记录“全部已覆盖／无未覆盖确证发现”等具体理由。
- 自检：仅新建已批准范围内 ISSUE；没有评论、关闭或编辑已有 ISSUE；API 返回与预定正文相同；未成功项不能记 created。

### S10 提交、推送和交接

- 输入：最终报告、证据账、ISSUE 记录与自检结果。
- 动作：核对源树未变；显式 `git add -- <三个新文件>`，用 `git diff --cached --name-status` 确认全部为本作业新文件；按派发指定署名和分支提交，只推本分支。GET 回读实际 ISSUE，核对本地提交与远端分支一致。
- 预期产出：路径×提交号、检查摘要、ISSUE URL 清单、限制和验收入口。
- 自检：不得 git add .、force push、修改 main、改历史证据。远端核验失败则如实记录未完成，不输出完成哨兵。成功交付使用最后单独一行 `DXUAU3IMPL-DONE-<tip7>`；该信号只表示实施待独立验收，不表示阶段已 PASS。定义阶段仍使用 `DXUAU3DEF-DONE-<tip7>`；独立验收 PASS 才可使用 `DXUAU3ACC-PASS-<tip7>`。

### 5.1 GitHub ISSUE API 提交规程（仅供第二步执行）

固定仓库 `innuama-coder/ai-novels`。定义阶段已通过公开 GET 核对列表，并从 [GitHub 官方 OpenAPI](https://github.com/github/rest-api-description/blob/main/descriptions/api.github.com/api.github.com.json) 核实：列表与单条读取为 GET，创建为 POST，创建成功响应为 201，正文请求至少含 title。本规程只发送 title、body，不借机设置指派、标签、里程碑或其他外部状态。

```text
GET  https://api.github.com/repos/innuama-coder/ai-novels/issues?state=all&per_page=100&page=1
GET  https://api.github.com/repos/innuama-coder/ai-novels/issues/{number}
POST https://api.github.com/repos/innuama-coder/ai-novels/issues
请求 JSON：{"title":"[断线 R3审视] <单一问题>","body":"<完整已审正文>"}
```

读取需处理分页，沿 Link 的 next 或递增页码至完；只允许固定 api.github.com 主机，拒绝跨域重定向。列表中的 `pull_request` 项排除。不能只读取第一页、只比标题或只查 open；closed ISSUE 若已覆盖同命题亦不能直接重开，先记录状态差异。冻结快照继续原样保留，实时集合单独记录获取时间、分页完成情况和参与去重的 number／body hash。

认证：请求头 `Accept: application/vnd.github+json`、明确 User-Agent；写入时由程序从该实施作业预置的只读凭据文件读取秘密到内存，再置 `Authorization: Bearer <内存值>`。本定义作业的推送凭据路径不自动成为下一作业凭据路径。请求体 UTF-8 JSON 编码，不把含多行正文的 JSON 拼进 shell，不把秘密写入提交记录；请求日志只保留 method、固定 endpoint、状态码和脱敏结果。不得将秘密放 URL 或自动追随到其他主机。

创建按候选顺序串行；仅 201 算成功，记录 number、html_url、title、body 和 created_at，立即 GET 单条重算正文 SHA-256。GET 结果必须与提交正文逐字一致。401／403／404／410／422 等失败记录状态与脱敏原因，停止该候选发布；限流按服务端指示恢复，不循环撞库。POST 超时、断连或 5xx 表示结果可能不确定：先列取全状态 ISSUE 查稳定标记及正文，找到一条精确匹配则恢复编号；零条也须等待读取状态明确并复核后才能有界重试，同候选最多一次安全重试；发现多条或持续不确定则停止并交人工处理，不制造更多重复。

稳定标记固定为 `<!-- duanxian-audit3-impl-001:DX3-F001:base=92573f1cca40f37cee04d2beb8708ff33ba603d6 -->`，后续候选只替换 F 编号；修正轮不得变更标记以绕过去重。实际 job_ref 不同时在 S01 记录相应固定前缀。该标记只防重复提交，仍需正文语义去重。

每条正文必须包含：

1. 标记、BASE、发现 ID、责任阶段和严重度（high／medium／low，加影响理由；不沿用分值替代论证）。
2. 问题是什么：一个明确可证伪命题、对象版本及影响；历史稿写明“直接沿用需适配”，不要伪称当前批准版已错误。
3. 应然与实然证据：完整路径、BASE 行号／JSON Pointer、最短必要原文、上下文及反证限制；证据可用 GitHub `blob/<BASE>/<path>#L<line>` 回读。
4. 与 13 条及实时 ISSUE 的差异：最接近的条目 URL、共享部分和既有关闭条件为何无法覆盖本条；禁止只写“已去重”。
5. 解决建议和关闭条件：指出后续责任层、需保持的控制及可逐项验证的结果，不直接创作新剧情。
6. 采纳边界：不撤销已批准构思、不裁决开放问题、不修改原文，不把静态观察说成运行测试；修复需要后续授权。

`impl-001-issues.json` 至少含 `schema_version、job_ref、base_commit、definition_commit、snapshot_sha256、existing_references、candidates、created、failures`。每候选含 `finding_id、dedup_disposition、closest_existing、difference_reason、publish_gate、marker、body_sha256、publish_status`；已发记录另含 `number、url、created_at、get_verified、retrieved_body_sha256`。零发现时仍保留13项 existing_references 和空 created。记录中不存认证头或凭据。

### 5.2 中断与恢复

每完成一组阅读或一个发布事务即把已完成范围、待读起点、候选状态和远端编号写入本轮新建证据账。不能修改旧轮次证据；恢复先核对 BASE、定义 SHA、快照 hash 和已发标记，再从未完成步骤继续。中断交付 `@@CONTINUE-<组号>@@` 及明确下一动作，不输出 DONE。内存不足、网络失败或模型轮次耗尽不能变成自动 PASS。

## 第六节：独立验收作业检查单（验收检查单）

第三步由独立任务执行，不能由实施者在同一上下文改称“验收者”。读取给定定义／实施提交、BASE、冻结快照和线上 ISSUE；不使用实施者未提交的聊天记忆补足证据。独立验收可消费报告，但每个强结论必须重新回读源文。验收自身不创建、评论、关闭 ISSUE，不修改小说及历史交付物。

### 6.1 报告质量线

| 检查 ID | 必验项与方法 | PASS 标准／FAIL 条件 |
| --- | --- | --- |
| R01 | 核对定义提交、BASE、快照 hash、分支及 diff | 输入绑定准确；仅本轮允许的新文件。源文件改变或基线混用直接 FAIL。 |
| R02 | 重算 R∪N、E 集合并核对全读账 | 134 件集合精确、全部区间／Pointer 覆盖；21 件代码都有选择理由；无哈希冒充阅读。缺项、截断、假称全读即 FAIL。 |
| R03 | 全文读实施报告，检查九项目标、权威表和版本账 | 作业宪法、项目总则、小说目标、历史 SPEC 与批准证据分层成立；不虚构根宪法。 |
| R04 | 逐行核对一致性／实现程度矩阵 | 每目标有证据和限度；不以规范已冻结推实际完成，不以历史 pending 推当前失败。 |
| R05 | 重核 A1、A2、A5 的已有绑定与缺包说明 | 局部绑定与全链可用性严格区分；批准范围不被扩大／撤销。 |
| R06 | 对全部冲突、全部新候选及所有“无／全部”判断回读完整相关源 | 应然、实然、上下文、反证和影响闭合；没有把未决或未完成当缺陷。 |
| R07 | 复核全部13条去重及六内容 ISSUE 的双侧证据 | 已覆盖项只交叉引用；工程项没有被再次审计发布；历史验收状态表述忠实。 |
| R08 | 对非发现行作反证抽查 | 九目标各至少一项，批准内容、旧 SPEC、workflow-docs、proposal／PRD、HLD、LLD、writing、正文每类至少一件；覆盖重叠可共用。记录选样理由及具体原文，不能只看结论。 |
| R09 | 发现抽查失真后的扩查 | 任一类出现遗漏／误读，扩至该类全部相关文件与目标行；仍不能核实即 FAIL，不以样本率掩盖。独立验收抽查不降低实施全读义务。 |
| R10 | 检查范围、建议及可恢复性 | 未写新故事、未运行生产、未越域；建议有后续授权边界，待证项和偏离有明确状态。 |
| R11 | 检查交付完整与措辞 | 报告非模板空壳，三个实施文件一致，可由新执行者复现；PASS 是审视质量，不是小说批准。 |

### 6.2 ISSUE 质量线

| 检查 ID | 必验项与方法 | PASS 标准／FAIL 条件 |
| --- | --- | --- |
| I01 | GET 回读所有本轮新 ISSUE，逐字比对 body hash | number／URL／标记／BASE／正文与记录一致；禁止凭 POST 退出码单独宣布成功。 |
| I02 | 检查每条完整问题、应然实然、建议和严重度 | 证据路径可回读，严重度有影响依据，关闭条件可独立执行；单纯措辞偏好不可立项。 |
| I03 | 再与13条及当前全状态 ISSUE 语义对照 | 不重复同命题，不把追加证据拆成新条；部分交集有不可替代的差异及独立关闭条件。 |
| I04 | 评估粒度 | 同根因跨载体归并，独立机制可分开；没有“旧稿总整改”或“一行一个 ISSUE”。 |
| I05 | 双向检查报告↔候选↔实际 ISSUE | 已发都有报告证据；报告声称已发的都真实存在；未发布项有理由。 |
| I06 | 检查权限与公开内容 | 没有秘密、个人凭据、外部运行包泄漏；没有擅自评论／关闭旧 ISSUE或设置无关外部状态。 |
| I07 | 零新增或发布失败路径 | 零新增须全读闭合且每发现合法归类；发布未完成只能如实报告，不能以候选正文冒充线上结果。 |
| I08 | 不确定 POST 的恢复 | 有标记查重／GET 证据，没有盲目重发；多条重复或不确定结果未解即 FAIL。 |

### 6.3 总体判定与 FAIL 修正指令

每行输出 PASS／FAIL／证据缺失及证据定位；硬项“证据缺失”按未通过处理。两条质量线全部通过，且 Owner 无未处理的重大边界异议，才能总体 PASS。不得以大多数条目通过、已有 ISSUE 数量足够或机械关键词通过抵消失败。

FAIL 修正单逐条采用 `ACC-Fnnn`：写违反本定义哪一条、实施对象与原文、独立反例、正确边界、要求动作、预期产物、复验方法、影响范围及回到 S 几。按输入／阅读→语义→去重→发布记录→交付的依赖排序。不得用“全面提高质量”替代具体动作，不在修正单里直接改写小说。

允许的修正仅是补读、修正本轮报告／证据的新增版本、重新归类候选、补足未完成的合法新 ISSUE 发布及收据。若已发布内容误报、重复或需改正文，而冻结权限仅允许新建，则记录具体外部对象和纠错备选，提交 Owner 待授权；不能悄悄编辑、评论、关闭，也不能再开一条“纠错 ISSUE”制造噪音。该分支保持 FAIL，预算耗尽同样不结束阶段。复验须检查修正项及受影响下游，再保留未受影响项的来源，不抹除原 FAIL 历史。

### 6.4 本定义书自身的交付检查

定义作业执行 `.kunora/spec.yaml` 中冻结的机械检查命令；另核验七个一级业务节、七项 Owner 口径逐字包含、13 条处置及链接、134／21 集合和所有明确路径。以 `git diff --name-status BASE HEAD` 证明只有定义书新增，以远端分支 SHA 证明推送结果。辅助自检不是第三步独立验收，也不是 Owner 手工批准；二者状态须如实留待后续。

## 第七节：Owner 决策点

本定义的读取、判断、去重、报告与默认发布规程可以执行，没有必须先改变小说事实或扩大权限才能完成的前置决定。以下是条件性决策点，未触发时遵循默认值，不反复请求确认；触发后仅停止受影响动作，其余只读工作继续。

| 决策点 | 备选 | 推荐／默认 | 影响及状态 |
| --- | --- | --- | --- |
| O1 既有 ISSUE 追加确认／关闭 | 保持只交叉引用；或另行授权对明确条目操作 | 保持现有禁评／禁关闭边界 | 不影响本轮去重与完成；若要改变需列具体条目、动作与理由，待 Owner 批准。 |
| O2 缺失机器链的受控取证 | 仅按冻结树报告证据不足；或另派受控取证任务 | 本轮引用 #7 并保留限度 | 不宣称新机器链复验；引入新来源须另冻结范围与版本，待 Owner 批准。 |
| O3 已发新 ISSUE 的纠错 | 暂停并记录 FAIL；或授权指定正文修改／关闭及复验 | 暂停受影响发布并给具体纠错稿 | 本轮不自行获得外部编辑权；只有误报等事实触发，待 Owner 批准。 |
| O4 三轮后仍未通过 | 增加定向修正预算；或暂停并重订任务输入 | 先交完整修正单，按未通过保留 | 不降低验收标准、不输出阶段完成；新增预算或范围变更待 Owner 批准。 |

定义提交不代表上述条件授权已经取得。第二步严格按本定义执行，第三步按独立证据作最终验收；本作业不预填任何后续 PASS。
