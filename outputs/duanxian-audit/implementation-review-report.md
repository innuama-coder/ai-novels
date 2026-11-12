# 《断线》实施审视报告（工作项 B·修正轮 r3）

- 内容基线 BASE：`92573f1cca40f37cee04d2beb8708ff33ba603d6`（冻结只读；本报告全部证据取自该树）。
- 规范输入：B 定义书 rdef-001（完整 SHA `c423216ef9f8bbe8a9846b1a4d877d298a9334f7`）；A 基准 gdef-001（`68ec7c0a…`）与目标拟人化总结（`ac7f045a…`）仅作目标口径基线，不引为新故事事实来源。
- 方法与执行边界：只读静态审视（`git ls-tree/show/grep`、本地 SHA-256 重算、`python3 -I` 标准库行为观察）；本轮未运行仓库 CLI、pytest、validator 或任何构建，未访问仓库本体之外的网络资源。
- 本稿为按独立复核 raccr2-001 §8 RF01–RF08 逐条修正的 r3 稿（其上一稿 r2 的修正源头为 racc-001 F01–F10）；修正仅落本文件，不改动任何既有源文件与历史证据。全文事实逐条贴口径标签：【当前权威口径】【历史/旧链口径】【未完成项】【流程规范】【推断】。

## 一、审视范围与证据基线

**总量与分层（B-E049）**：BASE 跟踪树共 1444 个文件：根层 6、`duanxian/` 148（147 个常规路径＋1 个中文名文件 `duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/HLD-断线设计稿.md`——文件名字节不含引号，前稿所见引号是 `git ls-tree` 对非 ASCII 名的显示层转义，非文件名属性）、`engine/` 1290（docs 83、skills 669、harnesses 404、scripts 5、tests 6、testing 10、tasks 112、README 1）。

**覆盖账（RF01 重述，按层闭合，三类互斥）**：

| 层（总数） | 全文读毕 | 定点/行级 | 结构·清单·哈希核对 |
| --- | ---: | ---: | ---: |
| 根层（6） | 6 | 0 | 0 |
| duanxian（148） | 22 | 50 | 76 |
| engine/README.md（1） | 1 | 0 | 0 |
| engine/docs（83） | 0 | 14 | 69 |
| engine/skills（669） | 0 | 45 | 624 |
| engine/harnesses（404） | 0 | 24 | 380 |
| engine/scripts（5） | 0 | 5 | 0 |
| engine/tests（6） | 0 | 0 | 6 |
| engine/testing（10） | 0 | 3 | 7 |
| engine/tasks（112） | 0 | 0 | 112 |
| 合计（1444） | 29 | 141 | 1274 |

三类口径互斥闭合：29＋141＋1274＝1444，与逐层清单总数一致（engine/README 计入 engine 层，不与根层重复）。

**全文读毕 29 件逐一点名（RF01 补全；本轮新增：根层补齐 6/6、写作层 14/17、engine/README）**：
1. 根层 6：`README.md`（19 行）、`.gitattributes`（23 行）、`.gitignore`（19 行）、`.serena/.gitignore`（2 行）、`.serena/project.yml`（168 行，工具配置）、`.zcode/plans/plan-sess_316609e2-5263-4909-a27a-c47b17476339.md`（89 行，即 B-E045 根层唯一命中文件）。
2. duanxian 22＝批准目录 4 件（`conception-approved/README.md`、`author-decision.json`、`conception-completion.json`、`human-review-report.md`，两 JSON 为全字段走查）＋`duanxian/novel-goals.md`＋`duanxian/README.md`＋`novel-text/2026-06-07-duanxian-novel.md`（508 行）＋`conception-production/run.py`（1082 行，两段读毕）＋写作层 14 件（characters 7：writer-R07/writer-betrayer/writer-colleagues/writer-jiling/writer-qianxu/writer-shenyu/writer-zhengbozhou；scenes 1：scene-K1；spaces 6：digital-realm/hotel-room/meeting-room/operation-room/security-hall/server-room）。
3. engine 1：`engine/README.md`（27 行；L9 技能计数、L27 引擎内部以 engine/ 为根寻址约定）。

**未全文读毕与处理方式（如实登记，不以抽样冒充全读）**：写作层余 3 件按定点核对——`apartment.md` 读至 L46（前 46 行全文，余部按锚点与禁写词核对）、`city.md`/`corridor.md` 作模板同型核对（同型空间模板已由 6 件全读代表，二者无独有禁写词命中）；engine 各大层按结构/清单/签名核对——skills 669 中 82 个 SKILL.md 头部归类＋7 个生产技能与 3 个标记类技能跨文件核对（第六节闭包）；31 个 zip 二进制仅目录/清单/sha256 核对（B-E034），其中 8 对为同源重复投影（唯一 23）；`human-review-report.html` 为结构核对（svg/外链/script 计数）。

- **限制声明（硬门现状保留）**：定义书"全部全文读毕"硬门仍未满足——141 件定点与 1274 件结构核对不等于逐字全读；本报告按定义书允许的分级口径给出上表并保留该失败声明。结构核对类仅支撑计数、存在性与引用真实性结论，不单独支撑语义结论；抽样按定义书 §2.5 高风险全查＋确定性抽样执行。
- 否定性断言与可复现性：本报告全部否定性断言（零命中、不存在、未见）附检索范围与规则——文件名类用 `git ls-tree -r --name-only` 全名单精确匹配；内容类用全树 `git grep` 或目录内全文扫描；"对象不在树"与"对象从未存在"严格分开表述。全部计数类结论可用标准命令对 BASE 复现。
- 权限与红线遵守：秘密零打印零写入，凭据仅经命令替换引用；未修改宪法、spec 与历史证据；运行账本按 `.gitignore:L11–18` 设计不入库（B-E004）【流程规范】，构成第三、四节"本体不可复验/无法判断"类限制的来源。

## 二、目标六问与实现对照

章节定位按 BASE 实测行号重映射（RF03；前稿误标处一并改正）：`novel-goals.md` 六章为第一章「主题与目标」L7–27、第二章 L29–51（含"3. 内容权威与呈现分离"）、第三章 L53–71、第四章「约束」L73–103（七控制表 L79–89）、第五章 L105–127（含"2. 分部、章节与覆盖目标"）、第六章「验收标准」L129–151；项目当前进度并非专章，状态分散于 L49–51/L71/L113 与 `duanxian/README.md`。

| 问 | 目标定位（BASE 实测） | 实现对象（路径） | 正向证据 | 缺口/反证 | 程度 | 强度 |
| --- | --- | --- | --- | --- | --- | --- |
| 要写一本什么小说 | 第一章 L7–27：数字生命近未来长篇，危机闭环与伦理未决并立【当前权威口径】（B-E001） | 批准构思 `human-review-report.md` 故事章（B-E012）；`novel-text` 旧稿（B-E013）【历史/旧链口径】 | L277–289 记忆非录像、R-07 为新主体；旧正文 L464–476"评估完成。选择终止。" | 旧稿成稿于 2026-06-07，先于 2026-08-17 批准；与新版叙述契约 L26 存在差异（第五节） | 构思层已完成（限定批准范围）；正文层属历史遗留 | 直接留存 |
| 为何写 | 第一章动机段 L9–21＋意图卡 L15–17 动机问句【历史/旧链口径】（B-E001/B-E015） | 批准报告 L251–255 原因层、L608–615 保管责任人（B-E012） | 批准层主题证据完整 | 主题执行须待 HLD 与正文；意图卡只是主题来源，不得代作者宣布唯一伦理答案 | 构思层完成；执行层无法判断 | 直接留存／不足 |
| 为谁写 | 第一章 L23–27；意图卡 L31"目标读者未指定"【未完成项】（B-E001/B-E015） | 无商业画像产物 | 未决状态本身有直接记录 | 任何具体读者画像或渠道判断都是编造 | 未决（作者侧待定，非程序缺陷） | 直接留存（未决记录） |
| 怎么写 | 第二章 L29–51：构思 V2→开发基线→HLD→LLD→写作→分层评审【流程规范】（B-E001） | 构思链 approved/ready（B-E007/B-E008/B-E009）；引擎 HLD/LLD 工具链 implementation-candidate（B-E037） | 作者批准＋完成记录＋三层哈希账（第三节） | 开发 handoff 本体未留存（B-E009 引用不可复验）；`run.py` 七条 runtime 路径静态断裂（B-E028） | 构思段完成；HLD 及以后未证 | 直接留存＋静态可定位 |
| 写成什么样算合格 | 第六章「验收标准」L129–151 三门＋第四章「约束」L73–103（七控制表 L79–89）；`development-phase.md` L137–152 场景 80/70% 规则【流程规范】（B-E043） | 构思段留痕分层：作者门 approved（B-E008）；机器门引用一致＋3 对象重算（第三节）；语义门 `review_path` 五项结构化导航（B-E011） | 作者门与机器门（引用一致层）可支撑 | 语义门仅有结构化留痕，逐元素判定本体未留存，不可复验（第三节）；场景级评分零实例；validator 本轮未重放 | 构思段部分可复验；后续门无启用证据 | 引用值／直接留存分层 |
| 当前进度与断点 | 状态分散于 L49–51/L71/L113＋`duanxian/README.md` L3/L22–23（六章中无专门进度章——前稿误标"第六章"，据 BASE 改正） | 批准链 2026-08-17（B-E007） | 批准与留存绑定成立 | 旧 HLD 停在 pending 人审【历史/旧链口径】（B-E019–B-E022）；新版 HLD 运行留痕未见且账本不入库，现实进度无法判断【未完成项】 | 构思完成；HLD/LLD/写作现实进度无法判断 | 直接留存＋不足 |

说明：矩阵逐行贴口径；"无法判断"均指冻结证据不可得，不指现实未发生。

**逐问补充解读**：
1. "要写什么"——目标文档把主承诺定为"危机闭环与伦理未决同时成立"，不用胜利抵销失去（B-E001）；批准纲要以硬规则、开放边界两章承接（L295–315、L325–329）；旧正文结尾段方向一致，但其因果安排先于新版叙述契约，只能作历史参照，不得计为批准后的实现。
2. "为何写"——批准报告的授权链（L468–475）与保管责任人（L608–615）给出人物级落点；写作层的责任刻画目前只存在于 2026-06-07 旧稿，BASE 未见批准后新版写作产物或其运行留痕（运行账本按政策不入库），现实是否已开工不可判断【未完成项】。
3. "为谁写"——未决。目标读者、年龄层与渠道均无作者决定，本报告不以沟通对象【推断】替代定位事实。
4. "怎么写"——流程规范要求每次交接携带来源、版本、约束与状态；构思段三份记录（author-decision/completion/human-review-report）携带上述必要字段，满足交接记录的信息要求；但完整交接链还要求机器本体可消费、语义与作者门可复验（`final-delivery-contract.md` L64–79，B-E044），后两者本体在冻结树不可得，"构思→开发"交接的下游连续性仍不可复验，这是流程可用性的实际断点。
5. "写成什么样算合格"——三门与场景 80/70% 规则是"应当"而非"已经"；构思段可支撑作者门（批准记录）与机器门（引用一致层），语义门有结构化留痕但未做逐元素复验；场景级评分规则尚无任何实例记录可援引。
6. "当前进度与断点"——冻结证据只能确认：构思阶段完成并批准；旧链停在人类评审门；引擎侧 HLD 工具链为候选态。现实是否已推进新版 HLD 属树外事实，本报告不代答。

## 三、构思批准链与P1留存

【当前权威口径】批准事实（字段归属按 BASE 字节改正，RF02）：`duanxian/conception-approved/author-decision.json` `/approval_scope=conception`、`/decision=approved`、`/run_id=duanxian-conception-v2-20260811-18`、`/approval_record/text`＝"构思合格，完成提交并推送。"、`/approval_record/event_seq=1`、`/approval_record/unresolved_items=[]`（后两键属 author-decision.json，前稿误置于 completion，B-E008）；`conception-completion.json` `/status=ready`、`/run_id` 与上一致、`/stage_completions` 九键 B0,C1,E1,H1,P1,Q1,S1,T1,W1（B-E009，该文件不含 event_seq/unresolved_items/review_path 字段）；批准 README 记 2026-08-17 作者批准、approved/ready（B-E007）。

**哈希三层账（重算、引用一致、本体不可得分层）**：

| 层 | 对象（运行相对路径） | 值与绑定 | 判定 |
| --- | --- | --- | --- |
| 本轮本地重算 | author-decision.json | `4f5a070d22a92fb211b9e99709e04e05b16460aa52ae40c7ebb0eaf49249e2bd`＝completion `/author_decision/sha256` | 一致，直接留存 |
| 本轮本地重算 | conception-completion.json | `4eabd4af2b249493f3aae1a2668c4de9b37dea7f61628e1b454293e49587d127`＝批准 README L22 记录值 | 一致，直接留存 |
| 本轮本地重算 | human-review-report.html | `80cfc4d82d77683324808ba3f96817914c24fd1de007fae70641789dedf65e36`＝author-decision `/human_review_package/html_sha256` | 一致，直接留存 |
| 引用值跨文件一致 | P1/package-manifest.json | author-decision `/machine_package/manifest_sha256`＝completion `/p1_manifest/sha256`＝`bba81d35a089320074eb8677911707052ba99b1265fbf19731c78785a1eef8ce` | 两处记录一致；本体未留存，不可重算 |
| 引用值跨文件一致 | P1/stage-completion.json | author-decision `/machine_package/completion_sha256`＝completion `/stage_completions/P1/sha256`＝`42e307d1089a58ed3df6f13059007fe33f48da993b8c62832edc141f2a6e249b` | 同上 |
| 引用值跨文件一致 | H1/stage-attempt-02/stage-completion.json | author-decision `/human_review_package/completion_sha256`＝completion `/stage_completions/H1/sha256`＝`28ec088d192374e825bfb4ffb44853bdf6e498f518d625f266980a91f1834e89` | 同上 |
| 单处引用、本体不可得 | H1/stage-attempt-02/package-manifest.json（`fbe8b9a6…`）、H1/html-attempt-04/package-manifest.json（`72092963…`）、P1/development-handoff.json（`d48194db…`）、`/validation/sha256`（`c370cea5…`） | 仅留存文件单侧记录（B-E009） | 引用值，无法复验 |
| 运行态（设计不入库） | `state/revision-037.json`（completion `/run_state` 引 `1ca5af5c…`）与批准 README L18/L21 终态 `state/revision-038.json`（`0679739a…`） | 两处分属完成时点与终态时点 | 阶段先后解释成立，非冲突 |

- 三层分离结论：**记录批准**成立；**留存文件绑定**对 3 个重算对象成立；**全链重新验证未做**——validator 未重放、机器本体不在树，本报告不声称"合规/三投影一致已复验"【流程规范】。
- 三门执行证据分层（RF02，按 `final-delivery-contract.md` L64–79 的"哈希/结构不能证明语义"收窄）：作者门＝author-decision.json `decision=approved`（记录成立）；机器门＝manifest/JSON 引用一致＋3 对象本地重算（不含 validator 重放）；语义门＝`human-review-report.json` `/review_path` 五项（kinds world/storylines/characters/fragments/decision，estimated_seconds 187/113/89/175/23，合计 587 秒）为**结构化导航留痕，非语义判定本体**——逐元素语义判定的 presentation-fidelity-review 本体未留存，语义门执行不可复验，"构思段三门全部执行"不成立。
- e2e 证据归属更正（RF02）：`engine/testing/test_conception_autonomous_v2_e2e.py` L112–125 `_test_fidelity_review` 是**忠实度评审 fixture**（其"门"指呈现忠实度，非作者门），不得用作作者门绑定证据；作者绑定的静态机制在 `engine/harnesses/novel-conception-autonomous/runtime/author_decision.py` L202–255（P1 指纹不匹配即拒绝）＋L80–88 `_validate_sealed`（B-E031/B-E041）。"作者门不可由生产侧合成"的规范表述成立，证据落点以此为准。
- 版本号的分层含义：completion 内 `/run_state` 引用完成时点快照（`revision-037`），批准 README 的 final state 是运行收束后的终态记录（`revision-038`）；两处指向不同时点，属记录阶段差而非冲突；两个状态本体均未留存，作引用值对待。
- 留存政策与缺口：批准 README L3"运行账本和历史尝试不纳入 Git"＋`.gitignore:L11–18`（B-E004/B-E007）。三个机器 basename（novel-conception-package.json、development-handoff.json、hld-completion.json）对 BASE 全量文件名列表精确匹配零命中（B-E048）——这是**留存缺口**，不证明机器链不存在，也不否定批准【未完成项】。
- 人审计数（`decision_controls=8`、`visual_models=5`、`fragments=3`、`drilldown_index=4602`、`reduction_ledger=4602`、`source_coverage=3924`，均出自 human-review-report.json，B-E011）与 HTML 结构（5 个 svg、0 外链、0 script）属**结构/离线核对**，不等于逐元素语义验证（B-E010）。

## 四、HLD与LLD断点及旧链隔离

**版本时间线（均为冻结记录；v4.0 日期按 BASE L10 实测改正为 2026-06-07——前稿误写 2026-06-06，RF06）**：

| 时点 | 对象与状态 | 口径 |
| --- | --- | --- |
| 2026-06-06/07 | `design/specs/2026-06-06-hld-digital-life-novel.md`（文件名日期 06-06）L10 记 v4.0 于 2026-06-07 收束，风格章现位于 §9（L312–339）（B-E017） | 【历史/旧链口径】 |
| 2026-06-06 | `design/specs/2026-06-06-lld-digital-life-novel.md` L36–39 反斜杠旧路径（B-E018） | 【历史/旧链口径】 |
| 2026-06-07 | `duanxian/writing/` 17 件＋`novel-text` 旧正文（B-E013/B-E027） | 【历史/旧链口径】 |
| 2026-07-05 | `design/specs/2026-07-05-duanxian-proposal.md` L39/L45–46 Agent pass、人审 pending；§18 L265–267 门类与放行条件、L276 非冻结声明（B-E016） | 【历史/旧链口径】 |
| 2026-07-08 | `design/runs/lld/2026-07-08-duanxian-lld-workflow-blocked/manifest.md` blocked/superseded 留痕（B-E024）；引擎侧 `engine/docs/superpowers/runs/design/2026-07-08-hld-lld-design-task-dispatch/manifest.md` 存在（B-E025） | 【历史/旧链口径】 |
| 2026-07-13 | HLD run：`manifest.md` L12–15 定 canonical v3.0 唯一事实源、人审前不得进入 LLD（B-E019）；`artifacts/12-hld-integrity-report.md` L25 HLD-TRACE-CLOSURE P1 open、L32–34 fail/pending_required/blocked_revision_required（B-E020）；`artifacts/final-hld-package.md` L20–22 fail/pending/blocked（B-E021）；`gate-report.md` 列下一道人类评审门（B-E022） | 【历史/旧链口径】 |
| 引擎侧 | `engine/harnesses/novel-hld-autonomous/manifest.yaml` L1–27：13 阶段 HB0–HF1、implementation-candidate、codex-only；L44–48 not-run（B-E037） | 【流程规范】＋【未完成项】 |

**旧链隔离词表核验（B-E050，RF03 全表重述；检索为 BASE 全文逐字匹配）**：

| 方向 | 词面 | 检索范围 | 结果 |
| --- | --- | --- | --- |
| 旧链→批准 | 陆远、灰鸟、郑柏舟、四段式、三者关系、K9、K10（7 词） | author-decision.json、conception-completion.json、human-review-report.md 三份批准文件全文 | 均 0 命中；K1–K8 亦逐一复验 0 命中 |
| 批准→canonical | 程予安、许曼青、秦峥、梁策、伊利亚、德米特里（6 名） | `canonical-world-facts-v3.0.md`（对 v2.0 同法复验） | 均 0 命中 |
| 范围限定 | 沈逾、顾衡、周岚 | canonical v3.0 | 各命中 5、9、11 次——新旧链在 canonical 层有共有人物，词表结论不得外推为整体隔离 |

结论限定（撤回前稿"隔离已核"的全称表述）：上述结果仅证明**词表内**旧链专名/术语未渗入批准文件、**词表内**批准新名未见于 canonical v3.0/v2.0；语义级隔离未逐事实核验，不作全称断言。`HLD-TRACE-CLOSURE` 全树 `git grep` 仅 2 文件命中。`canonical-world-facts-v2.0.md` 与 `v3.0.md` 并存（B-E023），以 manifest 指定的 v3.0 为准。

- 冻结记录内状态不外推：2026-07-13 的 open/pending 是**冻结记录内**的状态判定，不延伸为"至今无处置"——现实处置在树外不可知。同理，新版 HLD 在 BASE 未见运行留痕（账本设计不入库），因此**无法判断**新版是否运行过或是否开工，不得写"未运行/零运行/正文未开工"。
- 层级不外推：proposal 的 Agent pass、旧 HLD 的 pending、引擎 harness 的 implementation-candidate、2026-08-17 构思批准，四者分属不同层与不同版本，任一层状态不得替代另一层的准入判断【流程规范】。
- 命名与布局两则：其一，K1–K10 场景号、"陆远"等旧链专名只在各自来源内使用，未渗入批准口径（词表零命中见上表，人物侧另见第五节）；其二，`engine/README.md:L27` 确立"引擎内部一律以 engine/ 为根做仓库相对寻址"的布局约定（B-E003），因此 engine 内部代码里的旧式相对路径属有效约定，与项目侧自仓库根重复拼 engine 前缀的缺陷性质不同。

## 五、写作产物与批准口径一致性

读法申明（定义书 §2.3 顺序）：先全文读毕写作层（14/17 全读、3 件定点，第一节），再按定义书权威序次逐控制对照；对照基准为批准报告【当前权威口径】，被对照物为 2026-06-07 旧正文与写作素材【历史/旧链口径】——故下列判定均为"旧稿对主题方向的支持度"，不构成新版实现合格性。控制序次：主体/记忆、当前感官、权限与现实行动、亲属同意、信息分层、关停/备份、开放边界，关系另列附加核对。

1. **主体/记忆**：批准 L277–289（记忆非录像、主观重构）＋L382–419（新主体不归给顾衡）；旧正文 L183–205 记忆回放被重构（像素采样、郑柏舟 82% 匹配），L381 与 L474–476（L474 引出、L476 作结"这是我的。"）呈现自我区分。判定：**局部主题支持（限旧稿）**——"新主体自我区分"的主题方向有旧稿支撑；但其记忆机制（像素采样百分比匹配）是另一套设定，与批准口径"记忆非录像、主观重构"机制不同，登记为旧稿设定差异，待新版按批准口径重写，不给整行贴当前权威标签。
2. **当前感官/信息来源**：批准 L241/L289/L389（无当前视听，输入限于操作数据）；旧正文 L245/L271 击键节奏/压力传感属操作数据，合规。**差异登记**：L335/L341 R-07 内部评估使用"会议室中的沉默——十秒"，而 K8 会议发生于实验楼内会议室（`writing/spaces/meeting-room.md` L17：数字生命实验室内部、无窗），会议内容无任何向 R-07 的文字传递（`writer-shenyu.md` L214："K8：她在会议室选择沉默——它在上方不知道她在保护它"）——旧稿内部对同一事件一处引用、一处否认可知，该数据来源未交代，且素材与旧正文相互矛盾。判定：**局部合规＋一处未解释的信息来源缺口与旧稿内部矛盾**（登记，不定性为越权）。
3. **权限与现实核验**：批准 L295–315/L468–475/L524–531（情报经专家、硬件与授权链复核，现实团队完成阻断）；旧稿为另一故事（无气象武器袭击主线），L359–369 遇袭轮廓与档案关联、L464–476 读取记录均未展现该处置链。判定：**无对应实现（待新版迁移）**——旧稿无此情节线，不能记为"支持"。
4. **亲属同意**：批准 L423–449（程予安同意边界、周岚非情报筹码）；旧正文与写作 17 件对"程予安""周岚"字面检索均 0 命中（writing 中"妻子"仅无名提及，`writer-qianxu.md` L17/L152 对妻子的承诺不披露）；旧稿人物为郑柏舟/纪菱/陆远代际（`writer-qianxu.md` L1/L15：前序＝灰鸟/陆远）。判定：**未找到同名对应**——仅能证明无反面工具化段落，不能证明亲属主题合格；无法判断。
5. **信息分层**：批准 L253/L315（行动层/原因层分层交付）；旧正文 L407 私密层"保留"与 L417"访问权限：开放——无限制"在旧稿内部即存在分层与开放的张力，未见批准口径的分层交付实现。判定：**无对应实现/旧稿差异**。
6. **关停/备份**：批准 L271/L283/L396/L510–517/L608–615（外部执行、无活动备份、静态保管不保证连续性）；旧稿为自主终止——`writer-R07.md` L74"然后它关闭了自己的处理循环。"、L91"它启动了关闭序列。不是外部指令——是内部选择。"、L249 K9 自主关闭，`writer-zhengbozhou.md` L239 郑柏舟的话成为它终结决定的外部催化。**差异登记（成立，属历史）**：旧稿＝自主终止；七月 `duanxian-narrative-contract.md` L26"无自行终止权限……让沈逾执行终止"亦属【历史/旧链口径】——`novel-goals.md` L93–97 明示该契约为历史且未绑定 P1，不得升格为现行规范；当前批准口径的关停要求以批准报告 L510–517 等为准。判定：**已登记的历史差异；当前无新版写作可判**。
7. **开放边界**：批准 L327/L608–615（法律身份、连续性与互信保持开放）；旧正文 L480–508 结尾留有认知问题与空缺，仅局部留白（法律身份/重载/互信未全覆盖）。判定：**局部留白/无对应**。
8. **关系（附加核对）**：批准 L147/L169/L382–419（新感情不属顾衡、不写旧爱复活）；旧正文未见反向改写，但沈逾在旧正文仅出现 1 次，新感情线无正面实现；前序素材属另一代际（灰鸟/陆远）。判定：**无对应实现/无法判断**，不记为"已实现"。

- 汇总（改写前稿"五类获支持"的过度归纳）：七类控制中 **0 类**可称"当前权威口径下的实现支持"；**2 类**为旧稿局部主题方向支持（主体/记忆、当前感官——各带登记差异）；**4 类**无对应实现（权限与现实核验、信息分层、开放边界、关系）；**1 类**（亲属同意）未找到同名对应；**1 类**（关停/备份）为已登记的历史差异。写作产物整体属 2026-06-07 旧链，不能作为七控制的实现证据，仅能作为主题方向与素材底稿【历史/旧链口径】。
- 迁移线索：`writer-qianxu.md` L1/L15"灰鸟（陆远）"、L153"'陆远'不产生叙事焦点——K2 元数据中出现一次"属旧链人名设定（B-E027），与批准口径人物表并存，作历史素材对待，不自动进入新版。样片中人物的误解不等于作者叙述违规（B-E011 `characters.constraints`："人物可能误解，但知情、权限、选择与后果必须分开。"）。
- 样片非权威与误读处理：批准报告内三个试读场景为非权威体验样片，其中雨声、动作等局部写法不得补为新设定（`final-delivery-contract.md` L26–30 的 P1 权威边界，B-E044）；本报告未将任何样片措辞用作故事事实；一致性判定一律回退到批准报告的要求行核对。

## 六、代码层与流水线契约可用性

**项目 CLI（B-E028，全文 1082 行）**：`duanxian/conception-production/run.py` L14 `ROOT` 已解析到 `<仓库根>/engine`；但 `_s1_runtime`（L51–55）、STAGE_SPECS（L58–99）与 Q1/P1 装载（L123–135）共 7 条路径仍写 `"engine/skills/<skill>/scripts/run_v2.py"`（S1/W1/E1/T1/C1/Q1/P1），拼接后为 `<仓库根>/engine/engine/skills/…`——7 条组合路径在 BASE 全部不存在；去掉重复前缀后的正确路径全部存在（novel-storyline-architecture-designer、novel-world-model-designer、novel-environment-system-designer、novel-event-timeline-designer、novel-character-system-designer、novel-conception-reviewer、novel-conception-deliverable-assembler 七个技能目录逐一核对）。
- **失效机理**：`_load_stage_runtime` L43–44 仅在 spec/spec.loader 为 None 时抛 `RuntimeError("cannot load stage runtime: …")`，实际装载读取在 L47 `spec.loader.exec_module(module)`。以 `python3 -I` 仅标准库观察（未 import 仓库代码）：`spec_from_file_location` 对不存在的 `.py` 仍返回 spec 与 SourceFileLoader，失败发生在其后 `exec_module` 抛 `FileNotFoundError`。故正确表述为"正常冻结布局下目标源码缺失导致加载不可完成"【推断】（静态分析，未运行 CLI）。
- 影响范围：7 条 runtime 装载路径同型受影响；需要装载对应 runtime 的 issue/start/submit/finalize 子命令不可完成装载，不泛称每条子命令都在入口失败。

**CLI 测试（B-E029）**：`tests/test_attempt_selection_cli.py`、`test_line_sequence_review_cli.py`、`test_topology_review_cli.py` 三件同型：L12 `ROOT=parents[4]`、L13 `ENTRYPOINT=ROOT/"projects"/"duanxian"/"conception-production"/"run.py"`，指向仓库外旧布局。按上述标准库观察，L19–20 的 spec 断言不一定失败，实际失败点在其后 L23 `exec_module`【推断】。

**驱动与迁移（B-E030）**：`duanxian/testing/run_duanxian_conception_v2.py` L16–23 RUN_ID 环境变量默认 `20260802-04`——默认值可被覆盖只说明可配置，实际八月运行是否使用该入口、如何多轮迭代不可由代码与命名推出；L27–35 迁移读取旧根 `engine/projects`；L43–55 三段回退 ENGINE→ENGINE.parent→NOVEL。驱动代码仅证明能力设计，**不证明任何实际运行历史**【推断】。

**runtime 存量（B-E031）**：`engine/harnesses/novel-conception-autonomous/runtime/` 直接 `.py` 19 件（分母含 `__init__.py` 189 行，如排除则为 18——前稿"18 模块"与"20446 行"分母不一致，统一为 19 件 20446 行）、共 20446 行；行数前列：production_orchestrator 8133、production_store 2706、baseline 2184、production_coordinator 1388、conception_revision 1153、h1_completion 1073。行级闭环样本：production_orchestrator.py L3466–3497 `initialize_production_run`；production_store.py L617–620 `ensure_uninitialized` 防重复初始化；author_decision.py L80–88 `_validate_sealed`＋L202–255 P1 不匹配拒绝；return_routing.py L147–156 责任阶段退回。

**契约与 schema（B-E032）**：`engine/docs/ai-novel-workflow/contracts/autonomous-v2/` 为 **32 份 `.schema.json`＋`contract-index.md`＝33 个文件**；前稿"33 份 JSON Schema"计数错误，更正为 32 schema＋1 索引。

**四 harness 成功/拒绝/退回链闭包（RF01 补全；静态定位，未运行）**：
- novel-conception-interview（92 件/0 测试）：`README.md` L3–13 定位其承担跨技能顺序、证据与批准门组织——0 测试不推出"无门禁"，仅登记测试缺位。
- novel-conception-autonomous（107/25）：成功链＝production_orchestrator.py L3466–3497（取锁→`ensure_uninitialized`→revision-000→持久化）；拒绝链＝production_store.py L617–620（非空残留拒绝初始化）＋author_decision.py L80–88/L202–255（签封校验、P1 指纹不匹配拒绝）；退回链＝return_routing.py L147–156（按责任阶段路由）。
- novel-hld-autonomous（152/12）：manifest.yaml 13 阶段 HB0–HF1 含 author_gate 必经（B-E037）；releases 0.1.0 declaration-only/not-run（B-E038）。
- kun-workshop-intranet-delivery（53/0）：`README.md` L3–12 内网交付边界（云资源、生产数据与发布需授权，B-E047）。

**五 validator 与测试闭包（RF01 补全；行号为 def/关键行，静态核对，未运行）**：
- `validate_proposal_contract.py` L12–18 ↔ `test_validate_proposal_contract.py`：正例 L18/L35；拒绝例 L7（短语声明）、L41/L66（同 claim 漂移）、L91、L119/L130（依赖环/非依赖引用）、L150/L161/L174、L190、L205（Agent pass 带 P1 风险）、L244（空收敛日志）、L262（三次尝试重构触发）。
- `validate_prd_contract.py` L13–23 ↔ `test_validate_prd_contract.py`：正例 L437/L457/L472/L579/L590；拒绝例 L464/L477/L486/L495/L504/L522/L570/L596/L608/L624/L639/L660 及 upstream/HLD 扩张族 L689–L816。
- `validate_design_tasks.py` L14–43 ↔ `test_validate_design_tasks.py`：正例 L24/L31/L39/L46/L77/L85/L93/L101/L115/L122/L166/L177/L188/L223/L230；拒绝例 L60/L72/L138/L145/L154/L199/L211。
- `validate_hld_contract.py` L13–17 ↔ `test_validate_hld_contract.py` L1185–1193 正例、L1418–1420 文本包含检查、L1500–1520 raises 拒绝。
- `validate_hld_release.py` L192–194（root-not-cwd）↔ `test_validate_hld_release.py` L80–95（untracked/staged）、L130–160（校验和/快照/状态门）。
- **IC004 边界反例**：validate_hld_contract.py L13–17 `ROOT=parents[1]` 相对 `engine/` 根有效（`engine/README.md` L27 同约定）；validate_prd_contract.py L16–22 `resolve_recorded_path` 更在运行时把 `docs/superpowers/runs/*` 迁移解析到 `duanxian/design/runs/*`——**代码内含旧串不等于失效链接**，engine 内部旧式相对路径不是缺陷，缺陷仅限自仓库根再拼 engine 前缀的调用点。

**`duanxian/testing/` 归类（17 件）**：运行驱动 1 件（run_duanxian_conception_v2.py）；run08 阶段构建辅助 3 件（build_run08_hi1_000230/000237/000238）；阶段构建与装配脚本 10 件（c1/e1/t1/w1 构建器、q1 语义与交接、h1 计划/片段/HTML/装配）；评审生成 1 件（generate_duanxian_editorial_review.py）；树内测试 2 件（test_c1_determinism.py、test_duanxian_title_provenance.py）。该组为项目侧测试与辅助资产，存在不等于通过，本轮仅做只读归类，未执行。

**技能存量与分类闭包（RF06 更正，B-E033）**：skills 一级目录 82 个、各含 SKILL.md。按前缀/职能分类闭合：novel-hld-* 21（含 Legacy 标记的 novel-hld-writer 与交接提示涉及 14 个既有失败的 novel-hld-lld-readiness-evaluator，B-E040）＋novel-conception-* 6＋novel-prd-* 6＋novel-proposal-* 3＋访谈/intake 族 8＋写作族 4（character/scene/space/lld-writer）＋开发基线 2＋通用构思设计/评审 32；21＋6＋6＋3＋8＋4＋2＋32＝82。run.py 路由的 7 个构思生产技能（storyline-architecture/world-model/environment-system/event-timeline/character-system/conception-reviewer/conception-assembler）已跨文件核对。树内 `test_*.py` 56 件分布于 **28 个**技能目录（15 个 novel-hld-*＋6 个 novel-conception-*＋baseline-preparer、environment-system、event-timeline、interview-b0-migrator、storyline-architecture、world-model、character-system）；其余 54 个目录无测试——纯提示型技能（如 novel-character-designer，SKILL.md 仅提示式职责）无脚本无测试，不因此自动构成缺陷。**撤回前稿"一技能一契约一测试"的全称表述**（56/82 的分布不支持该全称）。**计数漂移（IC003）**：`README.md` L5 与 `engine/README.md` L9 写"81 个技能"，实测 82（B-E036）。zip 31 个、唯一 sha256 23 个、8 对重复（interview 1.0.0 releases＋dist 六件、autonomous 1.0.0 codex=source、harness releases codex=source）（B-E034）。

**字节稳定（B-E005/B-E006）**：根 `.gitattributes` L3–23 模式为 `harnesses/novel-hld-autonomous/**/*`、`skills/novel-hld-*`、`skills/novel-development-baseline-preparer/**`——均无 `engine/` 前缀，保留旧根布局；对 3 个真实路径执行 `git check-attr --cached text eol`，六项属性全部 `unspecified`。结论：规则文本承载历史意图，**当前布局下未生效**；登记为未生效的配置缺口，本轮不修改 `.gitattributes`【推断→未完成项】。

**历史与标记类存量**：`engine/skills/novel-hld-writer/SKILL.md` L3–5 标 Legacy（B-E040）；engine/testing 契约测试 L108/L130"production never synthesizes this gate"（作者门不可由生产侧合成）＋e2e L112–125 忠实度 fixture（语义归属见第三节，B-E041）；`engine/skills/novel-interview-b0-migrator/SKILL.md` L2–10 两条明确决定路径（"Silence…satisfies neither route"）＋runtime `migration_handoff.py` L1–6（fail-closed/waiting_author 永非 valid）（B-E042）；`engine/harnesses/novel-hld-autonomous/releases/0.1.0-acceptance.json` declaration-only（42 bounded、15 skills、18 tokens、stable_major False、4 suites、5 eval cases）＋`0.1.0.md` L3–5【历史/旧链口径】（B-E038）；`.zcode/plans/plan-sess_316609e2-5263-4909-a27a-c47b17476339.md` 记录 engine 内部旧根布局为当时设计状态（B-E046）。

**测试与运行证据边界**：本轮未执行任何测试（作业契约禁用）。编排交接提到的 engine/tests 12 个、novel-hld-lld-readiness-evaluator 14 个既有失败属交接提示，非本轮实测——维持边界：测试存量≠通过；负例预期拒绝≠测试失败；历史日志≠当前基线事实【流程规范】。

## 七、实现程度总评与未决事项

| 对象 | 程度 | 依据与边界 |
| --- | --- | --- |
| 构思批准与留存绑定 | 已完成（限定：approved/ready＋3 对象重算一致） | 第三节；不含全链 validator 重放 |
| P1 机器本体/handoff/运行态留存 | 缺口（留存类） | 三 basename 零命中＋账本设计不入库；获取/重验渠道建议见 IC008【未完成项】 |
| 旧 HLD run（2026-07-13） | 记录内四分：机器证据（manifest/final-hld-package 记录）／语义证据（integrity 报告 fail＋pending）／消费证据（无）／作者证据（gate-report 列人审门，未见通过记录） | 第四节；记录内状态不外推至今 |
| 旧链隔离 | 历史遗留（词表零命中已核——限第四节词表；语义隔离未逐事实核验；迁移责任仍在） | 第四节词表与限定 |
| 新版 HLD/LLD/写作现实进度 | 无法判断 | 留痕未见＋账本不入库；不写"未运行/未开工" |
| 项目 CLI 可用性 | 部分完成（静态断裂） | 7 条 runtime 路径；静态结论，非实测失败 |
| 引擎工具链（harness/validator/schema/测试存量） | 部分完成（存量与机制静态可定位——四 harness 成功/拒绝/退回链与五 validator 正负例分布见第六节闭包；发布为历史或候选态；未经全量逐字阅读与运行验证） | implementation-candidate＋Legacy 标记 |
| 文档一致性 | 部分完成（81/82、章节号、旧路径引用） | IC003/IC004/IC005 |

- 不设全仓完成百分比；以上分对象结论与各节一致。下一证据需求及理由：①编排方提供 rint2 阶段执行记录（命令、退出码、忽略区写入范围、模型重派记录）——核验红线遵守与自检真实性的共同输入；②Owner 裁决机器本体留存与获取渠道——决定 IC008 按缺陷立项还是渠道建设；③新版 HLD 人审门记录——判断"构思之后"阶段是否推进的**必要**记录（非"唯一合规依据"——完整判断还需同版机器包复验与消费证据）；④路径修复须在授权后以 CLI selftest 与 validator 实测复核，静态复验只能确认路径存在与拼装正确。

## 八、ISSUE 候选清单

每条含问题、应然依据、实际证据、影响、版本、强度、根因、建议、验证、归并；均未创建 ISSUE、不预填编号。已具证问题与线索/建议分列。

- **B-IC001**（已具证，强）run.py 七条 runtime 路径重复 engine 前缀。应然：CLI 应能在冻结布局下装载各阶段 runtime（`run.py` L14 自身 ROOT 约定）。实际：`duanxian/conception-production/run.py:L14,L41–55,L58–99,L123–135`；7 条组合路径全不存在、正确路径全存在。影响：S1/W1/E1/T1/C1/Q1/P1 装载不可完成（静态）。版本：当前。强度：静态可定位。根因：目录重构未同步路径前缀【推断】（静态分析，未运行验证、未取证历史提交）。建议：去除重复前缀或改为 ROOT 相对拼装。验证：修复后 `python3 -I` 两步装载观察＋获授权 selftest。归并：与 IC002/IC004 同族（根路径迁移）。
- **B-IC002**（已具证，强）3 件 CLI 测试 ENTRYPOINT 指向仓库外旧布局。应然：测试应自足定位被测入口。实际：`duanxian/conception-production/tests/test_attempt_selection_cli.py:L12–13,L19–23` 及 `test_line_sequence_review_cli.py`、`test_topology_review_cli.py` 同型（parents[4]＋projects 拼装）。影响：测试无法在当前布局定位入口；spec 断言不一定失败，失败点在 exec_module。版本：当前。强度：静态可定位。根因：同 IC001【推断】。建议：改仓库相对定位。验证：静态路径核对＋获授权 pytest。归并：可并入 IC001。
- **B-IC003**（已具证，中）技能计数漂移。实际：`README.md:L5`、`engine/README.md:L9` 写 81，BASE 实测 82（B-E033/B-E036）。应然：导览计数与树一致。影响：误导存量认知，不损运行。版本：当前。强度：直接留存。根因：新增技能后未同步文档【推断/未知】——冻结树只能证明计数不一致，不能证明历史因果。建议：两处改 82 或去掉具体数字。验证：一级目录计数复跑。归并：独立文档缺陷。
- **B-IC004**（已具证，中）全树旧根路径引用，按解析基点分类登记（RF07 重写）。实际：字面串 `docs/superpowers` 全树 79 文件 219 行——duanxian 31 文件 88 行＋engine 47 文件 119 行＋根 1 文件 12 行（`.zcode` plan L5/7/29/30/31/42/43/44/48/49/62/64），分项闭合 88＋119＋12＝219（B-E045）；该计数是**文本命中数**，不是失效链接数。三类解析基点：(a) `duanxian/writing/` 17 件各 1 个反引号 LLD 旧路径（B-E027），替换为 `duanxian/design/specs/lld/` 后均可定位——真失效待修；(b) engine 内部代码/文档相对 engine/ 根的引用——按 `engine/README.md:L27` 约定有效，且 `validate_prd_contract.py` L16–22 `resolve_recorded_path` 在运行时迁移解析 `docs/superpowers/runs/*`→`duanxian/design/runs/*`，含旧串不等于失效；(c) 历史文本/计划中的旧路径叙述（`.zcode` plan、旧 specs/runs 记录）——历史事实，非坏链。应然：引用应按其解析基点可解析（素材/文档类指向现行权威文档；代码类按运行时寻址约定）。影响：(a) 类损害文档与素材可解析性；(b)(c) 类无影响。版本：历史遗留兼当前。强度：静态可定位。根因：目录重构未同步引用【推断】（"f7ac2db 一族"为前稿推测，本轮未取证历史提交，撤回确定性表述）。建议：按 (a)(b)(c) 分类处置，仅修 (a)。验证：grep 抽样回放＋engine 例外人工复核。归并：IC001/IC002 与 `.gitattributes` 前缀缺失（B-E005/B-E006）同族，可合立一项。
- **B-IC005a**（已具证，中）HLD 章节号错位。实际：`duanxian/writing/characters/2026-06-07-writer-R07.md:L13–16` 引 §10.2/10.3/10.4/10.6/10.8，现 HLD 风格章为 §9（`duanxian/design/specs/2026-06-06-hld-digital-life-novel.md:L312–339`；L10 记 v4.0 于 2026-06-07 重构收束）。应然：写作素材引用应可解析到现行权威文档（流程可追溯要求）。影响：写作素材引用悬空。版本：历史遗留。强度：静态可定位。根因：v4.0 重构改号未同步引用【推断】。建议：**按内容重新对照**——v4.0 重构后小节编号与结构已变，不能机械减号改引 §9，须将 L14 所引五个小节与现 §9 各小节逐一对内容后改引或加迁移注。验证：章节内容逐一核对。归并：并入 IC004 迁移族。
- **B-IC005b**（线索，待取证）部分 writing 素材无 frontmatter。与 005a 根因不同，且未见明确规范要求素材必须带 frontmatter，降为线索：须先取证规范依据再定是否立项。
- **B-IC006**（已具证，中）HLD-TRACE-CLOSURE P1 open。实际：`duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/artifacts/12-hld-integrity-report.md:L25,L32–34,L57–58`；同 run `final-hld-package.md:L20–22`。应然来源：HLD 规范与 manifest 定义的 LLD 准入条件（integrity report 即该 run 的准入核验产物）。影响：该 run 记录内 LLD 准入被阻。版本：历史遗留（记录属 2026-07-13）。强度：直接留存。根因：trace 未逐字段绑定（记录自述）。建议：新版 HLD 流程接管时关闭或显式作废该门槛——验证落点为新版 HLD integrity 复核记录。表述边界：仅判定冻结记录仍 open，现实处置不可知（检索范围：全树 `git grep`，仅 2 文件命中）。归并：独立或与 IC007 同 run 记录族。
- **B-IC007**（已具证，中）v2.0/v3.0 标签混用。实际：integrity 报告 L33"v2.0 is newly presented after material world reconstruction."而同 run `manifest.md` L12–15 定 v3.0 唯一事实源；`canonical-world-facts-v2.0.md` 与 `v3.0.md` 并存（B-E023）。影响：版本指称混乱，不改变 v3.0 权威。版本：历史遗留。强度：直接留存。根因：同 run 内报告与 manifest 口径未对齐【推断】。建议：以 manifest 为准，后续报告统一版本指称。验证：两文件对读。归并：可并入 IC006。
- **B-IC008**（重新定位：留存政策已明示，缺的是获取/重验渠道；RF07 重写）机器本体获取与同版复验渠道缺位。实际：`conception-completion.json` `/p1_manifest`、`/development_handoff`、`/run_state` 等 Pointer 引用的本体未入库（B-E009）；三机器 basename 全树零命中（B-E048）。**政策侧已明示非未定**：批准 README L3"运行账本和历史尝试不纳入 Git"＋根 `.gitignore:L11–18` 设计性忽略（B-E004/B-E007）——撤回前稿"入库政策未定"的根因表述。应然依据：`final-delivery-contract.md` L26–30 定 P1 为构思事实最终权威，下游消费需要**同版**机器包（本体哈希对 manifest＋可消费性验证）。影响：下游无法在仓库内消费机器包、无法做同版复验。版本：当前（渠道缺位，不作违约断言）。强度：直接留存（缺口事实）＋引用值。根因：留存政策与下游复验需求之间的渠道缺位。建议：Owner 建立脱敏入库或受控留存库，并定义同版 package/hash/消费方向的重验渠道；**留存渠道与路径缺陷（IC001/IC004）分别处理**。验证：渠道建立后复跑 basename 检索＋同版哈希核对。归并：独立。
- **B-IC009**（建议性，弱）写作目录缺就地口径提示（RF07 限定重写）。"就地提示"指 writing 文件内提示历史口径/迁移状态的注记（如"本文档为 2026-06 旧链素材，现行权威见 conception-approved"）。实际：目录级声明已存在——`duanxian/README.md:L22–23` 历史链与批准优先、旧 proposal L276 非冻结说明（前稿"仓库缺历史口径声明"的判断已撤回）；且 17 件素材**均带文件内修订记录表**（版本/日期/作者/状态四栏，如 `writer-R07.md` L5–7、`scene-K1.md` L5–8）——缺的不是版本元数据，而是口径指向。剩余改进点仅：读者直达旧稿文件时无就地提示可能误当现行设定。建议：writing 目录加局部 README 或每件加一行迁移注。影响：低。版本：建议。强度：建议性归纳【推断】。验证：采纳后以评审确认。归并：可并入 IC004 迁移族或独立小项。

## 九、证据索引与自检记录

**唯一键索引（B-E→完整路径＋定位）**：

| 键 | 定位 |
| --- | --- |
| B-E001 | `duanxian/novel-goals.md`：六章（一 L7/二 L29/三 L53/四 L73/五 L105/六 L129）＋S01–S23 索引；动机 L9–21、读者 L23–27、流程 L29–51、状态 L49–51/L71/L113、七控制表 L79–89、叙述契约历史定位 L93–97、门 L133–151 |
| B-E002 | 根 `README.md:L5`（"81 个技能"声明）；全文 19 行读毕 |
| B-E003 | `engine/README.md:L9`（同 81）；L27（引擎内部以 engine/ 为根寻址）；全文 27 行读毕 |
| B-E004 | 根 `.gitignore:L11–18`（duanxian 运行账本目录忽略）；L19（.kunora/）；全文 19 行读毕 |
| B-E005 | 根 `.gitattributes:L3–23`（harnesses/novel-hld-autonomous/**/* 等旧根模式）；全文 23 行读毕 |
| B-E006 | `git check-attr --cached text eol` 三真实路径输出均 unspecified（命令记录） |
| B-E007 | `duanxian/conception-approved/README.md`：L3 留存声明；L18/L21 终态 revision-038 与 SHA；L22 completion SHA |
| B-E008 | `duanxian/conception-approved/author-decision.json`：/approval_scope、/decision、/run_id、/approval_record/text、/approval_record/event_seq=1、/approval_record/unresolved_items=[]、/human_review_package/*、/machine_package/* |
| B-E009 | `duanxian/conception-approved/conception-completion.json`：/status、/run_id、/author_decision/sha256、/p1_manifest、/development_handoff、/h1_html_manifest、/run_state、/stage_completions 九键（B0=774ac64a…、C1=83994b8d…、E1=b5d777c8…、H1=28ec088d…、P1=42e307d1…、Q1=4dab74a1…、S1=04d25ec9…、T1=6e462e88…、W1=dd719e9f…）、/validation/sha256（不含 event_seq/unresolved_items/review_path） |
| B-E010 | `duanxian/conception-approved/human-review-report.html`：sha256 见第三节；5 svg、0 外链、0 script |
| B-E011 | `duanxian/conception-approved/human-review-report.json`：/review_path 五项（kinds world 187/storylines 113/characters 89/fragments 175/decision 23；导航字段，非语义判定）、characters.constraints 等结构化字段 |
| B-E012 | `duanxian/conception-approved/human-review-report.md`：L147/L169、L241、L253/L315、L271/L283、L277–289、L295–315、L325–329/L327、L382–419、L423–449、L468–475、L510–517、L524–531、L608–615 |
| B-E013 | `duanxian/novel-text/2026-06-07-duanxian-novel.md`：L161、L183–205、L245/L271、L284–318（K8 会议段）、L335/L341、L359–369、L381、L407/L417、L464–476（L474 引出句、L476 引文）、L480–508 |
| B-E014 | `duanxian/design/workflow-docs/duanxian-narrative-contract.md`：L26、L28 |
| B-E015 | `duanxian/design/workflow-docs/duanxian-intent-card.md`：L15–17（动机问句）、L31（目标读者未指定） |
| B-E016 | `duanxian/design/specs/2026-07-05-duanxian-proposal.md`：L39、L45–46、L265–267（§18 门类）、L276 |
| B-E017 | `duanxian/design/specs/2026-06-06-hld-digital-life-novel.md`：L10（v4.0 收束日期 2026-06-07）、L312–339（§9 风格章） |
| B-E018 | `duanxian/design/specs/2026-06-06-lld-digital-life-novel.md`：L36–39 |
| B-E019 | `duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/manifest.md`：L12–15 |
| B-E020 | 同 run `artifacts/12-hld-integrity-report.md`：L25、L32–34、L57–58 |
| B-E021 | 同 run `artifacts/final-hld-package.md`：L20–22 |
| B-E022 | 同 run `gate-report.md`（下一道人类评审门） |
| B-E023 | 同 run `canonical-world-facts-v2.0.md`、`canonical-world-facts-v3.0.md`（沈逾/顾衡/周岚命中 5/9/11） |
| B-E024 | `duanxian/design/runs/lld/2026-07-08-duanxian-lld-workflow-blocked/manifest.md` |
| B-E025 | `engine/docs/superpowers/runs/design/2026-07-08-hld-lld-design-task-dispatch/manifest.md` |
| B-E026 | `duanxian/README.md`：L3、L12、L22–23 |
| B-E027 | `duanxian/writing/` 17 件（14 全读＋3 定点）；`writer-R07.md` L5–7（修订表）、L13–16、L74、L91、L249；`writer-qianxu.md` L1/L15/L153/L17；`writer-shenyu.md` L214；`writer-zhengbozhou.md` L239；`spaces/meeting-room.md` L17 |
| B-E028 | `duanxian/conception-production/run.py`：L14、L41–48、L51–55、L58–99、L123–135、L921–944 |
| B-E029 | `duanxian/conception-production/tests/test_attempt_selection_cli.py` L12–13、L19–23；`test_line_sequence_review_cli.py`、`test_topology_review_cli.py` 同型 |
| B-E030 | `duanxian/testing/run_duanxian_conception_v2.py`：L16–23、L27–35、L43–55 |
| B-E031 | `engine/harnesses/novel-conception-autonomous/runtime/`：19 `.py`＝20446 行；production_orchestrator.py L3466–3497；production_store.py L617–620；author_decision.py L80–88、L202–255；return_routing.py L147–156；migration_handoff.py L1–6 |
| B-E032 | `engine/docs/ai-novel-workflow/contracts/autonomous-v2/`：32 `.schema.json`＋contract-index.md |
| B-E033 | `engine/skills/` 82 一级目录各含 SKILL.md；分类闭包 21＋6＋6＋3＋8＋4＋2＋32＝82；test_*.py 56 件分布 28 目录 |
| B-E034 | zip 31 个、唯一 sha256 23、8 重复对（interview/autonomous/harness releases 族） |
| B-E035 | 四 harness 文件数：interview 92/0、autonomous 107/25、hld-autonomous 152/12、kun-workshop 53/0；成功/拒绝/退回链闭包见第六节 |
| B-E036 | 实测 82 对 `README.md:L5`、`engine/README.md:L9` 的 81 |
| B-E037 | `engine/harnesses/novel-hld-autonomous/manifest.yaml`：L1–27、L44–48 |
| B-E038 | `engine/harnesses/novel-hld-autonomous/releases/0.1.0-acceptance.json` 与 `0.1.0.md` L3–5 |
| B-E039 | `engine/scripts/validate_{design_tasks,hld_contract,hld_release,prd_contract,proposal_contract}.py`；对应 `engine/tests/test_validate_*.py` 正负例行号闭包见第六节 |
| B-E040 | `engine/skills/novel-hld-writer/SKILL.md`：L3–5 |
| B-E041 | `engine/testing/test_conception_autonomous_v2_contracts.py` L108/L130；`test_conception_autonomous_v2_e2e.py` L112–125（忠实度 fixture，非作者门） |
| B-E042 | `engine/skills/novel-interview-b0-migrator/SKILL.md`：L2–10 |
| B-E043 | `engine/docs/ai-novel-workflow/development-phase.md`：L137–152 |
| B-E044 | `engine/harnesses/novel-conception-autonomous/docs/final-delivery-contract.md`：L26–30、L64–79 |
| B-E045 | 字面串 `docs/superpowers` 全树逐行 grep：79 文件 219 行＝duanxian 31/88＋engine 47/119＋根 1/12（`.zcode` plan L5/7/29/30/31/42/43/44/48/49/62/64）；含历史说明文本与 engine 内有效相对路径，非 219 个失效链接 |
| B-E046 | `.zcode/plans/plan-sess_316609e2-5263-4909-a27a-c47b17476339.md`（89 行全文读毕） |
| B-E047 | `engine/harnesses/kun-workshop-intranet-delivery/README.md`：L3–12 |
| B-E048 | 三机器 basename 全树零命中（`git ls-tree -r --name-only` 全名单精确匹配） |
| B-E049 | 树总量 1444＝根 6＋duanxian 148＋engine 1290；覆盖账 29/141/1274 互斥闭合 |
| B-E050 | 词表双向检索：7 旧词×3 批准文件＝0（K1–K8 亦 0）；6 新名×canonical v3.0＝0（v2.0 同）；沈逾/顾衡/周岚在 v3.0 命中 5/9/11——结论限词表；HLD-TRACE-CLOSURE 全树 2 文件 |

**自检记录（真实时序）**：定义书 §6.1 文件检查（UTF-8、6000–12000 中文字、九节、五口径、BASE 串、秘密/占位模式）在**提交前**对本文件运行，通过后连同 `git status --short --untracked-files=all`、`git diff --check` 作为提交前置门；**范围检查**（BASE..HEAD 仅本报告文件新增/修改、单亲提交、树净、HEAD 内文件与工作树一致）在**提交后**对完整候选运行，其结果连同完整提交号、报告 SHA-256、远端 SHA 写入交付交接，本报告不预写该通过状态。
- 本轮执行边界：未运行仓库 CLI/pytest/validator/构建；除最终推送外无网络动作；未向忽略区写入业务文件；凭据零打印零写入，仅经命令替换引用并脱敏输出。
- 剩余限制：全量逐字阅读未完成（第一节账目如实保留）；机器本体不可复验（第三节）；现实运行史不可判断（第四节）；以上缺口均不反向推断为"未发生"。
