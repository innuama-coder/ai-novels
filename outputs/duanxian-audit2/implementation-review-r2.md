# 《断线》构思、设计与正文实现一致性审视报告 R2

## 一、审视摘要与范围

本报告固定小说内容基线 BASE=`92573f1cca40f37cee04d2beb8708ff33ba603d6`，定义书 DEF=`11d01717448960487e072870b07873cf69dc4a8d`，本轮开工 HEAD（IMPL_START）=`f56f9fbcdba7229b0e7ba6fee9fb55988ecf1c88`。定义书文本 SHA-256 实测为 `ce034561ee6e2ed97295d6640349a916576c0a1e12584873e9657d89e87d0237`。审视对象是 BASE 中目标、批准包、96 份设计文件、17 份写作素材和唯一连续正文，共 121 个文件；另读三份导览和三份设计辅助材料。所有小说事实均取自 BASE，未用定义书代替故事证据。本轮按独立验收 C01—C07 修订引文、权限推断、记忆约束、统计、追溯及数量口径。

【当前权威口径】批准范围是 `conception`，并非正文或正式 HLD/LLD 的批准。目标与批准包在主体、新感情、感知与记忆限制、责任分立、危机闭环、终局和开放边界上总体同向，17 人和 12 个环境均可逐条定位。控制声明写“十个环境”而可见环境为十二项，写“六个样章片段”而可见片段为 FRAG-DX-01—03；数字不吻合是事实，但其统计范围和内容是否缺失仍待裁决。完整 P1 本体未留存，故 43 个主要事件及十线的全部细节不能由摘要逆推。

【历史/旧链口径】现有设计不是一套与当前批准版同版的完成品。七月 workflow-docs 对双前置、权限、核验和披露有较强承载；旧 PRD/HLD 对危机链有具体展开；六月 specs 与写作素材主要服务“活性转移—内部背叛—自我终结”旧故事。它们能提供局部材料，却也带来当前感官、完整记忆数据库化、亲属参与、终止执行、人物身份和开放项的冲突，不能凭旧 `pass`、`ready`、`covered` 认定为当前落实。

【未完成项】连续正文只写序幕、她·1—6、它·1—3，覆盖转移、异常访问、隐瞒、审查和终止，未写当前版沈逾接受职责、分层情报、专家/硬件/授权核验、现实阻断、两国余波及静态保管。正文还让 R-07 直接展示“选择：终止”并关闭自身感知场，和当前“告别前不展示决定、不能自行终止、沈逾执行”三项约束均不合。正文另把记忆写成完整、可寻址、可重采样的数据体，触及“不得写成可检索录像或客观数据库”的独立禁令。素材与正文重复内容只计一次，不把三段批准样片当作连续手稿。

【推断】三层结论应分开：构思层是“主体成立、呈现数字有差异、细节受缺失本体和统计范围限制”；设计层是“历史承载丰富但需系统适配”；实现层是“局部旧稿可复用，当前目标仍处早期”。M1—M6 仅证明沈逾执行技术激活，不能单独证明她拥有项目启动决策权；正文真正成立的权限冲突是 R-07 自行关闭。本报告不撤销作者批准，不替作者决定法律身份、重载、续作、读者画像、章数或全书字数，也不把小说缺口换算成整体完成百分比。工程基础设施候选仅作“移交工程线，不入本报告结论”的分流声明，不进入发现、统计或建议。

## 二、基线、权威与目标义务

目标全文六章被拆成 16 条工作义务：原感知义务进一步分为当前接口、记忆可用范围和现实验证三项，避免用“视觉属于过去”掩盖记忆数据库化。G-ID 和 F-ID 仅为本报告索引，不冒充批准包正式 ID。硬约束的反例是明确相反命题；未写到不判“不一致”，缺中间材料不强行判一致。流程要求只用于区分阶段与责任，不拿规范存在证明作品达标。

| G-ID | 目标义务与定位 | 支持证据 / 反例 | 类型与标签 |
|---|---|---|---|
| G-001 | 顾衡已死；R-07 继承记忆却是新主体，以自身选择负责（`duanxian/novel-goals.md` 第一章、第四章） | 新决定归顾衡即反例 | 硬约束；【当前权威口径】 |
| G-002 | 启动、接受职责、交互、核验、行动、关停、保管责任分立（同文件第一、四章） | 沈逾独自作项目启动决定或 R-07 输出自生权限即反例；单纯技术操作不等于决策证明 | 硬约束；【当前权威口径】 |
| G-003 | 沈逾曾单向暗恋；R-07 的新感情来自启动后交流（同文件第一章） | 预装爱情、旧爱复活即反例 | 硬约束；【当前权威口径】 |
| G-004 | 程予安在世，周岚为儿时守护者；亲属有同意边界（同文件第一、四章） | 妻子死亡、周岚恋人化或参与袭击、婚姻产生所有权即反例 | 硬约束；【当前权威口径】 |
| G-005A | 当前仅文字接口，无视听、身体、移动及现实行动（同文件第四章；批准 JSON `/world/environments/2`、`/10`） | 实时感官、读心、控网、未输入而知情即反例 | 硬约束；【当前权威口径】 |
| G-005B | 过去记忆只能作受限主观片段，不得成为可检索录像或客观数据库（同文件第四章；批准 JSON `/world/environments/8/must_hold`、`/must_not_imply`） | 完整记忆、全节点可寻址、像素重建、无损回放即反例 | 硬约束；【当前权威口径】 |
| G-005C | 记忆只提供线索，必须与现实证据交叉核验，人物知识须有可追溯通道（同文件第四章；批准 JSON `/world/environments/8/must_hold`） | 把记忆直接当事实、无输入却获得外部信息、以自述核验代替实际核验即反例 | 硬约束；【当前权威口径】 |
| G-006 | 顾衡入口与受命汇流；人质/专家/硬件/授权独立核验，团队阻断（同文件第一、四章） | 一句情报直接关闭袭击即反例 | 硬约束；【当前权威口径】 |
| G-007 | 行动层救人、原因层保护；终止决定告别前不直接展示（同文件第四章；批准 JSON `/decision_controls/4`） | 提前展示决定、未发送内容被接收者知道即反例 | 硬约束与叙述目标；【当前权威口径】 |
| G-008 | 袭击完全避免；沈逾执行当前实例关停；无活动备份（同文件第三、四章） | R-07 自行执行、活动副本或任务成功抵销伦理责任即反例 | 硬约束；【当前权威口径】 |
| G-009 | 重载、法律身份、长期互信保持未决，未来加载需重新许可（同文件第三、四章） | 已证实复活、自动互信、续作内容被冻结即反例 | 作者开放项；【当前权威口径】 |
| G-010 | 双前置汇入唯一主体；八推进、十线、17 人、43 事件是规模而非章数（同文件第五章） | 支撑线取代 R-07、数字被转成固定章数即反例 | 结构目标；【当前权威口径】 |
| G-011 | 17 人各有功能、关系和权限，不能按职位相似强行映射（同文件第四章；批准 MD 人物节） | 工具化任一核心或亲属、角色权限全知即反例 | 硬约束与质量目标；【当前权威口径】 |
| G-012 | 环境分别承担准入、记忆、核验、监督、关停和保管功能（同文件第四章；批准 MD 十二处） | 空间自动完成行动、封存变活动备份即反例 | 硬约束与设计目标；【当前权威口径】 |
| G-013 | MD/JSON/HTML 的人物、环境、样片与规模呈现保持同义（同文件第二章“内容权威与呈现分离”） | 数字差可证；统计对象和内容范围未澄清时只能列疑点 | 呈现一致性；【当前权威口径】【推断】 |
| G-014 | 设计有功能、选择、变化、依赖、信息边界；正文以行动后果承载主题；未知读者和篇幅不补定（同文件第一、五、六章） | 模板声明代替功能、篇幅代替质量、擅自补作者开放项即反例 | 质量目标与【流程规范】 |

五种口径在矩阵中组合使用：当前事实标【当前权威口径】；旧设计和旧正文标【历史/旧链口径】；缺对应或未完成标【未完成项】；阶段责任标【流程规范】；审视者的适配解释标【推断】，其反证条件随发现给出。E0—E3/EU 只评价具体义务在特定层的可核对程度，不是质量分或阶段放行。

## 三、对象覆盖与版本关系

121 个对象均已全文读取并登记 blob、角色、目标和证据定位，第九节集合差为零。分布为：目标 1、批准 6、specs 36、workflow-docs 11、runs 49、writing 17、连续正文 1。另读 `README.md`、`duanxian/README.md`、`engine/docs/ai-novel-workflow/README.md` 三份导览，以及 design-tasks 两份和 style-reference 一份辅助材料。批准 JSON 的 4602 条 drilldown/reduction 追溯记录经程序化遍历去重，业务字段、must_hold、must_not_imply、人物、环境、事件、控制和样片均完整核对；HTML 含折叠正文亦全部读取。

【流程规范】版本顺序只用于判断材料身份：六月 specs/writing 属早期设计；七月 proposal→PRD→HLD 属另一历史链；七月 21 日 workflow-docs 再经访谈修订；八月批准包才是当前构思权威。旧 K1—K10 不等于 M01—M10，也不等于当前章节；C1—C9 是因果功能，PRD-S00—S18 是另一套主干场景，不能混号。旧 HLD v3.0 虽自称唯一事实源，其效力仅限该历史包，且 v2.0 已被其标为废弃。

【未完成项】批准包 README、作者决定和 completion 证明批准及留存绑定，但完整 `novel-conception-package.json`、正式开发 handoff 和 43 事件本体不在 BASE。HTML 的“当前尚未作出决定”是供审阅页面的事前状态，作者决定文件才记录后续批准，两者不构成故事事实冲突。批准 MD 的概括不能替代机器本体，本报告因此对事件级细节保留证据限度。

## 四、构思层一致性

下表逐条核对目标与批准包。设计/实现栏用于跨层追溯，构思层结论不以历史材料反证批准事实；遇当前基准内部疑点保留双侧定位。

| G-ID｜层次 | 目标路径+定位 | 批准路径+定位 | 设计路径+定位 | 实现路径+定位 | 材料版本/身份 | 五种口径标签 | 一致性 | 程度 | 证据限度 | 关联发现 |
|---|---|---|---|---|---|---|---|---|---|---|
| G-001｜构思 | `duanxian/novel-goals.md` §一.1、§四.1 | `duanxian/conception-approved/human-review-report.md` “记忆怎样变成选择”、顾衡；`duanxian/conception-approved/human-review-report.json` `/decision_controls/0` | `duanxian/design/workflow-docs/duanxian-subject-definition.md` §0 | `duanxian/novel-text/2026-06-07-duanxian-novel.md` 它·2、它·3 | 当前批准／历史材料／草稿 | 【当前权威口径】 | 一致 | E3 | MD/JSON/HTML 同义；新主体不等于人格哲学全答 | — |
| G-002｜构思 | `duanxian/novel-goals.md` §一.1、§四.1 | `duanxian/conception-approved/human-review-report.md` “秘密基地准入套间”“R-07核心实验室”；`duanxian/conception-approved/human-review-report.json` `/world/systems/1/must_hold` | `duanxian/design/workflow-docs/duanxian-causal-storyline.md` C1—C2 | `duanxian/conception-approved/human-review-report.md` “门合上以后” | 当前批准；样片非连续稿 | 【当前权威口径】 | 一致 | E3 | 启动、接受、执行、核验和保管均可定位 | — |
| G-003｜构思 | `duanxian/novel-goals.md` §一.2 | `duanxian/conception-approved/human-review-report.md` 沈逾、R-07、关系变化网；`duanxian/conception-approved/human-review-report.json` `/characters/relationship_networks/0/must_not_imply` | `duanxian/design/workflow-docs/duanxian-core-character-design.md` §0、§3 | `duanxian/conception-approved/human-review-report.md` “只有文字的清晨” | 当前批准 | 【当前权威口径】 | 一致 | E3 | 顾衡未爱与新感情来源明确分开 | — |
| G-004｜构思 | `duanxian/novel-goals.md` §一.2、§四.1 | `duanxian/conception-approved/human-review-report.md` 周岚、程予安；`duanxian/conception-approved/human-review-report.json` `/characters/supporting_characters/1/must_not_imply`、`/characters/supporting_characters/2/must_not_imply` | `duanxian/design/workflow-docs/duanxian-interview-review-brief.html` “不可混淆的关系锚点” | `duanxian/design/workflow-docs/duanxian-core-character-design.md` R-07—周岚 | 当前批准／历史对照 | 【当前权威口径】 | 一致 | E3 | 两位亲属均在世且主体边界完整 | — |
| G-005A｜构思 | `duanxian/novel-goals.md` §四.1 | `duanxian/conception-approved/human-review-report.md` R-07 隔离套间；`duanxian/conception-approved/human-review-report.json` `/world/environments/2/must_not_imply`、`/world/environments/10/must_not_imply` | `duanxian/design/workflow-docs/duanxian-narrative-contract.md` §0、§4 | `duanxian/conception-approved/human-review-report.md` “只有文字的清晨” | 当前批准 | 【当前权威口径】 | 一致 | E3 | 当前仅文字，过去感官不等于当前感知 | — |
| G-005B｜构思 | `duanxian/novel-goals.md` §四.1 | `duanxian/conception-approved/human-review-report.md` 记忆重构沙箱；`duanxian/conception-approved/human-review-report.json` `/world/environments/8/must_hold`、`/world/environments/8/must_not_imply` | `duanxian/design/workflow-docs/duanxian-narrative-contract.md` §4“记忆、回忆与历史信息” | `duanxian/conception-approved/human-review-report.md` “只有文字的清晨” | 当前批准 | 【当前权威口径】 | 一致 | E3 | 片段主观、可中断，禁止录像化和数据库化 | F-011 |
| G-005C｜构思 | `duanxian/novel-goals.md` §四.1 | `duanxian/conception-approved/human-review-report.md` 记忆重构沙箱、现实硬件控制室；`duanxian/conception-approved/human-review-report.json` `/world/environments/8/must_hold` | `duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/canonical-world-facts-v3.0.md` §3—4 | `duanxian/conception-approved/human-review-report.md` “雨停以前” | 当前批准／历史对照 | 【当前权威口径】 | 一致 | E3 | 记忆与外部证据相互印证，现实团队完成闭环 | — |
| G-006｜构思 | `duanxian/novel-goals.md` §一.1、§四.1 | `duanxian/conception-approved/human-review-report.md` “跨国威胁处置”“故事的八次推进”；`duanxian/conception-approved/human-review-report.json` `/world/event_conditions/1` | `duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/canonical-world-facts-v3.0.md` §3—4 | `duanxian/conception-approved/human-review-report.md` “雨停以前” | 当前批准／历史对照 | 【当前权威口径】 | 一致 | E3 | 人质、专家、硬件、授权和物理阻断形成闭环 | — |
| G-007｜构思 | `duanxian/novel-goals.md` §四.2 | `duanxian/conception-approved/human-review-report.md` 第六阶段；`duanxian/conception-approved/human-review-report.json` `/decision_controls/4`、`/storylines/connections/1/must_hold` | `duanxian/design/workflow-docs/duanxian-narrative-contract.md` N1—N6 | `duanxian/conception-approved/human-review-report.md` “只有文字的清晨” | 当前批准／历史对照 | 【当前权威口径】 | 一致 | E3 | 行动/原因层、读者知识、事实和误解分开 | — |
| G-008｜构思 | `duanxian/novel-goals.md` §三.1、§四.1 | `duanxian/conception-approved/human-review-report.md` 第八阶段、唐黎、苏望舒；`duanxian/conception-approved/human-review-report.json` `/world/environments/7/must_hold`、`/world/event_conditions/4/must_hold` | `duanxian/design/workflow-docs/duanxian-development-map.md` M09—M10 | `duanxian/conception-approved/human-review-report.md` “只有文字的清晨” | 当前批准／历史对照 | 【当前权威口径】 | 一致 | E3 | 选择与执行分立，封存不是活动备份 | — |
| G-009｜构思 | `duanxian/novel-goals.md` §三.1、§四.1 | `duanxian/conception-approved/human-review-report.md` “开放边界”、沈逾、苏望舒；`duanxian/conception-approved/human-review-report.json` `/world/boundaries` | `duanxian/design/workflow-docs/duanxian-causal-storyline.md` §6 | `duanxian/conception-approved/human-review-report.md` “只有文字的清晨” | 当前批准／历史对照 | 【当前权威口径】 | 一致 | E3 | 开放的是重载、法律身份和互信，不是 R-07 是否新主体 | — |
| G-010｜构思 | `duanxian/novel-goals.md` §五.2 | `duanxian/conception-approved/human-review-report.md` “故事的八次推进”“十线架构”“三层延伸与职责覆盖”；`duanxian/conception-approved/human-review-report.json` `/visual_models/3` | `duanxian/design/workflow-docs/duanxian-development-map.md` M01—M10 | `duanxian/conception-approved/human-review-report.md` 三个试读场景 | 当前批准；P1 未留存 | 【当前权威口径】【未完成项】 | 部分一致 | E2 | 八阶段、七泳道和 13 个时间节点可见，十线及 43 事件全集不可由摘要重建 | — |
| G-011｜构思 | `duanxian/novel-goals.md` §四.1、§五.2 | `duanxian/conception-approved/human-review-report.md` 17 人条目；`duanxian/conception-approved/human-review-report.json` `/characters/core_characters`、`/characters/supporting_characters` | `duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/artifacts/04-character-system.md` 全表 | `duanxian/conception-approved/human-review-report.md` 三个试读场景 | 当前批准 | 【当前权威口径】 | 一致 | E3 | 17 人姓名、功能、关系、限制均可定位；事件分配不全 | — |
| G-012｜构思 | `duanxian/novel-goals.md` §四.1 | `duanxian/conception-approved/human-review-report.md` “故事发生的十二个地方”；`duanxian/conception-approved/human-review-report.json` `/world/environments` | `duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/artifacts/05-environment-system.md` 全表 | `duanxian/conception-approved/human-review-report.md` 三个试读场景 | 当前批准 | 【当前权威口径】 | 一致 | E3 | 十二项定义及责任完整；控制声明数量差异另列 G-013 | F-001 |
| G-013｜构思 | `duanxian/novel-goals.md` §二.3 | `duanxian/conception-approved/human-review-report.json` `/decision_controls/1/statement`、`/decision_controls/7/statement` 对比 `/world/environments`、`/fragments`；`duanxian/conception-approved/human-review-report.md` 十二处、三样片；`duanxian/conception-approved/human-review-report.html` 对应元素 | `duanxian/conception-approved/README.md` 留存范围说明 | `duanxian/conception-approved/human-review-report.md` 三个试读场景 | 当前批准内部呈现疑点 | 【当前权威口径】【未完成项】【推断】 | 证据不足 | EU | 数字不吻合已证实；统计对象、隐藏本体和内容缺失无法判定，不把其升级为明确反命题 | F-001 |
| G-014｜构思 | `duanxian/novel-goals.md` §一.3、§五.3、§六 | `duanxian/conception-approved/human-review-report.md` 三样片及开放边界；`duanxian/conception-approved/human-review-report.json` `/decision_controls/7/must_hold` | `duanxian/design/workflow-docs/duanxian-development-map.md` 功能单元 | `duanxian/conception-approved/human-review-report.md` 三个试读场景 | 当前批准／流程规范 | 【当前权威口径】【流程规范】 | 部分一致 | E2 | 样片验证局部声音与选择；最终读者、章数、全书字数仍未决 | — |

17 人逐项核对结果如下，姓名与功能均来自批准 MD“人物想要什么，又害怕什么”及对应 JSON Pointer。除 R-07 与沈逾为双核心外，其余 15 人均有不可替代职责，没有把旧郑柏舟、纪菱、陆远等按职位相似直接改名的依据。

| 人物 | 当前批准功能与边界 | 历史对应的适配判断【推断】 |
|---|---|---|
| R-07 | 新生命；自主减害、交付、请求结束；无现实行动和自行终止 | 旧“它”可保留文字受限与自我形成，终止执行须重设 |
| 沈逾 | 接受职责、访谈、伦理质询、最终关停；非启动者 | 旧技术员可保留专业/情感盲区，须补受命与多人权限 |
| 顾衡 | 已死情报员；记忆不占有新决定；未爱沈逾 | 陆远/灰鸟不能直接沿用；旧背叛线须换成危机入口 |
| 周岚 | 儿时守护者；非恋人、非袭击参与者，保有协查同意 | 旧维护例外和复杂依恋必须重设 |
| 程予安 | 在世妻子、医生；婚姻不转移所有权 | 旧“妻子/承诺”仅作弱素材，须补在世与同意功能 |
| 许曼青 | 导师和推荐责任人，不知项目全貌 | 六月纪菱/同事不能替代导师责任 |
| 秦峥 | 顾衡领导与行动授权，非全能决策者 | 郑柏舟的项目主管职位不能直接映射 |
| 梁策 | 接头人，闭合现实核验，非全知 | 旧接应组只有功能种子，须具体化 |
| 罗景明 | 项目负责人，受交叉授权与伦理记录约束 | 旧主管只能提供流程材料，权限须重设 |
| 唐黎 | 工程师，核验实例与硬件，移交静态材料 | 旧机柜/日志素材可复用，不能证明人格连续 |
| 贺闻钧 | 行动负责人，组织团队阻断 | 旧危机处置组须落到具体行动责任 |
| 伊利亚·萨温 | 袭击协调者，持续反制且不知 R-07 内部决定 | 旧裂隙网络可作功能参照，非一一映射 |
| 德米特里·沃尔科夫 | 被胁迫专家，提供有限证词 | 旧 M 国首席认证师可作主要历史来源，须保留有限性 |
| 叶惟正 | C 国代表，划定共享与国家责任 | 旧国家代表抽象，需明确授权边界 |
| 阿列克谢·奥尔洛夫 | M 国代表，坚持独立核验 | 旧 M 方犹疑可保留，须避免无条件信任或阻挠 |
| 赵澄 | 双边联络官，维持最低合作 | 旧 C/M 联络组只提供功能种子 |
| 苏望舒 | 未来静态保管人，不承诺复活 | 旧技术资料种子须改成不可执行记录与重新许可 |

十二处环境在 MD、JSON 和 HTML 中逐项同义：顾衡遗留证据接收链分离接触/撤离/读取；秘密基地准入套间保障知情选择；文字会话隔离室禁止未声明感官；联合情报指挥室保证团队行动；原因层保护单元限制反查；数字生命监督与责任室不提供伦理标准答案；C、M 两国安全联络通道保留独立核验；R-07 核心实验室禁止自行终止与远控；记忆重构沙箱禁止录像化；离线载荷保管库禁止复活承诺；R-07 隔离套间区分两侧感知；现实硬件控制室要求专家、硬件和授权共同复核。因此 G-012 的实质内容完整，G-013 仅处理控制声明与可见集合数量差异，二者不可合并成“环境缺失”的夸张结论。

## 五、设计层一致性

设计层评价分两步：先判断文件对当时上游的实现，再判断其对当前目标的适配。故“局部相容”不等于当前可直接采用，“冲突”也只指控明确相反命题。全部 96 个设计对象均有处置，状态型文件只证明历史身份；模板只有通用字段而无具体动作时，不给 E3。

| G-ID｜层次 | 目标路径+定位 | 批准路径+定位 | 设计路径+定位 | 实现路径+定位 | 材料版本/身份 | 五种口径标签 | 一致性 | 程度 | 证据限度 | 关联发现 |
|---|---|---|---|---|---|---|---|---|---|---|
| G-001｜设计 | `duanxian/novel-goals.md` §一.1 | `duanxian/conception-approved/human-review-report.md` 顾衡、R-07；`duanxian/conception-approved/human-review-report.json` `/decision_controls/0` | `duanxian/design/workflow-docs/duanxian-coverage-matrix.md` 信息义务矩阵；`duanxian/design/workflow-docs/duanxian-narrative-contract.md`:25、79、92 | `duanxian/design/workflow-docs/duanxian-development-map.md` M03—M05 | 历史设计 | 【历史/旧链口径】【推断】 | 部分一致 | E2 | N1 明写 C3 起为新主体，preserved-open 在读者状态列；人格哲学开放与人物事实不再混作确定冲突 | F-002 |
| G-002｜设计 | `duanxian/novel-goals.md` §一.1、§四.1 | `duanxian/conception-approved/human-review-report.md` 准入套间、核心实验室；`duanxian/conception-approved/human-review-report.json` `/world/systems/1` | `duanxian/design/workflow-docs/duanxian-causal-storyline.md` C1—C2；`duanxian/design/runs/prd/2026-07-07-duanxian-prd-workflow/artifacts/03-trunk-scenes.md` PRD-S04—S05 | `duanxian/design/workflow-docs/duanxian-development-map.md` M02、M09 | 历史设计 | 【历史/旧链口径】 | 部分一致 | E2 | 七月 C2 明确团队启动/沈逾受命；PRD 三方签字及旧六月单人操作仍须统一为当前多人责任 | — |
| G-003｜设计 | `duanxian/novel-goals.md` §一.2 | `duanxian/conception-approved/human-review-report.md` 沈逾、关系变化网；`duanxian/conception-approved/human-review-report.json` `/characters/core_characters/1/must_not_imply` | `duanxian/design/workflow-docs/duanxian-core-character-design.md` §0、§2—3 | `duanxian/design/runs/proposal/2026-07-05-duanxian-proposal-workflow/artifacts/04-storyline-design.md` 故事梗概 | 历史设计 | 【历史/旧链口径】 | 部分一致 | E2 | 七月已明确单向暗恋和新感情；旧 proposal 的旧情投射可保留，但“事后知被骗”须按当前知识差复核 | — |
| G-004｜设计 | `duanxian/novel-goals.md` §一.2、§四.1 | `duanxian/conception-approved/human-review-report.md` 周岚、程予安；`duanxian/conception-approved/human-review-report.json` `/characters/supporting_characters/1`、`/characters/supporting_characters/2` | `duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/canonical-world-facts-v3.0.md` §5；`duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/artifacts/04-character-system.md` HLD-04-04 | `duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/HLD-断线设计稿.md` §3 | 历史设计 | 【历史/旧链口径】【未完成项】【推断】 | 不一致 | E2 | 周岚主动写入维护例外并关联攻击，触及批准禁止；复杂依恋未直白恋爱化这一限度保留，程予安功能未建立当前对应 | F-003 |
| G-005A｜设计 | `duanxian/novel-goals.md` §四.1 | `duanxian/conception-approved/human-review-report.md` R-07 隔离套间；`duanxian/conception-approved/human-review-report.json` `/world/environments/2/must_not_imply` | `duanxian/design/runs/prd/2026-07-07-duanxian-prd-workflow/artifacts/03-trunk-scenes.md` PRD-S06、S13；对照 `duanxian/design/workflow-docs/duanxian-narrative-contract.md` §4 | `duanxian/design/runs/prd/2026-07-07-duanxian-prd-workflow/artifacts/final-prd-package.md` §6 | 历史设计 | 【历史/旧链口径】【推断】 | 不一致 | E2 | PRD 明写当前光线、声音感知和“听见沉默”；七月叙述契约虽可复用，旧稿相反能力不能静默保留 | F-004 |
| G-005B｜设计 | `duanxian/novel-goals.md` §四.1 | `duanxian/conception-approved/human-review-report.md` 记忆沙箱；`duanxian/conception-approved/human-review-report.json` `/world/environments/8/must_not_imply` | `duanxian/design/specs/2026-06-06-digital-life-novel-design.md` §二“完整意识结构化数据”；`duanxian/design/workflow-docs/duanxian-narrative-contract.md`:65、117 | `duanxian/design/specs/lld/characters/2026-06-07-character-it.md` §2 | 历史设计 | 【历史/旧链口径】【推断】 | 不一致 | E2 | 旧稿一方面禁止全知检索，另一方面以完整意识、反复回放和像素重建形成数据库能力；当前须逐场限定片段与缺口 | F-011 |
| G-005C｜设计 | `duanxian/novel-goals.md` §四.1 | `duanxian/conception-approved/human-review-report.md` 记忆沙箱、现实硬件控制室；`duanxian/conception-approved/human-review-report.json` `/world/environments/8/must_hold` | `duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/artifacts/03-world-rules.md` HLD-03-03；`duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/artifacts/06-event-system.md` HLD-06-03 | `duanxian/design/workflow-docs/duanxian-development-map.md` M07 | 历史设计 | 【历史/旧链口径】 | 部分一致 | E2 | 专家、模块与授权链提供外部核验承载，但部分旧稿把“可验证”停在自述，尚需落到实际独立结果 | F-011 |
| G-006｜设计 | `duanxian/novel-goals.md` §一.1、§四.1 | `duanxian/conception-approved/human-review-report.md` 跨国威胁处置、八次推进；`duanxian/conception-approved/human-review-report.json` `/world/event_conditions/1` | `duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/canonical-world-facts-v3.0.md` §3—4；`duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/artifacts/06-event-system.md` HLD-06-03—06 | `duanxian/design/workflow-docs/duanxian-development-map.md` M06—M09 | 历史设计 | 【历史/旧链口径】 | 部分一致 | E2 | 专家、模块、救援、授权、D+57 纠偏具体；17 人职责及当前 C/M 最低合作尚未逐项重映射 | F-006 |
| G-007｜设计 | `duanxian/novel-goals.md` §四.2 | `duanxian/conception-approved/human-review-report.md` 第六阶段；`duanxian/conception-approved/human-review-report.json` `/decision_controls/4` | `duanxian/design/workflow-docs/duanxian-narrative-contract.md` N1—N6、A2；`duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/artifacts/07-time-information-system.md` HLD-07-06 | `duanxian/design/workflow-docs/duanxian-development-map.md` M05、M09 | 历史设计 | 【历史/旧链口径】 | 不一致 | E2 | 旧契约的外部证据和 C5 后关闭内心很具体；C5/K9 与当前八阶段尚无正式映射，旧 PRD 事后知骗也需调整 | F-005 |
| G-008｜设计 | `duanxian/novel-goals.md` §三.1、§四.1 | `duanxian/conception-approved/human-review-report.md` 第八阶段、唐黎、苏望舒；`duanxian/conception-approved/human-review-report.json` `/world/environments/7/must_hold` | `duanxian/design/runs/prd/2026-07-07-duanxian-prd-workflow/artifacts/06-freeze-boundaries.md` PRD-FREEZE-09；`duanxian/design/specs/2026-06-06-hld-digital-life-novel.md` K9 | `duanxian/design/workflow-docs/duanxian-development-map.md` M09 | 历史设计 | 【历史/旧链口径】【推断】 | 不一致 | E2 | 七月 M09 保留沈逾执行；旧 K9 与写作模板却让 R-07 自己关闭，静态保管与多人复核也未完整 | F-005 |
| G-009｜设计 | `duanxian/novel-goals.md` §三.1、§四.1 | `duanxian/conception-approved/human-review-report.md` 开放边界、苏望舒；`duanxian/conception-approved/human-review-report.json` `/world/boundaries` | `duanxian/design/workflow-docs/duanxian-causal-storyline.md` §6；对照 `duanxian/design/specs/2026-06-06-prd-digital-life-novel.md` §7 | `duanxian/design/workflow-docs/duanxian-development-map.md` M10 | 历史设计 | 【历史/旧链口径】【未完成项】 | 部分一致 | E2 | 七月保留重载和两国未决；六月固定三部曲内容与“技术种子”不能升级为当前作者决定 | — |
| G-010｜设计 | `duanxian/novel-goals.md` §五.2 | `duanxian/conception-approved/human-review-report.md` 八次推进、十线、17 人、43 事件；`duanxian/conception-approved/human-review-report.json` `/visual_models/3` | `duanxian/design/workflow-docs/duanxian-development-map.md` M01—M10；`duanxian/design/runs/prd/2026-07-07-duanxian-prd-workflow/artifacts/final-prd-package.md` §4 | `duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/artifacts/08-thread-system.md` 六线程 | 历史设计 | 【历史/旧链口径】【未完成项】 | 部分一致 | E2 | C/M/PRD-S/K 各有功能，但没有当前八阶段、十线、43 事件的正式映射；六线程不等于十线 | F-006 |
| G-011｜设计 | `duanxian/novel-goals.md` §四.1、§五.2 | `duanxian/conception-approved/human-review-report.md` 17 人；`duanxian/conception-approved/human-review-report.json` `/characters` | `duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/artifacts/04-character-system.md` 全表；`duanxian/design/specs/lld/characters/2026-06-07-character-it.md` §2；`duanxian/design/specs/lld/characters/2026-06-07-character-zhengbozhou.md` §2 | `duanxian/design/workflow-docs/duanxian-core-character-design.md` 双核心 | 历史设计 | 【历史/旧链口径】【未完成项】 | 部分一致 | E2 | 旧人物各自有动机和权限，但只覆盖少数当前功能；郑柏舟等无一一对应，17 人完整责任网未形成 | F-006 |
| G-012｜设计 | `duanxian/novel-goals.md` §四.1 | `duanxian/conception-approved/human-review-report.md` 十二处环境；`duanxian/conception-approved/human-review-report.json` `/world/environments` | `duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/artifacts/05-environment-system.md` 六处；`duanxian/design/specs/lld/spaces/2026-06-07-space-digital-realm.md` §2—3；`duanxian/design/specs/lld/spaces/2026-06-07-space-operation-room.md` §2—3 | `duanxian/design/specs/2026-06-06-hld-digital-life-novel.md` §5 | 历史设计 | 【历史/旧链口径】【未完成项】 | 部分一致 | E2 | 旧空间有感官与状态素材，但原因保护、独立监督、静态保管、双边联络和十二环境连接未完整对应；数字空间的感官模板还须区分现实观察侧与实例侧 | F-006 |
| G-013｜设计 | `duanxian/novel-goals.md` §二.3 | `duanxian/conception-approved/human-review-report.json` `/decision_controls/1/statement`、`/decision_controls/7/statement` 与实际集合 | 检索 96 份设计，未见对当前“十个/十二”“六个/三段”声明的适配说明；旧稿不具解释权威 | `duanxian/conception-approved/human-review-report.md` 三个试读场景 | 当前疑点；历史无对应 | 【未完成项】【推断】 | 未覆盖 | E0 | 缺当前设计解释，不能推定缺失场景或样片；须由批准呈现责任方澄清统计对象 | F-001 |
| G-014｜设计 | `duanxian/novel-goals.md` §一.3、§五.3、§六 | `duanxian/conception-approved/human-review-report.md` 三样片；`duanxian/conception-approved/human-review-report.json` `/decision_controls/7/must_hold` | `duanxian/design/specs/lld/scenes/2026-06-07-scene-K1.md` 通用蓝图；对照 `duanxian/design/runs/prd/2026-07-07-duanxian-prd-workflow/artifacts/03-trunk-scenes.md` 执行表 | `duanxian/design/workflow-docs/duanxian-development-map.md` 功能单元 | 历史设计／流程规范 | 【历史/旧链口径】【流程规范】 | 部分一致 | E2 | PRD/M 系有动作和状态，K 系多为通用模板；当前正式 HLD/LLD 缺失，旧读者与章节假设不继承 | F-006 |

【推断】旧设计最值得保留的是因果和披露方法，而不是人物、能力或结局表象。workflow-docs 的 C1—C9 把团队启动、沈逾接受、主体形成、关系变化、温和重开、分层交付、终止与余波串成可追溯链；M01—M10 又给出每单元的进入状态、POV、信息边界和退出状态。这些可直接转为当前设计核对表。相反，六月“短篇小说、三个月、五线并行、内部背叛、技术资料续作”和七月 PRD“初醒感知光线声音”均只是历史方案。

人物映射采用“保留、需适配、无对应、待确认”四类：R-07/沈逾保留核心但重设终局；顾衡保留死者与记忆来源但替换旧背叛线；德米特里主要继承旧专家；梁策、贺闻钧、赵澄可继承接头、行动、联络功能但须落实人物选择；罗景明、秦峥与郑柏舟不能因同为项目主管而合并；周岚的维护例外与程予安的妻子素材须按当前同意边界重审；许曼青、唐黎、叶惟正、阿列克谢、苏望舒在当前详细设计中实质缺位。伊利亚和周启明也不能仅因都是对抗者就视为同一人物。

设计文件的自身状态不升级内容权威。07-10 HLD 仅有阻塞记录；07-13 HLD 的 `pending_hld_human_review`、artifact 12 的 `blocked_revision_required` 与 final package 的 fail 只说明旧链未完成；07-08 LLD manifest 是错误分派记录，不证明全仓库无 LLD；specs/lld 的 26 篇虽有“已完成”，多数人物/空间/场景又只提供通用模板，不能把状态字当成当前功能已经细化。

## 六、实现层一致性

实现层把 writing 的人物/空间设定与场景 prose 分开，把唯一连续正文另列。对旧设计的实现程度与对当前目标的适配不混算。正文逐段核对叙述者、知识来源、动作、状态变化、触发和退出；批准样片只用于体验，不补正文缺链。每行的“素材”和“正文”分别给出载体状态，证据限度同时说明对旧上游落实与当前适配。

| G-ID｜层次 | 目标路径+定位 | 批准路径+定位 | 设计路径+定位 | 实现路径+定位 | 材料版本/身份 | 五种口径标签 | 一致性 | 程度 | 证据限度 | 关联发现 |
|---|---|---|---|---|---|---|---|---|---|---|
| G-001｜实现 | `duanxian/novel-goals.md` §一.1 | `duanxian/conception-approved/human-review-report.md` 顾衡、R-07；`duanxian/conception-approved/human-review-report.json` `/decision_controls/0` | `duanxian/design/specs/lld/characters/2026-06-07-character-it.md` 角色功能 | 素材：`duanxian/writing/characters/2026-06-07-writer-R07.md`:63、211“我看到了另一个”；正文：`duanxian/novel-text/2026-06-07-duanxian-novel.md`:183-205、381“这是我的” | 旧素材／旧草稿 | 【历史/旧链口径】 | 部分一致 | E2 | 对旧生成弧有自指与独立判断，对当前八阶段主体形成和危机选择仅有局部承载；两处引文分属素材与正文，不串源 | — |
| G-002｜实现 | `duanxian/novel-goals.md` §一.1、§四.1 | `duanxian/conception-approved/human-review-report.md` 准入样片、核心实验室；`duanxian/conception-approved/human-review-report.json` `/world/systems/1/must_hold`、`/world/environments/7/must_hold` | `duanxian/design/workflow-docs/duanxian-development-map.md` M02、M09 | 素材：`duanxian/writing/characters/2026-06-07-writer-shenyu.md`:79 核对手册，`duanxian/writing/characters/2026-06-07-writer-R07.md`:249 自行关闭；正文：`duanxian/novel-text/2026-06-07-duanxian-novel.md`:58-76 M1—M6、`:421-443` 感知场关闭 | 旧素材／旧草稿 | 【历史/旧链口径】【推断】 | 不一致 | E2 | M1—M6 是技术激活，项目决策/受命链未展示而非明确越权；R-07 自行终止才是明确反命题，其余核验与保管未写 | F-005、F-010 |
| G-003｜实现 | `duanxian/novel-goals.md` §一.2 | `duanxian/conception-approved/human-review-report.md` 沈逾、R-07 新感情；`duanxian/conception-approved/human-review-report.json` `/characters/relationship_networks/0` | `duanxian/design/specs/lld/characters/2026-06-07-character-shenyu.md` 行为标记 | 素材：`duanxian/writing/characters/2026-06-07-writer-shenyu.md` K7；正文：`duanxian/novel-text/2026-06-07-duanxian-novel.md`:245-273 “害怕”问答 | 旧素材／旧草稿 | 【历史/旧链口径】 | 部分一致 | E2 | 对旧人物关系有一次非任务回应，对当前持续交流形成新感情及告别确认不足 | — |
| G-004｜实现 | `duanxian/novel-goals.md` §一.2、§四.1 | `duanxian/conception-approved/human-review-report.md` 周岚、程予安；`duanxian/conception-approved/human-review-report.json` `/characters/supporting_characters/1`、`/characters/supporting_characters/2` | `duanxian/design/specs/lld/characters/2026-06-07-character-qianxu.md` §2 仅有前序妻子/背叛者，无当前对应 | 素材：`duanxian/writing/characters/2026-06-07-writer-qianxu.md` 仅有妻子承诺；正文：`duanxian/novel-text/2026-06-07-duanxian-novel.md` 全文 508 行未出现周岚、程予安 | 旧素材／旧草稿 | 【历史/旧链口径】【未完成项】 | 未覆盖 | E0 | 泛称妻子不能替代程予安；完整正文范围内两位亲属的同意与在世状态均未写，不扩张为绝对不存在于未写材料 | F-008 |
| G-005A｜实现 | `duanxian/novel-goals.md` §四.1 | `duanxian/conception-approved/human-review-report.md` R-07 隔离套间；`duanxian/conception-approved/human-review-report.json` `/world/environments/2/must_not_imply`、`/world/environments/10/must_not_imply` | `duanxian/design/specs/lld/spaces/2026-06-07-space-digital-realm.md` 非物理空间 | 素材：`duanxian/writing/spaces/2026-06-07-writer-digital-realm.md`:120-125 禁写物理感官；正文：`duanxian/novel-text/2026-06-07-duanxian-novel.md`:91 明确“被提取的记忆”、`:335` 无文字输入而得会议室十秒 | 旧素材／旧草稿 | 【历史/旧链口径】【推断】 | 部分一致 | E2 | 对旧非物理界面有承载，对当前过去/现在感官可区分；但无来源的会议室知识通道未建立 | F-007 |
| G-005B｜实现 | `duanxian/novel-goals.md` §四.1 | `duanxian/conception-approved/human-review-report.md` 记忆沙箱；`duanxian/conception-approved/human-review-report.json` `/world/environments/8/must_hold`、`/world/environments/8/must_not_imply` | `duanxian/design/workflow-docs/duanxian-narrative-contract.md`:65、117 禁止全知检索；`duanxian/writing/characters/2026-06-07-writer-R07.md`:291 空白帧要求 | 素材：`duanxian/writing/characters/2026-06-07-writer-R07.md`:59-64 第七次回放、`:207-213` 轮廓；正文：`duanxian/novel-text/2026-06-07-duanxian-novel.md`:95 全节点可寻址、`:187-199` 重采样、`:343` 完整记忆 | 旧素材／旧草稿 | 【历史/旧链口径】【推断】 | 不一致 | E2 | 对旧上游反复回放有实现，对当前主观片段边界则出现完整数据库化反例；素材要求的遇袭空白帧未在正文回放中体现 | F-011、F-012 |
| G-005C｜实现 | `duanxian/novel-goals.md` §四.1 | `duanxian/conception-approved/human-review-report.md` 记忆沙箱、现实硬件控制室；`duanxian/conception-approved/human-review-report.json` `/world/environments/8/must_hold` | `duanxian/design/specs/lld/scenes/2026-06-07-scene-K5.md` §2 | 素材：`duanxian/writing/characters/2026-06-07-writer-betrayer.md`:40 门禁交叉比对；正文：`duanxian/novel-text/2026-06-07-duanxian-novel.md`:191-199 两次置信度、`:367-369` 对话记录与“可验证”自述 | 旧素材／旧草稿 | 【历史/旧链口径】【推断】 | 部分一致 | E2 | 对旧推理有档案和门禁交叉材料，对当前独立现实核验只有局部证据与自述，未见专家/硬件/授权的实际闭环 | F-007、F-011 |
| G-006｜实现 | `duanxian/novel-goals.md` §一.1、§四.1 | `duanxian/conception-approved/human-review-report.md` 跨国威胁处置、八次推进；`duanxian/conception-approved/human-review-report.json` `/world/event_conditions/1` | `duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/canonical-world-facts-v3.0.md` §4 | 素材：`duanxian/writing/scenes/2026-06-07-scene-K1.md` 仅交接失败；正文：`duanxian/novel-text/2026-06-07-duanxian-novel.md` 全文无专家、人质、硬件核验、授权链或现实阻断 | 旧素材／旧草稿 | 【历史/旧链口径】【未完成项】 | 未覆盖 | E0 | 对旧交接与轮廓推理有承载，对当前公共危机核验和物理阻断未写；结论限已完整阅读的 508 行与 17 份素材 | F-008 |
| G-007｜实现 | `duanxian/novel-goals.md` §四.2 | `duanxian/conception-approved/human-review-report.md` 第六阶段；`duanxian/conception-approved/human-review-report.json` `/decision_controls/4` | `duanxian/design/workflow-docs/duanxian-narrative-contract.md` N3、A2 | 素材：`duanxian/writing/characters/2026-06-07-writer-R07.md`:241-253 K9；正文：`duanxian/novel-text/2026-06-07-duanxian-novel.md`:331-443 成本评估、“选择：终止”及整理 | 旧素材／旧草稿 | 【历史/旧链口径】【推断】 | 不一致 | E2 | 对旧 K9 有直接内心与执行，对当前告别前禁止决定性披露构成明确反命题；行动层/原因层交付未形成 | F-005 |
| G-008｜实现 | `duanxian/novel-goals.md` §三.1、§四.1 | `duanxian/conception-approved/human-review-report.md` 第八阶段、唐黎、苏望舒；`duanxian/conception-approved/human-review-report.json` `/world/environments/7/must_hold` | `duanxian/design/workflow-docs/duanxian-development-map.md` M09 | 素材：`duanxian/writing/characters/2026-06-07-writer-R07.md`:74-75 关闭处理循环；正文：`duanxian/novel-text/2026-06-07-duanxian-novel.md`:421-443 呼吸灯熄灭、感知场关闭，`:448` 后沈逾才回操作室 | 旧素材／旧草稿 | 【历史/旧链口径】【推断】 | 不一致 | E2 | 对旧终结结果有承载，对当前执行者构成明确冲突；“启动关闭序列”只属素材，正文实际措辞为“选择：终止”；静态保管未写 | F-005 |
| G-009｜实现 | `duanxian/novel-goals.md` §三.1、§四.1 | `duanxian/conception-approved/human-review-report.md` 开放边界、苏望舒；`duanxian/conception-approved/human-review-report.json` `/world/boundaries` | `duanxian/design/workflow-docs/duanxian-development-map.md` M10 | 素材：`duanxian/writing/characters/2026-06-07-writer-R07.md` K10 技术记录；正文：`duanxian/novel-text/2026-06-07-duanxian-novel.md`:383-387 未解答的问题、`:498-508` 未关窗口 | 旧素材／旧草稿 | 【历史/旧链口径】【未完成项】 | 部分一致 | E1 | 开放感只涉及关注机制和未关窗口，不等于当前重载许可、法律身份、两国互信及静态保管的实质承载，故不计入 E2 实质内容覆盖 | F-008 |
| G-010｜实现 | `duanxian/novel-goals.md` §五.2 | `duanxian/conception-approved/human-review-report.md` 八次推进、十线；`duanxian/conception-approved/human-review-report.json` `/visual_models/3` | `duanxian/design/workflow-docs/duanxian-development-map.md` M01—M10 | 素材：`duanxian/writing/scenes/2026-06-07-scene-K1.md` 前序交接；正文：`duanxian/novel-text/2026-06-07-duanxian-novel.md` 序幕、她·1—6、它·1—3 | 旧草稿 | 【历史/旧链口径】【未完成项】 | 部分一致 | E2 | 对旧双线与主体形成有局部承载，对当前双前置受命汇流、八阶段和完整支撑线未建立；篇名不是当前结构映射 | F-008 |
| G-011｜实现 | `duanxian/novel-goals.md` §四.1、§五.2 | `duanxian/conception-approved/human-review-report.md` 17 人；`duanxian/conception-approved/human-review-report.json` `/characters` | `duanxian/design/specs/lld/characters/2026-06-07-character-it.md` §2；`duanxian/design/specs/lld/characters/2026-06-07-character-zhengbozhou.md` §2 | 素材：`duanxian/writing/characters/2026-06-07-writer-shenyu.md`、`duanxian/writing/characters/2026-06-07-writer-zhengbozhou.md` 等七类旧人物；正文：`duanxian/novel-text/2026-06-07-duanxian-novel.md` 前序、沈逾、R-07、项目主管及轮廓 | 旧素材／旧草稿 | 【历史/旧链口径】【未完成项】 | 部分一致 | E2 | 对旧双核心和主管有行为材料，对当前 17 人责任网只覆盖少数；郑柏舟是旧人物，新增/适配待核而非一律禁止配角 | F-007、F-008 |
| G-012｜实现 | `duanxian/novel-goals.md` §四.1 | `duanxian/conception-approved/human-review-report.md` 十二处环境；`duanxian/conception-approved/human-review-report.json` `/world/environments` | `duanxian/design/specs/lld/spaces/2026-06-07-space-operation-room.md` §2—3；`duanxian/design/specs/lld/spaces/2026-06-07-space-digital-realm.md` §2—3 | 素材：`duanxian/writing/spaces/2026-06-07-writer-operation-room.md`、`duanxian/writing/spaces/2026-06-07-writer-digital-realm.md` 等九份空间稿；正文：`duanxian/novel-text/2026-06-07-duanxian-novel.md` 酒店、操作室、走廊、会议室、安检前厅 | 旧素材／旧草稿 | 【历史/旧链口径】 | 部分一致 | E2 | 对旧空间感官与状态连续有承载，可服务现实观察侧；当前十二环境的功能、连接、监督与保管未实现 | F-008 |
| G-013｜实现 | `duanxian/novel-goals.md` §二.3 | `duanxian/conception-approved/human-review-report.json` `/decision_controls/7/statement` 对比 `/fragments`；`duanxian/conception-approved/human-review-report.md` 三样片 | `duanxian/conception-approved/README.md` 留存范围说明 | 素材与正文：`duanxian/conception-approved/human-review-report.md` 三个试读场景；`duanxian/novel-text/2026-06-07-duanxian-novel.md` 不是六段或三段批准样片的汇编 | 当前呈现／旧草稿 | 【当前权威口径】【未完成项】 | 证据不足 | EU | 可见样片确为三，但缺完整 P1 和正式手稿，无法判断“六个”统计范围，也不能用旧正文补数 | F-001 |
| G-014｜实现 | `duanxian/novel-goals.md` §一.3、§五.3、§六 | `duanxian/conception-approved/human-review-report.md` 三样片；`duanxian/conception-approved/human-review-report.json` `/decision_controls/7/must_hold` | `duanxian/design/specs/lld/scenes/2026-06-07-scene-K1.md` 蓝图；`duanxian/design/runs/prd/2026-07-07-duanxian-prd-workflow/artifacts/03-trunk-scenes.md` 执行表 | 素材：`duanxian/writing/scenes/2026-06-07-scene-K1.md` 全篇；正文：`duanxian/novel-text/2026-06-07-duanxian-novel.md` 序幕、她·6 | 旧素材／旧草稿 | 【历史/旧链口径】【流程规范】 | 部分一致 | E2 | 对旧 K1 的动作、信息缺省和死亡后果有承载，正文终段也有缺席后果；但不能外推全书连续性和质量 | — |

正文有六条具体证据链。其一，序幕前序遇袭只提供旧危机入口，未出现当前顾衡遗留证据接收、梁策交叉核验和现实团队阻断。其二，她·1从六模块操作直接开始，缺少“门合上以后”所展示的知情选择；她的手背测温与句号是局部人物素材，不是项目授权。其三，她·4的“害怕”是唯一明显越出任务的回应，无法单独承担新感情从形成到告别确认的全弧。其四，它·3在终止前完整展示成本收益、终止决定和记录安排，随后自行关闭；这同时破坏当前披露、权限和执行者约束。其五，郑柏舟被明确识别为遇袭关联者，当前 17 人中无此对应，不能用“项目主管相似”把旧背叛者塞入批准版。其六，全节点可寻址、像素重采样与完整记忆表述使过去材料获得客观数据库形态，独立触及 G-005B，不因视觉被标为过去记忆而消解。

writing 素材也需分类使用。R-07、沈逾和前序人物稿提供语言与动作样片，但 R-07 的自终止样片不可继承；郑柏舟、纪菱、同事、背叛者稿属于旧人物系统，无当前直接对应。九份空间稿提供酒店、操作室、会议室、机柜室、城市、住所、走廊、安检和数字空间的感官状态，其中数字空间稿明确“无物理感官”，可以支持当前接口边界；其他现实空间只能服务沈逾一侧。K1 场景 prose 与连续正文序幕内容高度重合，覆盖统计只计一项，不当作两份独立实现。

【推断】“她·4”标题下主要是 R-07 的输入模式分析，接着才是沈逾动作，属于视角标记连续性风险（P2），但不是当前禁止的内心展示本身；“它·3”才是决定性终止提前披露。第-237 段的视觉、温度与空气数据被文本明确标为记忆，不能误判为当前实时感官。相反，它·3直接引用会议室沉默而未见文字输入，才是知识来源缺口。第四天异常起始与第十一日变化点、七次匹配与两处置信度描述、素材空白帧要求与正文回放之间，分别属于待核的旧上游落实或连续性疑点，不预填为确定剧情矛盾。

## 七、实现程度与未完成项

三层均以同一组 16 条义务为分母。等级只表示本层可核对程度，历史承载计入“有实质承载”但不等于当前适配完成；E1 只含计划、标签或说明，不计入 E2/E3 的实质内容覆盖；EU 不进入缺失或冲突数量。“完全一致”按一致性列的“一致”计数，不与 E3 混称。

| 层次 | E0 未见承载 | E1 只有声明 | E2 局部落实 | E3 完整可核对 | EU | 实质内容覆盖（E2+E3，含历史） | 完全一致 / 部分一致 / 不一致 / 未覆盖 / 证据不足 |
|---|---:|---:|---:|---:|---:|---|---|
| 构思层 | 0 | 0 | 2（G-010、G-014） | 13 | 1（G-013） | 15/16 | 13 / 2 / 0 / 0 / 1 |
| 设计层 | 1（G-013） | 0 | 15 | 0 | 0 | 15/16 | 0 / 10 / 5 / 1 / 0 |
| 实现层 | 2（G-004、G-006） | 1（G-009） | 12 | 0 | 1（G-013） | 12/16 | 0 / 9 / 4 / 2 / 1 |

【未完成项】构思层的下一创作条件不是撤销批准，而是澄清两处呈现统计，并在可取得的正式机器包中复核十线、43 事件及其关系。设计层需要以当前 17 人、12 环境和八阶段重建 HLD/LLD 映射，优先解决亲属、感知、记忆数据库化、终止和披露五类硬冲突，再复用旧因果功能与空间素材。实现层需要按当前批准设计形成连续正文，先补受命与双前置，再补分层核验、现实阻断、沈逾执行的告别和静态保管，不能用润色旧终止段替代结构创作。G-009 保留 E1 是因为现有文字只提供开放语气，未具体呈现当前开放义务。

【流程规范】E3 只授予具体义务，例如构思层新主体、关系、感知、记忆边界和责任分立；没有给设计或实现层任何“整体完成”结论。当前设计或正文若保留明确硬冲突，该义务不得评 E3。历史素材使部分义务达到 E2，并不表示这些素材已获当前批准，也不表示连续手稿已进入作者定稿。

## 八、发现、修订优先级与交接

优先级衡量小说内容影响：P0 破坏主体、能力、危机闭环或终局等硬约束；P1 是关键动机、因果、关系或披露缺口；P2 是局部呈现或连续性问题。以下“可供 C”只表示有双侧证据的后续整理资格，本作业未创建 ISSUE。纯证据不足和正常未完成创作不自动转缺陷。

| F-ID | 层次/G-ID/优先级 | 双侧证据与反例检查 | 性质、影响与责任层 | E级 | 可供 C |
|---|---|---|---|---|---|
| F-001 | 构思/G-013/P2 | 目标 `duanxian/novel-goals.md` §二.3要求呈现同义；`duanxian/conception-approved/human-review-report.json` `/decision_controls/1/statement` 写十环境而 `/world/environments` 有十二项，`/decision_controls/7/statement` 写六样片而 `/fragments` 仅三项；MD/HTML 为十二处、三段 | 可见数字不吻合已证实；统计范围、隐藏本体和内容缺失为 EU，不合并成确定内容冲突。由批准呈现责任方先澄清统计对象，再决定是否构成缺陷 | EU | 条件性（仅呈现澄清，不作确定缺陷） |
| F-002 | 设计/G-001、G-007/待澄清 | 目标 §一.1已确立新主体；`duanxian/design/workflow-docs/duanxian-narrative-contract.md`:25 写形成新意识，`:79` 在故事事实列写 C3 起为新主体、读者状态列才是 preserved-open，`:92` 保留人格哲学问题；`duanxian/design/workflow-docs/duanxian-coverage-matrix.md` 信息义务矩阵 | 原“确定主体冲突”撤回：N1 已满足原反证条件。读者知识、人物事实和人格连续性应分列；如另有改变故事事实的证据才可重开 | E2 | 否（已闭合，不进确定清单） |
| F-003 | 设计/G-004/P0 | 目标 §一.2与 `duanxian/conception-approved/human-review-report.json` `/characters/supporting_characters/1/must_not_imply` 禁止周岚恋人化及暗示参与袭击；`duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/canonical-world-facts-v3.0.md`:68 主动维护例外，`duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/artifacts/04-character-system.md` HLD-04-04 关联异常授权；`duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/canonical-world-facts-v3.0.md`:73 禁止直白恋爱化 | 历史设计冲突；直接沿用会改变亲属事实和危机责任。构思适配责任在人物/因果设计；复杂依恋未直接恋人化是证据限度，不能用来豁免参与链 | E2 | 是 |
| F-004 | 设计/G-005A/P0 | 目标 §四.1和 `duanxian/conception-approved/human-review-report.json` `/world/environments/2/must_not_imply` 禁止当前视听；`duanxian/design/runs/prd/2026-07-07-duanxian-prd-workflow/artifacts/03-trunk-scenes.md`:23 感知光线声音，`:30` 听见沉默 | 历史设计冲突；直接采用会破坏存在困境和知情边界。需逐场改成文字输入或过去片段，不能用“初醒拟人化”豁免 | E2 | 是 |
| F-005 | 设计与实现/G-002、G-005A、G-007、G-008/P0 | 目标 §四.1及 `duanxian/conception-approved/human-review-report.json` `/world/environments/7/must_hold` 禁止自行终止，`/decision_controls/4` 禁止提前展示；旧 K9、`duanxian/writing/characters/2026-06-07-writer-R07.md`:74-75、249 自行关闭；`duanxian/novel-text/2026-06-07-duanxian-novel.md`:347“选择：终止”、`:441` 感知场关闭 | 历史设计与旧正文冲突；影响执行者、告别、披露和静态保管。设计责任在终局/场景，正文须按新版重作；保留 R-07 选择结束与沈逾执行的区别。M1—M6 不再被当作项目启动决定证据 | E2 | 是 |
| F-006 | 设计/G-006、G-010—012、G-014/P1 | 目标 §五要求结构可核对，`duanxian/conception-approved/human-review-report.md` 有 17 人、12 环境、八阶段；`duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/artifacts/04-character-system.md` 和 `duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/artifacts/05-environment-system.md` 仅部分人物空间，`duanxian/design/specs/lld/scenes/2026-06-07-scene-K9.md` §3 又多为通用声明 | 当前目标未落实；旧危机链丰富但人物、环境、事件与正式 ID 未重建。责任在正式 HLD/LLD，不以历史 covered 代替当前覆盖 | E2 | 否（系统性设计未完成项，先重建映射） |
| F-007 | 实现/G-005A、G-005C、G-011/P1 | 目标 §四.1限定文字知识且 17 人已定；`duanxian/novel-text/2026-06-07-duanxian-novel.md`:335 无文字来源获知会议室沉默，`:365-369` 明确郑柏舟与遇袭直接关联；`duanxian/conception-approved/human-review-report.json` `/characters` 无郑柏舟 | 旧正文新增知识/人物事实；影响信息公平和人物授权。需查其历史设计依据并标新增/适配待核，不能把主管职位当映射证据，也不能据此禁止所有新增配角 | E2 | 是 |
| F-008 | 实现/G-004、G-006、G-009—012/P1 | 目标 §一.1、§三.1、§四.1要求完整选择链；`duanxian/novel-text/2026-06-07-duanxian-novel.md` 全文 508 行只有早期转移、异常访问、审查与终止，`duanxian/writing/scenes/2026-06-07-scene-K1.md` 也只有交接失败 | 当前正文未完成；影响受命、亲属、现实阻断、开放余波和多数角色环境。责任在连续创作而非单句修订；不能以批准样片抵补 | E0—E2 | 否（创作未完成项） |
| F-009 | 实现/G-007、G-014/P2 | 目标 §五.3要求知识连续；`duanxian/novel-text/2026-06-07-duanxian-novel.md`:245-247 先写 R-07 的输入模式分析再写沈逾，标题聚焦不清；同篇 `:91` 记忆片段有明确标记 | 局部视角连续性风险；不应误判所有视觉为当前感官。责任在正文视角标记与段落整理；反证条件是标题仅作交替编号而非聚焦声明 | E2 | 是（低优先级，可随正文适配整理） |
| F-010 | 实现/G-002/撤回并合并 | 目标 §一.1、§四.1要求责任分立；`duanxian/novel-text/2026-06-07-duanxian-novel.md`:58-76 只展示 M1—M6 技术激活，`duanxian/writing/characters/2026-06-07-writer-shenyu.md`:15、79 也限定她为按流程操作者 | 原“技术激活必然等于项目启动决策权”推断撤回。未见项目授权/知情受命链是限定范围缺口，不是明确越权反命题；真实自关闭证据并入 F-005，不重复计数 | E2 | 否（不独立进 C） |
| F-011 | 设计与实现/G-005B、G-005C/P0 | 目标 §四.1与 `duanxian/conception-approved/human-review-report.json` `/world/environments/8/must_hold` 要求现实交叉核验，`/must_not_imply` 禁止可检索录像/客观数据库；`duanxian/novel-text/2026-06-07-duanxian-novel.md`:95 全节点可寻址、`:187-199` 像素重建、`:343` 完整记忆，`:369` 仅自述可验证 | 新增独立硬约束发现：记忆被写成完整数据库，且实际独立核验未闭合。设计须区分片段可用范围、外部证据和核验结果；正文不能仅靠“属于过去”规避禁令 | E2 | 是 |
| F-012 | 实现/G-005B、G-014/证据不足 | `duanxian/writing/characters/2026-06-07-writer-R07.md`:291 要求遇袭前后空白帧；`duanxian/novel-text/2026-06-07-duanxian-novel.md`:117-127 第四天异常、`:375` 第十一日变化点、`:464` 七次匹配与 `:191-195` 两次置信度并列 | 对旧上游的空白帧要求未见对应呈现已证实；时间起点和匹配次数是省略还是连续性问题尚不能确定。只列复核责任，不预填剧情矛盾 | EU | 否（待连续性复核） |

交接建议只指定责任，不预写故事：先由构思/呈现责任方处理 F-001；正式 HLD 处理 F-003—F-006；终局设计与连续正文共同处理 F-005、F-007—F-012。C 后续可整理 F-003—F-005、F-007、F-009、F-011；F-001 须先澄清统计对象，F-002 已闭合，F-010 已撤回并合并，F-006、F-008 是正常创作未完成项，F-012 仍待核，均不得为凑数转缺陷。证据不足或开放项（重载、法律身份、长期互信、读者画像、章数和总字数）均保留给作者。

## 九、证据索引与自检记录

### 1. 证据定位约定

Markdown 行号均按 BASE 的固定对象核对；JSON 使用原文件 JSON Pointer，不使用 `/tmp` 展开文件作证据。关键定位包括：`duanxian/novel-goals.md:11-27`（主题与选择链）、`:79-97`（硬约束与叙述）、`:117-127`（结构与质量）；`duanxian/conception-approved/human-review-report.md:109-171`（八推进）、`:219-329`（规则环境）、`:377-639`（人物）、`:641-693`（样片与开放问题）；`duanxian/design/workflow-docs/duanxian-narrative-contract.md:25、65、79、92、117`（主体事实、读者状态和记忆限制）；`duanxian/design/runs/prd/2026-07-07-duanxian-prd-workflow/artifacts/03-trunk-scenes.md:23`（当前感官）、`:30`（听见沉默）；`duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/canonical-world-facts-v3.0.md:63-73`（周岚）；`duanxian/novel-text/2026-06-07-duanxian-novel.md:95、117-127、187-199、331-443、448-508`（记忆数据库化、时间起点、重采样、终止与余波）；`duanxian/writing/characters/2026-06-07-writer-R07.md:63、211、249、291`（素材专属短引、关闭和空白帧要求）。

本轮 C01—C07 闭合方式：实现层所有引文按载体逐句复查，时间线定位改为 `/visual_models/3`；技术激活与项目决策分写；N1 的故事事实、读者状态和哲学开放分列；感知、记忆和现实核验拆成三项义务；E1 不再计入实质覆盖并单列一致性和 EU；矩阵不再使用“同上”或目录代替具体证据；数量差与统计范围裁决分开。逐文件账保留已通过的 121 路径/blob 集合并补 G-ID、材料身份和实际证据定位。

### 2. 命令与机械结果

以下结果在本报告形成后实测，不自称独立验收：

- 定义书 SHA-256：`ce034561ee6e2ed97295d6640349a916576c0a1e12584873e9657d89e87d0237`，与冻结预期一致；独立验收 FAIL 报告 SHA-256：`37d65901cf0381554756f4b37b72c4a97050a349edce3beed75347d41b0652a0`，亦与冻结预期一致。
- 121 文件集合由 `git ls-tree -rz --name-only 92573f1cca40f37cee04d2beb8708ff33ba603d6 -- …` 重建；逐文件账见下。
- 冻结机械检查实测 `MECHANICAL-PASS Chinese_chars= 10220 inventory= 121`：第一至八节中文字数在 8000—15000 内，九个二级标题逐字且顺序正确，五类标签、BASE 和全部 121 路径齐全，未命中秘密模式。
- 冻结补充机械检查实测 `MECHANICAL-PASS bytes=94240`：报告 UTF-8 可解码，规定关键词齐全，未命中秘密模式。矩阵、统计与覆盖交叉检查另实测 `CROSS-CHECK-PASS matrices=48 obligations=16 ledger=121 blobs=121`。
- `git diff --check` 退出码 0；`git status --short` 仅显示授权报告修改。提交白名单在暂存后复核；IMPL、报告 SHA-256 和远端 SHA 在交接回复中提供，不写入本文件形成自指。

### 3. §6 语义检查单自检

| 检查项 | 自检结果与实测范围 |
|---|---|
| A01 版本固定 | 通过；BASE、DEF、IMPL_START 完整 SHA 已列，故事证据均来自 BASE |
| A02 完整覆盖 | 通过；121 对象集合差为零，六份参照/辅助材料另列，状态文件与正文素材分别处置，逐文件均有 G-ID 与定位 |
| A03 目标完整 | 通过；目标六章拆为 16 条 G-ID，感知/记忆/核验分设，最低控制面、开放项及质量要求均有去向 |
| A04 构思自洽 | 通过；MD/JSON/HTML、17 人、12 环境及控制条目交叉核对，数字差不与范围缺失混判 |
| A05 设计落实 | 通过；96 个设计对象均有历史身份、承载、冲突、未覆盖或证据限度，旧 ID 不混用，N1 反证已处理 |
| A06 正文落实 | 通过；唯一正文 508 行及 17 份素材全读，感知、记忆、知情、权限、终止和余波按上下文判断，素材与正文分载体 |
| A07 实现程度 | 通过；三层分母均为 16，E0—E3/EU 与一致性、权威分列，E1 不计实质覆盖，未计算整体完成率 |
| A08 证据与口径 | 通过；关键发现均有目标和对象双侧定位，五种标签及反证条件已列，矩阵无“同上” |
| A09 防跑偏 | 通过；摘要、发现、建议和统计无工程基础设施结论，仅保留范围分流声明与取证命令 |
| A10 作者边界 | 通过；未裁定重载、法律身份、续作、读者、章数或全书字数，未把样片升级为事实 |
| A11 交付范围 | 通过；开工以来只修改授权报告，未改小说源文件、未创建 ISSUE；暂存白名单另行复核 |
| A12 独立性与交接 | 通过；本记录是实施自检，不冒充独立验收；F-ID、责任层、可供 C 范围和未决项已列 |

### 4. 逐文件覆盖账

表中“已全读”表示从首行至末行读取，重复内容也核对所属文件身份和差异。blob 取 BASE Git 对象前十二位；G-ID 为主要关联而非排他映射。状态型文件的设计结论只记历史身份，不拿门禁结论代替小说内容评价。末六行是三份导览和三份设计辅助材料，不计入 121 分母。

| 路径 | blob | 全文读取 | 材料身份 | G-ID、实际结论与证据定位 |
|---|---|---|---|---|
| `duanxian/conception-approved/README.md` | `fb804af28a50` | 已全读 | 当前目标/批准 | G-001—G-004、G-005A/B/C、G-006—G-014；批准日期/run/留存范围；正式状态 |
| `duanxian/conception-approved/author-decision.json` | `0de3aa7d3ca4` | 已全读 | 当前目标/批准 | G-001—G-004、G-005A/B/C、G-006—G-014；approved仅conception；/approval_scope、/decision |
| `duanxian/conception-approved/conception-completion.json` | `edad40e3089d` | 已全读 | 当前目标/批准 | G-001—G-004、G-005A/B/C、G-006—G-014；ready及九阶段绑定；/status、/stage_completions |
| `duanxian/conception-approved/human-review-report.html` | `4c02abc00966` | 已全读 | 当前目标/批准 | G-001—G-004、G-005A/B/C、G-006—G-014；折叠正文与MD同义；section-decision为事前待决 |
| `duanxian/conception-approved/human-review-report.json` | `2bad572c1d6f` | 已全读 | 当前目标/批准 | G-001—G-004、G-005A/B/C、G-006—G-014；八控制、12环境、3样片及must_hold全核；G-013数量疑点 |
| `duanxian/conception-approved/human-review-report.md` | `52d1252eb069` | 已全读 | 当前目标/批准 | G-001—G-004、G-005A/B/C、G-006—G-014；主体/17人/12环境/八阶段/三样片全核；全文 |
| `duanxian/design/runs/hld/2026-07-10-duanxian-hld-workflow/gate-report.md` | `f672becb7df3` | 已全读 | 历史设计 | G-014；早期HLD入口阻塞，无业务事实；全表 |
| `duanxian/design/runs/hld/2026-07-10-duanxian-hld-workflow/manifest.md` | `0aad7c0e3513` | 已全读 | 历史设计 | G-014；早期HLD阻塞清单，无业务产物；全表 |
| `duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/HLD-断线设计稿.md` | `2ca7a80c0063` | 已全读 | 历史设计 | G-001、G-003、G-004、G-005C、G-006—G-012、G-014；旧v3主稿世界/危机/人物；§1—4，待人审 |
| `duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/artifacts/01-world-entity-inventory.md` | `6f37bb661c4b` | 已全读 | 历史设计 | G-006、G-010、G-011、G-012、G-014；旧33实体及事实追踪；初始库存 |
| `duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/artifacts/02-prd-support-matrix.md` | `ef4e00ba7652` | 已全读 | 历史设计 | G-002、G-004、G-005C、G-006、G-007、G-008、G-014；旧PRD支撑责任分配；HLD-02-01—07 |
| `duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/artifacts/03-world-rules.md` | `b7a6da33ecb7` | 已全读 | 历史设计 | G-002、G-005A/B/C、G-006、G-007、G-008、G-009；旧技术/授权/信息/权限规则；HLD-03-01—05 |
| `duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/artifacts/04-character-system.md` | `5700fe56f581` | 已全读 | 历史设计 | G-001、G-002、G-003、G-004、G-006、G-007、G-008、G-010、G-011；旧人物动机权限；HLD-04-04周岚反例 |
| `duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/artifacts/05-environment-system.md` | `b833feb8488b` | 已全读 | 历史设计 | G-005A、G-006、G-010、G-012、G-014；旧六环境状态变化；全表，非当前十二处 |
| `duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/artifacts/06-event-system.md` | `514ec0f1f54c` | 已全读 | 历史设计 | G-002、G-005C、G-006、G-007、G-008、G-010；旧D0/D+26/D+57/D+58/终止链；全表 |
| `duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/artifacts/07-time-information-system.md` | `e43866dace09` | 已全读 | 历史设计 | G-001、G-003、G-004、G-005A/B/C、G-006、G-007、G-008、G-009；旧六信息对象披露；HLD-07-06终止意图 |
| `duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/artifacts/08-thread-system.md` | `d8c52684284f` | 已全读 | 历史设计 | G-001、G-003、G-004、G-006、G-007、G-008、G-009、G-010、G-014；旧六线程闭合；全表，非当前十线 |
| `duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/artifacts/09-style-pov-system.md` | `1a91d3e2d3bc` | 已全读 | 历史设计 | G-001、G-003、G-005A/B、G-007、G-009、G-014；旧沈逾限知/日志揭示/对话风格；HLD-09-01—05 |
| `duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/artifacts/10-inventory-reconciliation.md` | `9949152dde54` | 已全读 | 历史设计 | G-006、G-010、G-011、G-012、G-014；旧33实体归并；最终库存，状态不升级 |
| `duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/artifacts/11-hld-integrator.md` | `b18cb945b264` | 已全读 | 历史设计 | G-006、G-010、G-011、G-012、G-014；旧事实源图与LLD索引；Source Map |
| `duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/artifacts/12-hld-integrity-report.md` | `dbe5c8807d97` | 已全读 | 历史设计 | G-014；旧HLD fail及修订阻塞；Output/Risks |
| `duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/artifacts/final-hld-package.md` | `c9ac18c5380c` | 已全读 | 历史设计 | G-014；旧最终包fail/pending；Delivery Verdict |
| `duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/canonical-world-facts-v2.0.md` | `8efdee692e77` | 已全读 | 历史设计 | G-001、G-003、G-004、G-005C、G-006、G-007、G-008、G-009、G-010、G-011；被v3废弃的事实集；§2—6，不作当前依据 |
| `duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/canonical-world-facts-v3.0.md` | `d6d4591c09d1` | 已全读 | 历史设计 | G-001、G-003、G-004、G-005C、G-006、G-007、G-008、G-009、G-010、G-011；旧危机证据链及周岚冲突；§3—5，F-003 |
| `duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/gate-report.md` | `a3a8c14e80d6` | 已全读 | 历史设计 | G-014；旧HLD入口及下一道人审；全表 |
| `duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/manifest.md` | `ca117f46988e` | 已全读 | 历史设计 | G-014；旧HLD pending_hld_human_review；输出范围 |
| `duanxian/design/runs/lld/2026-07-08-duanxian-lld-workflow-blocked/manifest.md` | `95cce50ba5ce` | 已全读 | 历史设计 | G-014；错误分派更正及LLD阻塞；Superseded notice/Source Gate |
| `duanxian/design/runs/prd/2026-07-06-duanxian-prd-workflow-blocked/manifest.md` | `1e77ffa50efa` | 已全读 | 历史设计 | G-014；早期PRD阻塞记录，无业务正文；Execution status |
| `duanxian/design/runs/prd/2026-07-07-duanxian-prd-workflow/artifacts/00-proposal-risk-report-human-confirmed.md` | `c92b725096bf` | 已全读 | 历史设计 | G-001—G-004、G-005A/B/C、G-006—G-014；旧人工确认后PRD入口；Output |
| `duanxian/design/runs/prd/2026-07-07-duanxian-prd-workflow/artifacts/01-part-scope.md` | `95bba4d71b2c` | 已全读 | 历史设计 | G-001—G-004、G-005A/B/C、G-006—G-014；旧PRD范围与独立闭环；Scope table |
| `duanxian/design/runs/prd/2026-07-07-duanxian-prd-workflow/artifacts/02-part-goal.md` | `5e7f77a1b5b2` | 已全读 | 历史设计 | G-001—G-004、G-005A/B/C、G-006—G-014；旧起终状态与成功标准；Part goal |
| `duanxian/design/runs/prd/2026-07-07-duanxian-prd-workflow/artifacts/03-trunk-scenes.md` | `c71f98705469` | 已全读 | 历史设计 | G-001—G-004、G-005A/B/C、G-006—G-014；PRD-S00—18具体场景；S06/S13能力冲突，执行表 |
| `duanxian/design/runs/prd/2026-07-07-duanxian-prd-workflow/artifacts/04-conflict-value.md` | `819b7afdd49f` | 已全读 | 历史设计 | G-001—G-004、G-005A/B/C、G-006—G-014；19场景价值变化；全表，可复核状态改变 |
| `duanxian/design/runs/prd/2026-07-07-duanxian-prd-workflow/artifacts/05-information-flow.md` | `64942a26762b` | 已全读 | 历史设计 | G-001—G-004、G-005A/B/C、G-006—G-014；旧角色/读者信息流；PRD-INFO-01—06 |
| `duanxian/design/runs/prd/2026-07-07-duanxian-prd-workflow/artifacts/06-freeze-boundaries.md` | `d493dfd4871a` | 已全读 | 历史设计 | G-001—G-004、G-005A/B/C、G-006—G-014；旧14冻结边界；PRD-FREEZE-09/13终局 |
| `duanxian/design/runs/prd/2026-07-07-duanxian-prd-workflow/artifacts/07-hld-expansion-requirements.md` | `a2a8a42a3437` | 已全读 | 历史设计 | G-001—G-004、G-005A/B/C、G-006—G-014；旧HLD-REQ-01—14与当前事实原子；全表 |
| `duanxian/design/runs/prd/2026-07-07-duanxian-prd-workflow/artifacts/08-prd-integrator.md` | `d5da49198083` | 已全读 | 历史设计 | G-001—G-004、G-005A/B/C、G-006—G-014；旧场景/信息边界整合；Source Map |
| `duanxian/design/runs/prd/2026-07-07-duanxian-prd-workflow/artifacts/09-prd-risk-report.md` | `7411805b30f9` | 已全读 | 历史设计 | G-014；旧pass_to_hld与剩余风险；Output/Risks |
| `duanxian/design/runs/prd/2026-07-07-duanxian-prd-workflow/artifacts/final-prd-package.md` | `0503d10aa46e` | 已全读 | 历史设计 | G-001—G-004、G-005A/B/C、G-006—G-014；旧19场景38单元最终包；§4—11，含S06能力反例 |
| `duanxian/design/runs/prd/2026-07-07-duanxian-prd-workflow/manifest.md` | `0b143d9c8981` | 已全读 | 历史设计 | G-014；PRD历史包与当前冻结摘要；Artifact order/digest |
| `duanxian/design/runs/proposal/2026-07-05-duanxian-proposal-workflow/artifacts/01-intake-boundary-ledger.md` | `057ca231c8f8` | 已全读 | 历史设计 | G-001、G-003、G-004、G-006、G-008、G-010、G-014；旧边界继承与非冻结声明；Output |
| `duanxian/design/runs/proposal/2026-07-05-duanxian-proposal-workflow/artifacts/02-reader-promise-pre-story.md` | `101903b0e7f3` | 已全读 | 历史设计 | G-010、G-014；旧读者承诺假设；Output，非当前读者画像 |
| `duanxian/design/runs/proposal/2026-07-05-duanxian-proposal-workflow/artifacts/03-core-concept-pre-story.md` | `ba30a95aee5f` | 已全读 | 历史设计 | G-001、G-003、G-010、G-014；旧核心概念假设；Output |
| `duanxian/design/runs/proposal/2026-07-05-duanxian-proposal-workflow/artifacts/04-storyline-design.md` | `34c72736d04b` | 已全读 | 历史设计 | G-001—G-004、G-005A/B/C、G-006—G-014；旧完整梗概/CLAIM-01—10；故事主链 |
| `duanxian/design/runs/proposal/2026-07-05-duanxian-proposal-workflow/artifacts/05-storyline-quality-report.md` | `8ff39e616e6d` | 已全读 | 历史设计 | G-014；旧故事线自评及P2风险；Reference Evidence |
| `duanxian/design/runs/proposal/2026-07-05-duanxian-proposal-workflow/artifacts/06-reader-promise-final.md` | `d7e2b8a3135f` | 已全读 | 历史设计 | G-010、G-014；旧最终阅读承诺；Output，非作者决定 |
| `duanxian/design/runs/proposal/2026-07-05-duanxian-proposal-workflow/artifacts/07-core-concept-final.md` | `03b1cc2f706a` | 已全读 | 历史设计 | G-001、G-003、G-010、G-014；旧核心概念与自毁钩子；Output |
| `duanxian/design/runs/proposal/2026-07-05-duanxian-proposal-workflow/artifacts/08-final-promise-concept-consistency.md` | `b361c991282b` | 已全读 | 历史设计 | G-001、G-003、G-010、G-014；旧承诺/概念一致性声明；Findings |
| `duanxian/design/runs/proposal/2026-07-05-duanxian-proposal-workflow/artifacts/09-macro-structure.md` | `69afa63cd600` | 已全读 | 历史设计 | G-010、G-014；旧四段宏观结构；Output，非当前章数 |
| `duanxian/design/runs/proposal/2026-07-05-duanxian-proposal-workflow/artifacts/10-core-character-frame.md` | `922223a56b5f` | 已全读 | 历史设计 | G-001、G-003、G-006、G-008、G-011；旧四类角色功能；Output |
| `duanxian/design/runs/proposal/2026-07-05-duanxian-proposal-workflow/artifacts/11-world-premise.md` | `82e4920dfb91` | 已全读 | 历史设计 | G-001、G-005A/B/C、G-006、G-008、G-009；旧世界前提与未知项；Output |
| `duanxian/design/runs/proposal/2026-07-05-duanxian-proposal-workflow/artifacts/12-ending-direction.md` | `509295cf013a` | 已全读 | 历史设计 | G-008、G-009、G-010、G-014；旧悲剧开放结局及不建议系列钩子；Output |
| `duanxian/design/runs/proposal/2026-07-05-duanxian-proposal-workflow/artifacts/13-proposal-integrator.md` | `9e8a3ec7fdc8` | 已全读 | 历史设计 | G-001—G-004、G-005A/B/C、G-006—G-014；旧组装来源映射；Claim Source Map |
| `duanxian/design/runs/proposal/2026-07-05-duanxian-proposal-workflow/artifacts/14-proposal-risk-checker.md` | `2b26b0cf6b19` | 已全读 | 历史设计 | G-014；旧风险与PRD阻塞；Risks |
| `duanxian/design/runs/proposal/2026-07-05-duanxian-proposal-workflow/manifest.md` | `2be418b67a13` | 已全读 | 历史设计 | G-014；proposal历史包索引及PRD待确认；Artifact Index |
| `duanxian/design/specs/2026-06-06-digital-life-novel-design.md` | `d38666d45ade` | 已全读 | 历史设计 | G-001、G-003、G-005A/B、G-007、G-008、G-009、G-010、G-014；旧短篇/三月/五线/自我终结；§1—11，当前仅局部素材 |
| `duanxian/design/specs/2026-06-06-first-meeting-digital-life-novel.md` | `120df865f8db` | 已全读 | 历史设计 | G-001、G-002、G-003、G-005A/B、G-014；旧临终活性转移与初相见；§2—6，非当前受命链 |
| `duanxian/design/specs/2026-06-06-hld-digital-life-novel.md` | `c5aed7bab7b4` | 已全读 | 历史设计 | G-001—G-004、G-005A/B/C、G-006—G-014；旧K1—K10与五线架构；§4/§10，非当前HLD |
| `duanxian/design/specs/2026-06-06-lld-digital-life-novel.md` | `f35f462488bd` | 已全读 | 历史设计 | G-001—G-004、G-005A/B/C、G-006—G-014；旧角色空间场景索引；§2—8，需逐项重映射 |
| `duanxian/design/specs/2026-06-06-prd-digital-life-novel.md` | `216f10307caf` | 已全读 | 历史设计 | G-001—G-004、G-005A/B/C、G-006—G-014；旧内部背叛/三部曲/不可确证情感；§2—9，历史约束 |
| `duanxian/design/specs/2026-06-06-reference-survey.md` | `81ed334776e7` | 已全读 | 历史设计 | G-010、G-014；参考作品方法，非作者批准要求；D1—D5 |
| `duanxian/design/specs/2026-06-06-science-background-digital-life-novel.md` | `4e9d7a075a82` | 已全读 | 历史设计 | G-005A/B、G-014；科学假设与虚构边界；H1—H6，不作外部科学结论 |
| `duanxian/design/specs/2026-06-06-technical-systems-digital-life-novel.md` | `6a4393b50431` | 已全读 | 历史设计 | G-001、G-002、G-005A/B、G-007、G-008、G-014；六步转移与感官素材；§2—7，能力须重审 |
| `duanxian/design/specs/2026-07-05-duanxian-intake.md` | `a278e0b71f58` | 已全读 | 历史设计 | G-001、G-003、G-004、G-006、G-008、G-010、G-014；旧KEEP/CONFLICT/OPEN及待确认身份；Intake Brief |
| `duanxian/design/specs/2026-07-05-duanxian-proposal.md` | `25b303e4ad86` | 已全读 | 历史设计 | G-001—G-004、G-005A/B/C、G-006—G-014；旧完整故事链/终局分工；§4—18，历史非冻结 |
| `duanxian/design/specs/lld/characters/2026-06-07-character-betrayer.md` | `7d8e2c3f8c21` | 已全读 | 历史设计 | G-006、G-011、G-014；旧内部背叛功能；§2，当前无一一对应 |
| `duanxian/design/specs/lld/characters/2026-06-07-character-colleagues.md` | `30723a3b2ee5` | 已全读 | 历史设计 | G-011、G-014；旧同事群像；§2，仅流程环境素材 |
| `duanxian/design/specs/lld/characters/2026-06-07-character-it.md` | `e46a07e1e9d5` | 已全读 | 历史设计 | G-001、G-005A/B、G-007、G-008、G-014；旧R-07生成弧；§2，语言可借鉴/终局须重设 |
| `duanxian/design/specs/lld/characters/2026-06-07-character-jiling.md` | `7abe6200f392` | 已全读 | 历史设计 | G-003、G-011、G-014；旧生活对照者；§2，无当前直接对应 |
| `duanxian/design/specs/lld/characters/2026-06-07-character-qianxu.md` | `474a376176f0` | 已全读 | 历史设计 | G-001、G-003、G-004、G-005B、G-006、G-011；旧陆远/灰鸟记忆源；§2，不可直接替换顾衡 |
| `duanxian/design/specs/lld/characters/2026-06-07-character-shenyu.md` | `b005d1a60397` | 已全读 | 历史设计 | G-002、G-003、G-008、G-011、G-014；旧技术员行为弧；§2，须补知情受命与关停责任 |
| `duanxian/design/specs/lld/characters/2026-06-07-character-zhengbozhou.md` | `2c9369a786df` | 已全读 | 历史设计 | G-002、G-006、G-011、G-014；旧项目主管；§2，不能按职位映射当前人物 |
| `duanxian/design/specs/lld/scenes/2026-06-07-scene-K1.md` | `37d74d950265` | 已全读 | 历史设计 | G-006、G-010、G-014；旧交接失败场景；§2九字段，通用蓝图非当前场景 |
| `duanxian/design/specs/lld/scenes/2026-06-07-scene-K10.md` | `6af85e0cc8b1` | 已全读 | 历史设计 | G-008、G-009、G-010、G-014；旧终结后空缺；§2，余波局部素材 |
| `duanxian/design/specs/lld/scenes/2026-06-07-scene-K2.md` | `50d1b77580bc` | 已全读 | 历史设计 | G-001、G-002、G-005A/B、G-014；旧活性转移；§2，非当前启动/受命完整链 |
| `duanxian/design/specs/lld/scenes/2026-06-07-scene-K3.md` | `82a5775b8f1b` | 已全读 | 历史设计 | G-002、G-003、G-007、G-014；旧第一次沉默；§2，通用模板 |
| `duanxian/design/specs/lld/scenes/2026-06-07-scene-K4.md` | `d43b41f95513` | 已全读 | 历史设计 | G-001、G-003、G-005B、G-014；旧非任务停留；§2，主体形成局部素材 |
| `duanxian/design/specs/lld/scenes/2026-06-07-scene-K5.md` | `a48f8679aca3` | 已全读 | 历史设计 | G-001、G-005B/C、G-006、G-014；旧真相异常；§2，非当前分层核验 |
| `duanxian/design/specs/lld/scenes/2026-06-07-scene-K6.md` | `3c2a474b6a13` | 已全读 | 历史设计 | G-002、G-006、G-014；旧机构压力升级；§2，通用模板 |
| `duanxian/design/specs/lld/scenes/2026-06-07-scene-K7.md` | `37a6baf702d6` | 已全读 | 历史设计 | G-003、G-014；旧主动关切；§2，新关系局部素材 |
| `duanxian/design/specs/lld/scenes/2026-06-07-scene-K8.md` | `087bf35cccd5` | 已全读 | 历史设计 | G-005C、G-007、G-014；旧保留真相；§2，信息层功能须重映射 |
| `duanxian/design/specs/lld/scenes/2026-06-07-scene-K9.md` | `03f2a32dbac0` | 已全读 | 历史设计 | G-005A、G-007、G-008、G-009、G-014；旧自主终结；§2，当前执行者与披露冲突 |
| `duanxian/design/specs/lld/spaces/2026-06-07-space-apartment.md` | `a87be9687a45` | 已全读 | 历史设计 | G-003、G-009、G-011、G-012、G-014；住所/余波感官素材；§2—8，当前人物关系另审 |
| `duanxian/design/specs/lld/spaces/2026-06-07-space-city.md` | `80e849fa99b7` | 已全读 | 历史设计 | G-009、G-012、G-014；城市外部过渡素材；§2—8，剪影功能可保留 |
| `duanxian/design/specs/lld/spaces/2026-06-07-space-corridor.md` | `e09735add994` | 已全读 | 历史设计 | G-012、G-014；走廊步速/阈值素材；§2—8，可服务沈逾侧 |
| `duanxian/design/specs/lld/spaces/2026-06-07-space-digital-realm.md` | `0ff9c85a123f` | 已全读 | 历史设计 | G-001、G-005A/B、G-007、G-008、G-012、G-014；数字处理空间；§2/§9，非物理感知可保留 |
| `duanxian/design/specs/lld/spaces/2026-06-07-space-hotel-room.md` | `684f5eebeca4` | 已全读 | 历史设计 | G-006、G-010、G-012、G-014；旧K1酒店交接；§2—8，危机入口可复用 |
| `duanxian/design/specs/lld/spaces/2026-06-07-space-meeting-room.md` | `1f89910fdb26` | 已全读 | 历史设计 | G-002、G-005C、G-006、G-012、G-014；旧制度审查空间；§2—8，非当前核验闭环 |
| `duanxian/design/specs/lld/spaces/2026-06-07-space-operation-room.md` | `8bf4042ef530` | 已全读 | 历史设计 | G-002、G-005A/C、G-007、G-008、G-012、G-014；操作室界面/呼吸灯素材；§2—8，须禁作R-07感官 |
| `duanxian/design/specs/lld/spaces/2026-06-07-space-security-hall.md` | `461e7eafe1e5` | 已全读 | 历史设计 | G-002、G-012、G-014；安检准入素材；§2—8，可服务权限边界 |
| `duanxian/design/specs/lld/spaces/2026-06-07-space-server-room.md` | `1bec55803518` | 已全读 | 历史设计 | G-002、G-005C、G-012、G-014；机柜物理载体素材；§2—8，可支持唐黎核验 |
| `duanxian/design/workflow-docs/duanxian-causal-storyline.md` | `3e8efa3e3d7e` | 已全读 | 历史设计 | G-001—G-004、G-005A/B/C、G-006—G-014；旧C1—C9完整因果；§0—7，当前适配主干 |
| `duanxian/design/workflow-docs/duanxian-conception-review.md` | `4147a8a1225d` | 已全读 | 历史设计 | G-014；旧九控制审阅且待作者批准；§1—7，状态不升级 |
| `duanxian/design/workflow-docs/duanxian-core-character-design.md` | `e058b5ede84c` | 已全读 | 历史设计 | G-001、G-002、G-003、G-004、G-005A/B、G-007、G-008、G-009、G-011、G-014；双核心动机/关系机制；§0—6，较具体可适配 |
| `duanxian/design/workflow-docs/duanxian-coverage-matrix.md` | `5e9446e521a6` | 已全读 | 历史设计 | G-001、G-002、G-003、G-005A/B/C、G-006、G-007、G-008、G-009、G-014；旧covered矩阵及主体preserved-open；§信息义务，F-002 |
| `duanxian/design/workflow-docs/duanxian-development-map.md` | `acc4d1239d99` | 已全读 | 历史设计 | G-001—G-004、G-005A/B/C、G-006—G-014；M01—M10功能/POV/依赖；§功能单元，非十章 |
| `duanxian/design/workflow-docs/duanxian-intent-card.md` | `a94b39b469fe` | 已全读 | 历史设计 | G-001、G-003、G-005A/B、G-007、G-008、G-009、G-010、G-014；旧意图/三部曲/无听觉修订；§1—6，当前仅历史来源 |
| `duanxian/design/workflow-docs/duanxian-interview-review-brief.html` | `167b3f975488` | 已全读 | 历史设计 | G-001、G-002、G-003、G-004、G-005A/B/C、G-006、G-007、G-008、G-009、G-010、G-011、G-014；新版访谈简报但awaiting_author_review；§1—3及追溯版本 |
| `duanxian/design/workflow-docs/duanxian-map-check.md` | `ebf9508724a7` | 已全读 | 历史设计 | G-014；旧地图自检及四项风险；§风险，pass不代替当前判断 |
| `duanxian/design/workflow-docs/duanxian-narrative-contract.md` | `803b5f552576` | 已全读 | 历史设计 | G-001、G-002、G-003、G-005A/B/C、G-006、G-007、G-008、G-009、G-014；旧N1—N6/POV/公平隐瞒；§1—7，可适配 |
| `duanxian/design/workflow-docs/duanxian-novel-design-brief.md` | `3517fc6b09ca` | 已全读 | 历史设计 | G-001—G-004、G-005A/B/C、G-006—G-014；旧NDB九节与开放项；§1—9，ready非批准 |
| `duanxian/design/workflow-docs/duanxian-subject-definition.md` | `0d3cb3e2c569` | 已全读 | 历史设计 | G-001、G-002、G-003、G-004、G-005A/B/C、G-006、G-007、G-008、G-009、G-011、G-014；旧主体/权限/终止诱导；§0—5，部分需重设 |
| `duanxian/novel-goals.md` | `ab8b3bca7f6a` | 已全读 | 当前目标/批准 | G-001—G-004、G-005A/B/C、G-006—G-014；目标六章拆为16义务；§1—6及资料索引 |
| `duanxian/novel-text/2026-06-07-duanxian-novel.md` | `2f75856fd07c` | 已全读 | 旧素材/草稿 | G-001—G-004、G-005A/B/C、G-006—G-014；508行旧连续草稿全核；它·3自终止与提前披露，危机闭环未写 |
| `duanxian/writing/characters/2026-06-07-writer-R07.md` | `c0071b7c60fb` | 已全读 | 旧素材/草稿 | G-001、G-005A/B/C、G-007、G-008、G-014；旧R-07语言/行为样片；K9自终止冲突，G-001、G-005A/B/C、G-007、G-008 |
| `duanxian/writing/characters/2026-06-07-writer-betrayer.md` | `790b2b367dfd` | 已全读 | 旧素材/草稿 | G-005C、G-006、G-011、G-014；旧背叛者痕迹素材；§2—8，当前无对应 |
| `duanxian/writing/characters/2026-06-07-writer-colleagues.md` | `c67c12424b9b` | 已全读 | 旧素材/草稿 | G-011、G-012、G-014；旧同事环境纹理；§2—6，非当前17人覆盖 |
| `duanxian/writing/characters/2026-06-07-writer-jiling.md` | `5a1853ca9172` | 已全读 | 旧素材/草稿 | G-003、G-009、G-011、G-012、G-014；旧纪菱日常对照；§2—8，非许曼青 |
| `duanxian/writing/characters/2026-06-07-writer-qianxu.md` | `2e399a2456a5` | 已全读 | 旧素材/草稿 | G-001、G-003、G-004、G-005B、G-006、G-011；旧陆远活人/记忆样片；§2—8，非顾衡全设定 |
| `duanxian/writing/characters/2026-06-07-writer-shenyu.md` | `0f4b6ec33ceb` | 已全读 | 旧素材/草稿 | G-002、G-003、G-008、G-011、G-014；旧沈逾动作与沉默样片；K2/K7，受命及关停未覆盖 |
| `duanxian/writing/characters/2026-06-07-writer-zhengbozhou.md` | `56298516247b` | 已全读 | 旧素材/草稿 | G-002、G-005C、G-006、G-011、G-014；旧项目主管流程样片；K4/K6/K8，非当前人物映射 |
| `duanxian/writing/scenes/2026-06-07-scene-K1.md` | `429be93afed2` | 已全读 | 旧素材/草稿 | G-006、G-010、G-014；旧K1完整prose；§场景正文，与序幕重复只计一项 |
| `duanxian/writing/spaces/2026-06-07-writer-apartment.md` | `545ff9ef280d` | 已全读 | 旧素材/草稿 | G-003、G-009、G-011、G-012、G-014；住所/纪菱/杯子状态素材；§3—8，非当前亲属功能 |
| `duanxian/writing/spaces/2026-06-07-writer-city.md` | `195eb9fc7902` | 已全读 | 旧素材/草稿 | G-009、G-012、G-014；城市海风/梧桐/积水素材；§3—8，可服务余波 |
| `duanxian/writing/spaces/2026-06-07-writer-corridor.md` | `ecdbdde71a53` | 已全读 | 旧素材/草稿 | G-012、G-014；走廊脚步/停顿素材；§3—8，可服务空间连续性 |
| `duanxian/writing/spaces/2026-06-07-writer-digital-realm.md` | `fb834f722ccd` | 已全读 | 旧素材/草稿 | G-001、G-005A/B、G-007、G-008、G-012、G-014；数字空间非物理感知规则；§2/§9，支持接口边界 |
| `duanxian/writing/spaces/2026-06-07-writer-hotel-room.md` | `54a6126de6bf` | 已全读 | 旧素材/草稿 | G-006、G-010、G-012、G-014；酒店交接感官与物件状态；§3—8，支持旧前置 |
| `duanxian/writing/spaces/2026-06-07-writer-meeting-room.md` | `59a55349b8b1` | 已全读 | 旧素材/草稿 | G-002、G-005C、G-006、G-012、G-014；会议室声学/桌面/文件素材；§3—8，非现实危机核验 |
| `duanxian/writing/spaces/2026-06-07-writer-operation-room.md` | `20695d9435f2` | 已全读 | 旧素材/草稿 | G-002、G-005A/C、G-007、G-008、G-012、G-014；操作室/呼吸灯/通讯窗口素材；§3—8，仅沈逾侧感官 |
| `duanxian/writing/spaces/2026-06-07-writer-security-hall.md` | `a3b04f301aa1` | 已全读 | 旧素材/草稿 | G-002、G-012、G-014；安检/门禁/材质边界素材；§3—8，可服务授权 |
| `duanxian/writing/spaces/2026-06-07-writer-server-room.md` | `f4e3b967f4cc` | 已全读 | 旧素材/草稿 | G-002、G-005C、G-012、G-014；机柜/硬件/断电流程素材；§3—8，可服务唐黎 |
| `README.md` | `9d9c09471196` | 已全读 | G-014；资产分类与运行产物不入库；根导览 |
| `duanxian/README.md` | `8aa29b185a83` | 已全读 | G-014；当前权威与历史链分界；权威与状态 |
| `engine/docs/ai-novel-workflow/README.md` | `131fce93def1` | 已全读 | G-014；构思/开发责任及场景功能原则；§统一状态/设计原则 |
| `duanxian/design/design-tasks/2026-07-07-duanxian-hld-design-planning/design-task-package.md` | `dd9b1f24ba18` | 已全读 | G-014；规划/覆盖矩阵身份；不将工程任务矩阵纳入发现 |
| `duanxian/design/design-tasks/2026-07-07-duanxian-hld-design-planning/manifest.md` | `46292d90ebd7` | 已全读 | G-014；规划包版本与阻塞状态；Package Metadata |
| `duanxian/design/reference/2026-06-07-style-reference-liu-cixin.md` | `b5ef8b00e12b` | 已全读 | G-014；历史风格参考身份；不升级为作者要求 |
