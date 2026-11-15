# 《断线》R3 修正交付 v2 独立复验记录（A2）

作业：duanxian-audit3-acc2-001，JOB 2449。被验对象：duanxian-audit3-impl2-001，提交 30e5584de933dc282fe184bb925194f93d4aecd7。复验时间：2026-11-15 UTC。本文新增于本作业工作分支，不修改被验交付物、定义书、小说源或线上 ISSUE。

## A2/01 总体判定与适用口径

**design_verdict=FAIL；报告质量线 FAIL；ISSUE 修正质量线 FAIL；总体判定 FAIL。** 这是 v2 审视交付质量的判定，不撤销《断线》构思批准，不表示小说生产运行失败，也不否定已经核实的局部修正。

独立复验确认：A1/A2 名称、因果版本、writing 件数、六月层身份、G02 执行/决策区别、G05 人物关系、G07 Markdown 无活动备份、FREEZE-05/10 分判、#14/#22 撤回扩发、#18/#21 核心事实、九条发布记录字段等均有改善。但以下内部缺口仍在：

1. A3 的索引数组仍以机器枚举、distinct 值阅读声明及 78 条抽样支撑“全读闭合”，未交付逐 Pointer 的语义覆盖或可复现复用映射；其自身未闭合清单又明确“结构级全覆盖＋抽样值级”。不能把库外 P1 原值不可得等同于库内索引字段不必阅读。
2. G09 将实际存在的 engine/、技能入口及 harness 实现写成“不在库”。冻结树中有 1,290 个 engine/ 路径；所引脚本的 ENGINE 定位、回退及真实目标均能静态核对。这不是行号精度或交叉引用美容问题。
3. #17 一面归 insufficient_evidence，一面写“窄命题过门待证”；#19 尚未判明已有隔离是否足够便标过门；#20 保留未列明的“载体对齐子集”，没有完成逐子命题和单一关闭目标的收敛。
4. 四维去重表把 #7 的受控同版取证关闭条件缩成“留存策略声明”，把 #3 的路径引用机制写成“.gitattributes 迁移”；这些改变了实际问题及去重比较依据。

上述分别登记 ACC-F011–ACC-F014，继续关联原 ACC-F001–F010，不重编号抹去历史。本轮交 Owner 裁决，不自行执行下一轮修正。

**本次 Owner 口径优先于旧轮结尾条件**：RF-1/2/3 及外部纠错提案均如实移交 OWNER_PENDING；外部原文尚未编辑本身不作为本次 FAIL 原因。旧 acc-001 §6.3/ACC-F010 和 v2 结语中的“外部仍错误则总体保持 FAIL”在本次判定不直接沿用。这里的 FAIL 来自 v2 内部可定位缺陷，不能靠批准外部编辑消除。

定位说明：启动摘要称“定义书 §6.4 复验规则”，但冻结定义的复验要求实际在 §6.3 末段；§6.4 标题是“本定义书自身的交付检查”。“§6.1 八项”亦与正文不符：§6.1 为 R01–R11 十一项，§6.2 为 I01–I08 八项。本次完整覆盖这两张表，不虚造另一套八项标准。

## A2/02 输入绑定、独立性与检查方法

| 输入 | 独立核对结果 |
| --- | --- |
| 小说 BASE | 92573f1cca40f37cee04d2beb8708ff33ba603d6；1444 个跟踪文件；现有文件 blob 与该树逐件相同 |
| 唯一定义 | 024ef15a201a536592162b5f8442cf6a57699a8d:outputs/duanxian-audit3/def-001-definition.md；当前文件与该提交字节相同 |
| 上轮验收 | outputs/duanxian-audit3/acc-001-acceptance.md；只取原检查项、问题对象与修正要求，不继承判词 |
| v2 被验提交 | 30e5584de933dc282fe184bb925194f93d4aecd7；工作开始 HEAD 精确相等 |
| 工作分支 | remote-agent/duanxian-audit3-acc2-001；不是 main |
| 冻结 ISSUE 快照 | .kunora/inputs/open-issues-snapshot-20261114b.md；SHA-256 f6cc9ddf44be3ee199c7993e0a37bc56813cb6be8b5e238da35a9f6ffeeffd90 |
| 启动 ACK | 全文读指定摘要并逐项确认后写入作业根 .kunora/first-response-ack；单行 nonce 精确核验；业务读取在 ACK 后进行 |
| 初始工作树 | git status --porcelain 空；初始化报告及注入输入不计小说 BASE 阅读集 |

本文简称 REPORT、LEDGER、ISSUES、PROPOSAL，分别是 outputs/duanxian-audit3/ 下 impl-001-report.md、impl-001-reading-ledger.md、impl-001-issues.md、impl2-001-external-correction-proposal.md，均绑定 v2 提交。A1=author-decision.json，A2=conception-completion.json，A3/A4/A5 分别为 conception-approved/human-review-report.json/.md/.html。源行号一律绑定 BASE，不取未来 main。

方法：重新用 git ls-tree -rz 构造集合，逐件核对 OID/SHA-256/字节；读取修正后报告全文、登记及原修正指令；抽五件核验阅读账并按缺陷扩查；读取相关原对象、完整正文 508 行及双侧上下文；解析 JSON 只用于结构、计数和明确 Pointer，不把枚举当全文语义理解；只读 GET 实际 ISSUE。没有运行生产 CLI、validator 或 pytest，没有启动其他 Agent，没有修改 ISSUE。

本次不声称重新语义通读 134 件全部内容，更不声称通读全部 A3 索引；独立验收抽查不能替代实施全读义务。引用源件已通过字节身份核验，再按下文所列区间阅读。所有关键失败均由源文或被验交付本身直接支持，不由前验收结论代证。

本轮探针位于 .kunora/acc2-work/：inventory.json、bindings.json、live-issues.json、live-receipts.json、rf1-line-counts.json。它们是隔离复现材料，核心证据、计数、定位及结论均在本文，读者无需依赖实施者未提交聊天。初次非 -z 路径输出的中文转义、快照 COMMENTS 元数据误计入正文，均在探针中纠正；未把这两个验收工具解析问题计为实施缺陷。

## A2/03 R02 全读账复验与五件抽查

R 的规则为 duanxian/ 全部文件，排除 conception-production/ 与 testing/；N 为定义 G1–G7 加根 README，G7 已属 R。独立重算 **R=127、N=8、R∪N=134、E=21**。155 条路径集合精确相等，missing=0、extra=0；155 条 BASE OID、SHA-256、字节全部正确；工作文件与源 blob 全部相同。21 件工程候选在 LEDGER §2 均有选择理由和静态展开边界。集合与身份子项 PASS。

| 样本与选样理由 | 独立回读与结果 |
| --- | --- |
| n=2，duanxian/README.md，检验历史隔离反证 | 全文 24 行；L22–23 明确批准包优先、旧 runs/specs 为历史层。摘要抓住 #19 反例。所记 L1–L31 仅属 RF-1，不据此推断缺读。 |
| n=4，duanxian/conception-approved/author-decision.json，检验权威对象 | 全对象解析与逐字段读取：decision=approved、approval_scope=conception；A2 author_decision.sha256 与本体一致，A1 html_sha256 与 A5 一致。不得扩大批准范围。 |
| n=7，duanxian/conception-approved/human-review-report.json，大对象覆盖风险 | 2,836,536 字节；reduction_ledger=4602、drilldown_index=4602、source_coverage=3924。内容与元数据分开见下文；未交付索引逐项语义覆盖，按证据缺失处理。 |
| n=8，duanxian/conception-approved/human-review-report.md，检验原 G05/G07 误读 | 回读 L245–329、379–449、495–519、605–617。L271/283/327/510/609/615 支持无活动备份与静态保管边界；L416/444 是程予安婚姻，L426–435 是周岚。修正成立；账记至 617、实际 693 的数值差单列 RF-1。 |
| n=153，duanxian/testing/run_duanxian_conception_v2.py，检验 G09 缺包推断 | L16–48 指向仓库 engine/ 并有回退，L80–122 指定七个技能入口，L128 定义 H1-DUANXIAN 前缀。账称这些入口均不在库，与 BASE 树相反，属于内容错误，见 ACC-F012。 |

**A3 覆盖缺口的精确边界。** LEDGER L10、n=7（L25）、§3 第9项分别使用“全量机器审计＋78条抽样”“distinct 值全读”“结构级全覆盖＋抽样值级”。重复值复用理解原则上允许；问题是交付没有将每个 Pointer 绑定到具体已读值、复用组和语境核验，只有一行总括。定义 §3.2 明确要求逐叶阅读覆盖和同文复用时逐 Pointer 版本/语境核对。机器枚举、distinct 总声明、78个样本不能单独证明该义务。

这些数组也不是只有不可读的 P1 哈希：/drilldown_index/0 包含 stage=B0、json_pointer=/control_registry/0、label、source_id、source_anchor_id、id 和 value_sha256；/reduction_ledger/0 包含 decision_control_ids、exposure、rationale、relation、review_priority、source_anchor_id；/source_coverage/0 包含 source_id 和 visible_element_ids。库外原值缺失是 #7 限度，库内这些映射的阅读覆盖是另一件事。不得要求凭空取回 P1，亦不得用前者豁免后者。这里判“提交证据尚不能证明全读”，不臆断执行者从未读过。

LLD 模板法按同文复用规则评估，不因使用 diff 自动判 FAIL。其两个引用收据 .kunora/impl2-work/lld-scene-diffs.txt、lld-space-diffs.txt 在本作业输入中不存在，也未进提交。K2 全文独立回读支持所述内容，其他相同段不能仅凭“17件等效”推断全部语境已审；后续可交付覆盖映射补证。本轮 R02 的阻断不以这两个文件缺失或 RF-1 行数差单独成立。

## A2/04 原 FAIL 语义项与九目标反证抽查

### A2/04.1 G05、G07、brief 与版本

brief 指 duanxian/design/workflow-docs/duanxian-interview-review-brief.html。L282 用分号分别描述周岚儿时守护者和顾衡医生妻子；A4 L416/444 明确后者为程予安，故撤回“周岚婚姻细节”正确。L91 为 awaiting_author_review；novel-goals.md L97 已提及该简报，不能称“不在任何审阅清单”。L314 的 I0/I1/I4/I5 与留存 v0.2/v1.1/v1.1/v1.1 不同，I3 核心角色 v1.0 相符；I2 不可由本树同名文件核对。四项差异是一项可证的引用观察，不是全部失配。

subject-definition.md L17 区分三个月全书、D+58 处置和三个月后会面；brief L108 不能仅凭数字不同证明同一事件互斥。brief L228“暴露自身意图”须连同 L306“不直接展示决定性终局思考”解读，界面梗概不是小说 POV，v2 撤回强断言合理。G07 不再以“仅 brief 一处”限制 Markdown：A4 L271 当前无活动备份、L283 静态封存非活动备份、L327 关闭当前实例无活动备份、L510 工程师确认无备份均直接成立。

### A2/04.2 G08 知情时点及受影响下游

duanxian/design/workflow-docs/duanxian-causal-storyline.md L7 是 v1.1，L24–25 保留沈逾相信重载并废止 v1.0 已知被利用口径。subject-definition.md L34 的创伤不是知骗断言，L41 明指第二部线索，L61 时间为 delegated。其 L19“带着真相”仍需辨析真相对象，不得自动等同第一部确认被骗；按 RF-2 移交，不由本次替作者裁决。

duanxian/design/runs/prd/2026-07-07-duanxian-prd-workflow/artifacts/06-freeze-boundaries.md L15 的 FREEZE-05 单向暗恋与 A4 L400 相容；L20 FREEZE-10 首列确实要求“结尾……事后理解骗局”，不能以后列未写“立即”洗掉。叙述契约 duanxian/design/workflow-docs/duanxian-narrative-contract.md L82 禁第一部确认受骗；v2 分拆判断正确。

扩查同一信息义务：上述 PRD 的 05-information-flow.md L26–28 分别为读者先知、研究员执行、事后知骗；03-trunk-scenes.md L32–34 同向。proposal/2026-07-05-duanxian-proposal-workflow/artifacts/04-storyline-design.md L25 也写事后逐渐明白。HLD/2026-07-13-duanxian-hld-workflow/artifacts/07-time-information-system.md L22 将真实终止意图列为 D+59–D+90、沈逾读日志知晓。这些历史适配证据应回到 #10 的终局知识/执行族比较，不按载体重新发布；不是拿 FREEZE-10 偷换 #16 的 subject 对象。proposal 同目录 12-ending-direction.md L24 是 Not recommended，不能推成未来重载被绝对禁止。

### A2/04.3 G02、#17 与 #19

A3 /characters/core_characters/1/must_not_imply 禁沈逾成为启动决策者；/world/systems/1/must_hold 明确“知情接受任务的执行者，不是项目启动者”。proposal 04-storyline-design.md L15–17、L36 是组织选择路径而研究员执行。LLD character-shenyu 的越界保护框架不能证明每次技术执行均非法。G02 的旧执行禁令撤回成立。

历史时间差异可证：duanxian/design/specs/lld/scenes/2026-06-07-scene-K2.md L26 是“前序濒死”，duanxian/design-scenes-draft.md L18 是脑死亡前、仍活着的人；A4 L419 则是顾衡已经死亡。它们是历史适配差异，不否定批准。README L22–23、novel-goals.md L67–71 已有隔离声明。因此“是否仍需要逐条适配映射”需要评价既有隔离对具体消费风险是否充分，不能把一个问句自动标过门。ISSUES L94 尚未提供这项评价。

#17 两表均完整回读相关行及列头：duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/artifacts/04-character-system.md L15 是 Information permission；L21 的具体动机提危机后追问，权限列写掌握行动层。07-time-information-system.md L15 是 Known by/Hidden from；L20 的行动层 D+57 对 HLD-04-05 隐藏；L21 的完整原因层对处置组和读者隐藏。权限、某时点实际知情、信息粒度不能直接画等号。v2 降为 insufficient_evidence 正确，但 ISSUES L71、L289 的“过门/过门待证”与该结论冲突；重命名为“待澄清”不补齐证据门。

### A2/04.4 #20 逐子命题复测

完整回读正文 duanxian/novel-text/2026-06-07-duanxian-novel.md 1–508；下表 writing 路径均完整列出，不把没有叙述的动作推成禁止发生。

| 子项 | 独立证据、反证与本次裁决 |
| --- | --- |
| 传输 | writing/characters/2026-06-07-writer-qianxu.md L78–84 有 U 盘传输；writing/spaces/2026-06-07-writer-hotel-room.md L103–115 有终端动作；writing/scenes/2026-06-07-scene-K1.md L23–67 与正文 L5–45 未演出传输。载体差异可观察，“未写即未发生”的互斥不成立，撤回正确。 |
| 人数 | K1 场景 L57 门口一人，正文 L29 走廊不止一人；空间范围不同，不能排除其他人。撤回正确。 |
| 面孔 | 正文 L37 认识门外脸，L187–199/L359–363 是右侧约两米轮廓；未建立同一人，不得暗补身份形成矛盾。撤回正确。 |
| K4/K6 载体 | writing/spaces/2026-06-07-writer-meeting-room.md L17–29 指 K4/K6 在会议室；writing/characters/2026-06-07-writer-shenyu.md L82、writer-zhengbozhou.md L191–199 是电话，正文 L302 回指 K6 电话。可登记旧素材采用关系待对齐；必须明确是否保留该子项、哪一设计为采用基准，与匹配次数是否同一关闭目标，v2 未给完整决定。 |
| 地点 | writing/spaces/2026-06-07-writer-city.md L109 明标“序幕·外部”；hotel-room 为室内。不能以仓库一词推出同一地点排他，撤回正确。 |
| 匹配次数 | 正文 L191/L195 与 L363 明写 67%→82% 两次，L464 对同一推理链写七次；L379/L472 的七个认知节点是另一计数对象，不能替七次匹配作解释。此局部不一致成立。 |
| 工程/道具/披露附带项 | 编号、字符损坏、道具缺来源不自动属于同一计数修订目标。#11 输入来源、#12 姓名披露、#13 记忆能力有独立控制；不能以“载体对齐子集”吞并。 |

v2 正确撤回了多个不成立的互斥，但 REPORT §8.1、ISSUES §2.7/§5.2、PROPOSAL #20 仍用“及经证实的载体对齐子集”“单一目标确立，否则关闭”而不指明保留集合。ACC-F006 要求的子命题表和已收敛关闭条件未闭合；本次表格是验收取证，不倒算成实施交付已补齐。

### A2/04.5 九目标非发现行反证样本

| 目标 | 选样理由、原文与反证结果 |
| --- | --- |
| G01 | 批准 A4 L379–389 新意识来自启动后交流；旧 SPEC duanxian/design/specs/2026-06-06-digital-life-novel-design.md L29–33 也写自主意识。新主体方向相容，但同 SPEC L12/25–26 完整注入不能被相容结论遮盖，归 #13。 |
| G02 | proposal 04 L17“参与执行”，A3 禁决策允执行；LLD K2 L26 和草稿 L18 的濒死差异另列。没有用技术动作推出启动权。 |
| G03 | 正文 L91 明示过去记忆，可相容；PRD 03 L23/30 给当前光声和听见沉默，则归 #9。A3 environments/2、/10 的文字边界不因旧文视觉词一概判违例。 |
| G04 | A4 L277 与 A3 environments/8 要求主观片段及现实核验；正文 L95 可寻址、L193 重建像素是相反证据，归 #13；“可验证”不代表已验证。 |
| G05 | A4 L416/426–447 与 brief L282 分清两名亲属，且程予安不是 R-07 自动夫妻。旧 HLD canonical-world-facts-v3.0.md L67–73/04-character-system L20 的参与链仍归 #8，不扩大成恋人共谋。 |
| G06 | A4 L245–267、L309–315 分开现实核验、行动和原因层；旧 subject L50–51 也列专家/硬件/授权。旧链部分相容不等于所有载体完整落实。 |
| G07 | A4 L271/283/327/510 无备份；testing/duanxian_t1_builder.py L278–293 先现实阻断后沈逾执行；LLD K9 L26–33、writing/characters/writer-R07（完整文件名见 A2/05）自行关闭和正文 L331–460 则是历史反例，归 #10。 |
| G08 | 叙述契约 L79–92 区分角色/读者知识；FREEZE-05 相容、FREEZE-10 不相容；proposal 12 L24 建议不等于禁令。批准开放项没有被替作者裁决。 |
| G09 | A1/A2/A5 的本地字节绑定成立；engine/harnesses/novel-conception-autonomous/docs/final-delivery-contract.md L17–27、48–79 明确本体/呈现/同版准入区别。engine 源码缺失断言被树证据反驳，不能靠缺 P1 将它洗成正确。 |

样本覆盖批准内容、旧 SPEC、workflow-docs、proposal/PRD、HLD、LLD、writing、正文八类。遇到 A3 覆盖、G09 缺失和候选过门问题，已扩查四份 v2 交付中的全部相关行及登记 JSON，而非用九个样本的通过率抵消失败。

## A2/05 两条质量线逐项结果

### 报告质量线 R01–R11

| ID | 判定 | 独立证据与限度 |
| --- | --- | --- |
| R01 | PASS | BASE/定义/快照/工作分支准确；1444 原有文件字节未变。v2 对原实施两文件的修订及两新增见其四件清单，本次不把该派发白名单修订追溯成未授权。 |
| R02 | 证据缺失→FAIL | 134/21 集合和155件身份均过；A3逐Pointer语义覆盖不闭合，见 A2/03、ACC-F011。RF-1不作失败依据。 |
| R03 | PASS（权威与版本修正范围） | A1决定/A2完成、因果v1.1、writing17、六月层纠正；批准、历史、机器静态证据分层。G09缺失事实另由R04/R06处理。 |
| R04 | FAIL | 12字段矩阵已展开、机器复验标签已撤回，但G09实际来源列与实现程度理由使用engine不存在的错误事实；候选待证又过门。 |
| R05 | PASS | A2→A1字节、A1→A5字节、A0→A2字节成立；run_id、P1 completion、P1 manifest、H1 completion引用相等。只承认局部绑定，不宣布全链可用。 |
| R06 | FAIL | G02/G05/G07等主要反例已改；G09全称缺失被BASE反证；#17/#19证据状态与过门不一致，#20保留子集未列明。 |
| R07 | FAIL | 13项均登记，#14/#22工程扩发撤回正确；四维表#3/#4机制、#7关闭条件不忠实，ACC-F014。 |
| R08 | PASS（已复测非发现行） | A2/04.5逐目标反证；FREEZE-05/10已分拆，REJ-02保持建议级；不提升成全部内容无问题。 |
| R09 | FAIL | 本轮扩查确认A3覆盖证明和G09错误跨报告、读账、总裁决仍存在；v2未使受影响下游闭合，不能以样本数放行。 |
| R10 | PASS（可观察边界） | v2四件变更未改小说源；本次只读取证和隔离探针；无生产运行、故事改写或ISSUE写操作。远端当前状态不能证明不可见历史操作均不存在。 |
| R11 | FAIL | 非空壳、登记可解析、FAIL历史保留；但全读闭合强声明、过门待证、G09不存在等互相矛盾，无法按交付独立复现完整通过。 |

### 既有13条去重复核（R07/I03）

| ISSUE | 本轮独立复核与处置 |
| --- | --- |
| #1 | 正文限定七runtime＋三测试静态路径，不等于所有子命令失败；#22扩载体仍非新故事控制，重归工程范围外正确。 |
| #2 | 对象为两README计数，非小说质量；不重新进行技能能力审计，不发布扩展。 |
| #3 | 对象为17素材LLD路径和R07五个内容指称；不是.gitattributes迁移。#14无新故事控制，撤回正确；四维机制需纠正。 |
| #4 | 对象为Git属性text/eol匹配与字节策略，不是忽略规则。不能与#3合并成同一机制。 |
| #5 | 历史追踪门open、语义自述通过、人审pending分别成立；#17的知识映射问题不能靠改trace行自动解决，但新性不等于证据已过。 |
| #6 | 历史评审版本指称，不证明实际审错版；#15的brief四项版本差异对象不同，必须保持其有限命题。 |
| #7 | 当前留存政策已明示。关闭需受控渠道、确切run/版本、包与hash、来源/实现/validation证据；“留存策略声明”不够。 |
| #8 | A3 supporting_characters/1禁暗示参与袭击；旧HLD canonical L40/67–73及人物L20实际参与但不知全部规模，历史适配仍成立。 |
| #9 | A3 environments/2、/10 对照PRD 03 L23/L30；当前视听反例成立，过去记忆不能混判。 |
| #10 | A3 environments/7、decision_controls/4；LLD K9、duanxian/writing/characters/2026-06-07-writer-R07.md L67–76/241–253、duanxian/writing/spaces/2026-06-07-writer-digital-realm.md L56–63/123、正文L331–460双侧回读。PRD研究员执行与六月自行关闭分开。 |
| #11 | 完整正文L284–341显示会议室十秒被用于推断，未交代文字输入；不捏造麦克风。 |
| #12 | duanxian/writing/characters/2026-06-07-writer-betrayer.md L15/40/76–102及writer-zhengbozhou.md L211/260限制显名，正文L193–199/365–369/464–466显名；writer-R07.md L90/325/338和LLD character-betrayer.md L28–29的不同方案并列，旧禁令不升为现作者令。 |
| #13 | 旧SPEC完整注入、正文可寻址/像素重建对照A3 environments/8。关闭关注记忆如何成为证据；计数可随适配复核，但未预填为矛盾。#20若只保留计数，仍须说明独立目标。 |

### ISSUE质量线 I01–I08（按本次修正质量与Owner例外评价）

| ID | 判定 | 独立结果 |
| --- | --- | --- |
| I01 | PASS | 全状态列表1页22项、无PR；逐条GET22项；九条新ISSUE正文hash与v1/v2登记一致，创建时间、编号、marker匹配。 |
| I02 | FAIL | #15错误全称撤回、#16降为观察、#18/#21核心成立；#17/#19仍存在证据不足却过门，#20子集和关闭条件未定。不是因外部旧正文未改而判。 |
| I03 | FAIL | #14/#22重归类正确；四维表#7的关闭标准实质缩水、#3/#4机制错误影响比较；#20与#11/#12/#13的单一目标差异未闭合。 |
| I04 | FAIL | #20“计数＋经证实载体子集”未列具体子集/同一责任/独立关闭条件；不自动拆成多个新ISSUE。 |
| I05 | PASS（状态映射） | 9条历史已发与REPORT/ISSUES/PROPOSAL一一对应；REG/REJ有未发布状态；当前外部原文与窄命题被明确区分。 |
| I06 | PASS（当前可观察证据） | 22条当前评论数0；9条无labels/assignees/milestone，正文hash未变；本次无外部写操作，扫描未见定义token模式。不能据当前状态断言所有不可见历史行为。 |
| I07 | PASS（本轮零新增路径） | 修正轮不以候选冒充新发布；已有错误只提出Owner方案。本项不把首轮全读/发布前置门倒推为通过。 |
| I08 | PASS（披露与恢复边界） | v2明确未留POST原始日志、不补造；现有9个唯一marker及GET足以证明当前发布对象，无重复恢复对象。本轮无POST；未证明的首轮逐次发布前请求仍标证据缺失。 |

## A2/06 ACC-F001–F010 逐项对照

PASS 指相应修正义务在本次对象范围成立；部分完成但硬要求未闭合仍记 FAIL。外部未授权操作的禁止项均保持，不要求通过擅自改线上来闭合。

| 原修正 | 预期产物/复验要求 | 本次结果及 forbidden 核对 |
| --- | --- | --- |
| ACC-F001 | 逐件读账、对象索引、未闭合清单；134/21、EOF/Pointer语义覆盖 | FAIL：集合身份及21理由齐；A3覆盖证明未闭合。未以哈希冒充本次阅读，RF-1不独立扣分；续ACC-F011。 |
| ACC-F002 | 正确权威/版本/12字段/等级及缺包限制 | FAIL：大部分名称数量等级改正；G09引擎不存在为新错误，续ACC-F012。没有为补等级运行生产。 |
| ACC-F003 | G05/G07/brief双侧表、F002重分类和Owner稿 | PASS（实体修正）：对象、备份、四项引用、待审和时间反例均已纳入；#15窄观察可成立，外部稿待Owner，不暗改A3。 |
| ACC-F004 | G08时点、FREEZE分判、下游知识边界 | PASS（定向修正）：三处强冲突撤回、FREEZE-10改历史适配且不发布；本次下游回读见A2/04.2。subject L19按RF-2移交，不扩大为已知骗。 |
| ACC-F005 | G02归责、F004/F006证据分类 | FAIL：禁决策允执行与隔离事实改正；#17/#19过门结论未与待证一致，续ACC-F013。不新增角色权限。 |
| ACC-F006 | F007子命题表、剥离无关项、单一关闭目标 | FAIL：多数误报撤回且计数核心成立，但“载体对齐子集”未列明，责任和关闭条件仍条件化，续ACC-F013。不暗补身份，不自动拆发。 |
| ACC-F007 | #14/#22撤回、22条四维表与范围/新性判断 | FAIL：工程扩发撤回及22条表已交付；#3/#4/#7四维失真，续ACC-F014。不评论关闭或重发。 |
| ACC-F008 | #18/#21核心与成因限定、03/04/06映射 | PASS（核心）：PRD L34/L281状态并存，A3 12/3对statement10/6可证；源码FRAGMENTS L204/262/319为03/04/06。A3重编号01/02/03不能与源码键直接混同；计数不证明体验控制。源码L200–203说明三窗口替六概要的意图，但不能据此证明批准A3生成因果。 |
| ACC-F009 | 可解析完整候选/created字段、GET与历史限度 | PASS（登记）：2个JSON块可解析，v1块与上轮相等；v2有19候选（9+8+2）、9个created，要求字段无缺。新GET重算相符，无补造历史POST日志；语义过门矛盾另列ACC-F013。 |
| ACC-F010 | 白名单新版本交付、逐项对应、历史和待决 | FAIL（实质闭合）：4件v2产物齐、原FAIL保留、Owner方案齐；ACC-F001/002/005/006/007尚未闭合，不可用机械通过取代。不因外部待授权本身保持FAIL。 |

## A2/07 新增/续接修正指令（交Owner，不代执行）

### ACC-F011：补足库内 A3 索引阅读覆盖，撤回未证全读闭合

- 违反：定义§3.2、§3.6、S03/S05、R02/R09/R11；续ACC-F001。
- 对象原文：LEDGER L10、L25、§3-9 的机器审计/抽样值级，与REPORT §11“ACC-F001阻断项闭合”。
- 独立证据：A3三数组4602/4602/3924；字段不仅value_sha256，含来源、Pointer、展示入口、控制关系及优先级。现交付没有逐Pointer覆盖并集/复用映射。
- 正确边界：P1原值不可得维持#7；不得声称本次补出了它。可复用相同文本理解，但必须核验各对象语境和绑定。
- 要求动作/预期产物：补读尚未证明部分；新增可解析Pointer覆盖表（实际读取、复用来源、语境检查、摘要、未读）；总表与报告闭合声明一致，不补造旧时间。模板diff若继续作为证据，提供可回读收据或足够复现映射。
- 禁止：把遍历计数、唯一值数、样本数改名为语义全读；不得要求公开缺失运行包或修改A3。
- 复验：从BASE重新枚举叶节点，检查覆盖并集/复用映射和非等价语境，定向抽回来源与控制字段；未闭合则保留证据缺失。
- 影响/返回：G01–G09全量零冲突和发布前提；返回S02→S03→S05，不自动进入S08。

### ACC-F012：纠正 G09 引擎/入口可得性和前缀推断

- 违反：S06、R04/R06/R09/R11；续ACC-F002。
- 对象原文：REPORT L65/L86/L118；LEDGER n153（L171）、L197、§3-2（L208）称engine/skills入口、harness实现不在库。
- 独立反例：BASE有1290个engine路径；engine/skills/novel-storyline-architecture-designer/scripts/run_v2.py、engine/harnesses/novel-conception-autonomous/runtime/__init__.py、同runtime/production_orchestrator.py均存在。run_duanxian_conception_v2.py L16–48明确根与回退，不能将engine/projects迁移目标缺失扩大为engine全缺失。
- 正确边界：运行目录、migration输入、三个机器包未留存；实际run的执行版本和绑定未获证明。这些足够限制复算。H1前缀不同只证当前脚本默认格式与留存session不一致，不能独立证明所有实际执行入口不在仓库。
- 要求动作/预期产物：新增“仓库路径/解析根/实际存在/运行绑定”四列证据表，按范围纠正报告、矩阵、E账和总裁决；保留真正缺包限度。
- 禁止：运行生产补证、修脚本、改变已批准记录、把源码存在误写成全链验证成功。
- 复验：git ls-tree -rz及git cat-file核各精确路径；静态追L43–48回退；检查四交付所有“不在库/复算/入口”同类断言。
- 影响/返回：G09、#7、实现程度轴和全读可信度；返回S05→S06→S08。

### ACC-F013：使候选证据状态、子集合与发布门一致

- 违反：§2.3五门、§4.1、S06–S08、I02/I04/R11；续ACC-F005/F006/F009。
- 对象原文：ISSUES L71/L289“窄命题过门待证”；L94“适配映射是否足够……过门”；REPORT #20及ISSUES §2.7/§5.2的未指定“载体对齐子集”。
- 独立反例：HLD两表权限/时点/粒度不同，桥接仍缺；README已隔离历史，未评估为何不够；K4/K6载体与匹配次数涉及不同材料和验收点，当前保留范围不确定。
- 正确边界：可以保留待证观察，不能用“待澄清”使未过证据门变成通过；历史发布状态与当前候选资格分列。
- 要求动作/预期产物：#17维持未过门或补足桥接；#19明确隔离充分性判断及理由；#20逐子项列保留/撤回/待证、证据和反证，明确单一可验关闭目标；自然语言与JSON一致。
- 禁止：新建纠错ISSUE、擅自改线上、补造角色知情时点、自动拆发多个条目。
- 复验：逐项独立重读两HLD表、README/目标文档、正文和相关素材；从候选表可直接推出各门状态，不存在“证据不足且已过门”。
- 影响/返回：#17/#19/#20、去重及总体候选状态；返回S06→S07→S08。

### ACC-F014：恢复四维去重对原 ISSUE 的忠实表达

- 违反：§2.2/2.3、S07、R07/I03；续ACC-F007。
- 对象原文：ISSUES §5.2 L175“#3机制=.gitattributes迁移”，L176“#4控制=忽略规则机制”，L179“#7关闭=留存策略声明”。
- 独立反例：冻结/实取#3为文本引用与内容指称迁移；#4为text/eol属性及字节稳定，非ignore；#7明确既有政策，关闭需受控同版取证链，单纯basename或hash相等也不足全链可用。
- 正确边界：不以工程扩展去重为由开展新工程审计；但已经用于判断的对象、机制和关闭条件必须忠实。
- 要求动作/预期产物：重做受影响四维行和与候选的差异论证，保留#14/#22范围外结论；检查22条表是否还有“只换对象/载体即新机制”的外推。
- 禁止：改变冻结快照、替Owner修改关闭标准、将#7解释为必须公开入Git。
- 复验：按冻结正文及当前GET逐列对照，验证候选独立关闭理由；变化须传至报告/JSON。
- 影响/返回：DEDUP-03/04/07、F001/F009及G09边界；返回S07→S08。

## A2/08 全局硬约束、hash 与远端收据

全局重跑覆盖原§6.1十一行与§6.2八行，不以八项简称替代。四条机械证据链独立于设计判定：

1. 冻结源：BASE全部1444个已有文件逐件git hash-object等于BASE blob；duanxian/、engine/相对BASE差异为空。定义与024ef15a原字节相同。v2相对ceaca065只改REPORT/ISSUES，新增LEDGER/PROPOSAL；本次仅新增本文。
2. 批准绑定：A1 SHA-256=4f5a070d22a92fb211b9e99709e04e05b16460aa52ae40c7ebb0eaf49249e2bd；A2=4eabd4af2b249493f3aae1a2668c4de9b37dea7f61628e1b454293e49587d127；A5=80cfc4d82d77683324808ba3f96817914c24fd1de007fae70641789dedf65e36。分别与A2作者引用、A0完成说明、A1 HTML引用一致。引用值相等的P1/H1哈希未冒充对应缺失本体重算。
3. 公开状态：无认证GET，固定api.github.com、拒绝重定向；全状态列表1页22条、无PR，随后22次单条GET；当前评论总数0。#1–#13正文与冻结快照BODY区一致（排除COMMENTS元数据与末尾换行）；#14–#22与登记哈希一致。只证明回查时点状态，不能恢复历史POST前全日志。
4. 秘密与权限：四件v2文件及22条线上body按定义token字面量模式扫描0命中；凭据未进入正文、URL、命令参数或临时文件。本次无ISSUE写操作、无生产流程；提交前另检本文并按冻结机械argv运行，结果记录作业根JSON。

| ISSUE | created_at UTC | 本次GET正文SHA-256（与v2相同） |
| --- | --- | --- |
| #14 | 2026-11-14T12:52:13Z | 5fb154303e9e1d576e746c1cf2bdf0f836d4caad749a01b4fe18bb73f0cb2d28 |
| #15 | 2026-11-14T12:52:18Z | 7581445b5ab13913ec59aa2859915cbad7f9de3a5dc5caa336a50de4787073cc |
| #16 | 2026-11-14T12:52:22Z | c43c926d355ea5a4c1ce9b088cec9b3a14f4c66684baa1a0124ae7c772291300 |
| #17 | 2026-11-14T12:52:27Z | ddae703bfc11bf45f5631a21290430a4d9efc8507830b9c2e97e7eb6cd5e4e93 |
| #18 | 2026-11-14T12:52:32Z | 34c9ec64c3f1aaa8d1cce96566caa4f857d5c400649826b2b415699fee6ea9b4 |
| #19 | 2026-11-14T12:52:37Z | 8521063d9fa73ad6e338cfbcf3749da1de54dfc0dab69bc77ad5e304a88cf5d0 |
| #20 | 2026-11-14T12:52:42Z | eea29d09a5e19aaa994ab967e7206b98658da590c514f8920b709470543b5a9f |
| #21 | 2026-11-14T12:52:47Z | c10b62c7d1933001565ee9c6676770dd2eacd9b89f04cf29d720e829a34e773b |
| #22 | 2026-11-14T12:52:51Z | 186d0bd68319530e46757729e7feaaac661d2b988a6284129f510435add6457f |

本次实取原文与元数据保存在隔离live-issues.json；正文可由 https://api.github.com/repos/innuama-coder/ai-novels/issues/{number} 重新获取并按UTF-8算SHA-256。网络结果或后续线上变化不能静默覆盖本时点收据。

## A2/09 Owner 移交、RF 与交付

| 项目 | 移交内容与判定边界 |
| --- | --- |
| RF-1（minor） | 行区间数字精度；自动核对显式L1–Ln的终点有44处与splitlines实际行数不同，例如README 33/19、项目README31/24、A4 617/693。只统计数字差，不等于44件缺读。本次不以其判FAIL；A3覆盖证明和engine事实错误分别立项。 |
| RF-2（minor） | subject L19“带着真相”须区分原因层/终止事实/被骗知识；不自动推出第一部知骗。移交Owner，未作新事实裁决。 |
| RF-3（cosmetic） | 交叉引用：目标表实际在定义§1.3而非第二节；复验条款在§6.3末段；ISSUES所称§5.1收据实际位于§2及机器JSON。保留定位对照，不作为FAIL。 |
| 外部纠错 | PROPOSAL完整移交OWNER_PENDING：#14/#22建议关闭说明；#15/#16/#17/#19/#20建议收窄或证据不足关闭；#21证据强度澄清；#18核心可保留。任何实际动作须Owner另授权，本轮不执行。 |
| manual-review | OWNER_PENDING；Owner确认记录完整和语义正确；不以此代替实质核验，也不预填作者签认。 |
| v2内部缺口 | ACC-F011–F014及原ACC未闭合项交Owner决定后续处理。本次保持FAIL，不自动启动下一实施LOOP。 |

唯一Git交付：outputs/duanxian-audit3/acc2-001-acceptance.md。作业根 .kunora/acceptance-report-r1.json 承载design_verdict、机械检查实际输出、提交与远端SHA、受影响项和Owner状态，不进入业务提交。仅使用指定remote-agent署名/提交消息，显式add本文，仅推本作业分支、不force。提交后的冻结机械检查与远端SHA核验属于交付验证；其PASS不改变本文design_verdict=FAIL。

复验分组已完成：A2/输入与全读证据、A2/事实与反证、A2/候选与去重、A2/硬约束与移交。所有后续建议均为验收修正指令，不是本轮小说或外部ISSUE改动。
