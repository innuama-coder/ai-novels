# 《断线》实施审视报告（工作项 B·修正轮 r2）

- 内容基线 BASE：`92573f1cca40f37cee04d2beb8708ff33ba603d6`（冻结只读；本报告全部证据取自该树）。
- 规范输入：B 定义书 rdef-001（完整 SHA `c423216ef9f8bbe8a9846b1a4d877d298a9334f7`）；A 基准 gdef-001（`68ec7c0a…`）与目标拟人化总结（`ac7f045a…`）仅作目标口径基线，不引为新故事事实来源。
- 方法与执行边界：只读静态审视（`git ls-tree/show/grep`、本地 SHA-256 重算、`python3 -I` 标准库行为观察）；本轮未运行仓库 CLI、pytest、validator 或任何构建，未访问仓库本体之外的网络资源。
- 本稿为按独立验收 racc-001 §7 F01–F10 的全量修正稿；修正仅落本文件，不改动任何既有源文件与历史证据。

## 一、审视范围与证据基线

**总量与分层（B-E049）**：BASE 跟踪树共 1444 个文件：根层 6、`duanxian/` 148（147 个常规路径＋1 个带引号中文名 `duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/HLD-断线设计稿.md`）、`engine/` 1290（docs 83、skills 669、harnesses 404、scripts 5、tests 6、testing 10、tasks 112、README 1）。

**覆盖账（F01 要求，按层闭合）**：

| 层（总数） | 全文已读 | 定点/行级 | 结构·清单·哈希核对 |
| --- | ---: | ---: | ---: |
| 根层（6） | 3 | 2 | 1 |
| duanxian（148） | 8 | 64 | 76 |
| engine/docs（83） | 0 | 14 | 69 |
| engine/skills（669） | 0 | 45 | 624 |
| engine/harnesses（404） | 0 | 24 | 380 |
| engine/scripts（5） | 0 | 5 | 0 |
| engine/tests（6） | 0 | 0 | 6 |
| engine/testing（10） | 0 | 3 | 7 |
| engine/tasks（112） | 0 | 0 | 112 |
| engine/README.md（1） | 0 | 1 | 0 |
| 合计（1444） | 11 | 158 | 1275 |

- 全文已读（11）：批准目录 4 件（README.md、author-decision.json、conception-completion.json、human-review-report.md，JSON 为全字段走查）、`duanxian/novel-goals.md`、`duanxian/README.md`、`duanxian/novel-text/2026-06-07-duanxian-novel.md`（508 行）、`duanxian/conception-production/run.py`（1082 行，两段读毕）。
- 定点/行级（158）：批准 HTML/JSON 2；CLI 测试 3；`duanxian/testing/` 17（驱动细读＋其余入口归类）；`duanxian/writing/` 17（逐件核对反引号 LLD 路径，writer-R07/writer-qianxu 细读）；workflow-docs 7；design/specs 顶层 10；design/runs 6（07-13 HLD 链为主）；design-tasks manifest 1；`project-display-metadata.json` 1；engine 侧为 workflow 契约文档、runtime 关键模块、五 validator 入口、manifest/release 记录等。
- 结构·清单·哈希核对（1275）：非逐字阅读，含 superpowers 旧根引用专项 grep（79 文件 219 行，B-E045）、autonomous-v2 32 份 schema 结构核对（B-E032）、82 技能目录与 56 个 `test_*.py` 计数（B-E033）、31 个 zip 的 sha256 去重（B-E034）、tasks 112 件任务样例清单核对（样例不作生产成果）。
- **限制声明**：逐字全量阅读门未满足，本报告不自称满足；上表不把抽样或结构核对虚报为“全读”。结构核对类仅支撑计数、存在性与引用真实性结论，不单独支撑语义结论。抽样按定义书 §2.5 高风险全查＋确定性抽样执行；本轮已按 F01 扩读契约文档与 run.py 全文。
- 否定性断言与可复现性：本报告全部否定性断言（零命中、不存在、未见）附检索命令与范围——文件名类用 `git ls-tree -r --name-only` 全名单精确匹配；内容类用全树 `git grep` 或目录内全文扫描；“对象不在树”与“对象从未存在”严格分开表述。全部计数类结论可用标准命令对 BASE 复现。
- 权限与红线遵守：秘密零打印零写入，凭据仅经命令替换引用；未修改宪法、spec 与历史证据；运行账本按 `.gitignore:L11–18` 设计不入库（B-E004）【流程规范】，构成第三、四节“本体不可复验/无法判断”类限制的来源。

## 二、目标六问与实现对照

| 问 | 目标定位（路径） | 实现对象（路径） | 正向证据 | 缺口/反证 | 程度 | 强度 |
| --- | --- | --- | --- | --- | --- | --- |
| 要写一本什么小说 | `duanxian/novel-goals.md` 第一、五章：数字生命近未来长篇，危机闭环与伦理未决并立【当前权威口径】（B-E001） | 批准构思 `human-review-report.md` 故事章（B-E012）；`novel-text` 旧稿（B-E013）【历史/旧链口径】 | L277–289 记忆非录像、R-07 为新主体；旧正文 L464–476“评估完成。选择终止。” | 旧稿成稿于 2026-06-07，先于 2026-08-17 批准；与新版叙述契约 L26 存在差异（见第五节） | 构思层已完成（限定批准范围）；正文层属历史遗留 | 直接留存 |
| 为何写 | `novel-goals.md` 第二章：记忆、身份与照护责任落到人物选择（B-E001） | 批准报告 L251–255 原因层、L608–615 保管责任人（B-E012）；旧意图卡动机段 L7–11【历史/旧链口径】（B-E015） | 批准层主题证据完整 | 主题执行须待 HLD 与正文；旧意图卡只是主题来源，不得代作者宣布唯一伦理答案 | 构思层完成；执行层无法判断 | 直接留存／不足 |
| 为谁写 | `novel-goals.md` 第三章；`duanxian-intent-card.md` L31“目标读者未指定”【未完成项】（B-E001/B-E015） | 无商业画像产物 | 未决状态本身有直接记录 | 任何具体读者画像或渠道判断都是编造 | 未决（作者侧待定，非程序缺陷） | 直接留存（未决记录） |
| 怎么写 | `novel-goals.md` 第四章：构思 V2→开发基线→HLD→LLD→写作→分层评审【流程规范】（B-E001） | 构思链 approved/ready（B-E007/B-E008/B-E009）；引擎 HLD/LLD 工具链 implementation-candidate（B-E037） | 作者批准＋完成记录＋三层哈希账（第三节） | 开发 handoff 本体未留存（B-E009 引用不可复验）；`run.py` 七条 runtime 路径静态断裂（B-E028） | 构思段完成；HLD 及以后未证 | 直接留存＋静态可定位 |
| 写成什么样算合格 | `novel-goals.md` 第五章三门；`engine/docs/ai-novel-workflow/development-phase.md` L137–152 场景 80/70% 规则【流程规范】（B-E043） | 构思段三门留痕：作者门 approved（B-E008）、机器门引用一致（第三节）、语义门 `review_path` 五项（B-E009） | 三门在构思段均有记录 | 场景级评分零实例；validator 本轮未重放，历史通过不外推 | 构思段部分可复验；后续门无启用证据 | 引用值／直接留存分层 |
| 当前进度与断点 | `novel-goals.md` 第六章（B-E001） | 批准链 2026-08-17（B-E007）；`duanxian/README.md` L22–23 权威与状态声明（B-E026） | 批准与留存绑定成立 | 旧 HLD 停在 pending 人审【历史/旧链口径】（B-E019–B-E022）；新版 HLD 运行留痕未见且账本不入库，现实进度无法判断【未完成项】 | 构思完成；HLD/LLD/写作现实进度无法判断 | 直接留存＋不足 |

说明：矩阵逐行贴口径；“无法判断”均指冻结证据不可得，不指现实未发生（F04 口径）。

**逐问补充解读**：
1. “要写什么”——目标文档把主承诺定为“危机闭环与伦理未决同时成立”，不用胜利抵销失去（B-E001）；批准纲要以硬规则、开放边界两章承接该承诺（L295–309、L325–329）；旧正文结尾段方向一致，但其因果安排先于新版叙述契约，只能作历史参照，不得计为批准后的实现。
2. “为何写”——目标要求把记忆、身份与照护责任落到具体人物的选择与代价；批准报告的授权链（L468–475）与保管责任人（L608–615）给出人物级落点；写作层的责任刻画目前只存在于旧稿，新版执行尚未开始或未见留痕。
3. “为谁写”——未决。目标读者、年龄层与渠道均无作者决定，本报告不以沟通对象【推断】替代定位事实。
4. “怎么写”——流程规范要求每次交接携带来源、版本、约束与状态；构思段三份记录满足该要求；开发 handoff 本体未留存，使“构思→开发”交接的下游连续性不可复验，这是流程可用性的实际断点。
5. “写成什么样算合格”——三门与场景 80/70% 规则是“应当”而非“已经”；构思段可支撑作者门（批准记录）与机器门（引用一致层），语义门有结构化留痕但未做逐元素复验；场景级评分规则尚无任何实例记录可援引。
6. “当前进度与断点”——冻结证据只能确认：构思阶段完成并批准；旧链停在人类评审门；引擎侧 HLD 工具链为候选态。现实是否已推进新版 HLD 属树外事实，本报告不代答。

## 三、构思批准链与P1留存

【当前权威口径】批准事实：`duanxian/conception-approved/author-decision.json` `/approval_scope=conception`、`/decision=approved`、`/run_id=duanxian-conception-v2-20260811-18`、`/approval_record/text`＝“构思合格，完成提交并推送。”（B-E008）；`conception-completion.json` `/status=ready`、`/run_id` 与上一致、`/event_seq=1`、`/unresolved_items=[]`、`/stage_completions` 九键 B0,C1,E1,H1,P1,Q1,S1,T1,W1（B-E009）；批准 README 记 2026-08-17 作者批准、approved/ready（B-E007）。

**哈希三层账（F02：重算、引用一致、本体不可得分层）**：

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

- 三层分离结论：**记录批准**成立；**留存文件绑定**对 3 个重算对象成立；**全链重新验证未做**——validator 未重放、机器本体不在树，本报告不声称“合规/三投影一致已复验”【流程规范】。
- 版本号的分层含义：completion 内 `/run_state` 引用的是完成时点的运行态快照（`revision-037`），批准 README 的 final state 是运行收束后的终态记录（`revision-038`）；两处指向不同时点，属记录阶段差而非冲突。但两个状态本体文件均未留存，两层记录同样只能作引用值对待。
- 留存政策与缺口：批准 README L3“运行账本和历史尝试不纳入 Git”＋`.gitignore:L11–18`（B-E004/B-E007）。三个机器 basename（novel-conception-package.json、development-handoff.json、hld-completion.json）对 BASE 全量文件名列表精确匹配零命中（B-E048，检索规则：`git ls-tree -r --name-only` 全名单）——这是**留存缺口**，不证明机器链不存在，也不否定批准【未完成项】。
- 人审计数（`decision_controls=8`、`visual_models=5`、`fragments=3`、`drilldown_index=4602`、`reduction_ledger=4602`、`source_coverage=3924`、`review_path` 五项 `estimated_seconds` 187/113/89/175/23）与 HTML 结构（5 个 svg、0 外链、0 script）属**结构/离线核对**，不等于逐元素语义验证（B-E010/B-E011）。

## 四、HLD与LLD断点及旧链隔离

**版本时间线（均为冻结记录）**：

| 时点 | 对象与状态 | 口径 |
| --- | --- | --- |
| 2026-06-06 | `design/specs/2026-06-06-hld-digital-life-novel.md` L10 记 v4.0 收束，风格章现位于 §9（L312–337）（B-E017） | 【历史/旧链口径】 |
| 2026-06-06 | `design/specs/2026-06-06-lld-digital-life-novel.md` L36–39 反斜杠旧路径（B-E018） | 【历史/旧链口径】 |
| 2026-06-07 | `duanxian/writing/` 17 件＋`novel-text` 旧正文（B-E013/B-E027） | 【历史/旧链口径】 |
| 2026-07-05 | `design/specs/2026-07-05-duanxian-proposal.md` L39/L45–46 Agent pass、人审 pending；L276 非冻结声明（B-E016） | 【历史/旧链口径】 |
| 2026-07-08 | `design/runs/lld/2026-07-08-duanxian-lld-workflow-blocked/manifest.md` blocked/superseded 留痕（B-E024）；引擎侧 `engine/docs/superpowers/runs/design/2026-07-08-hld-lld-design-task-dispatch/manifest.md` 存在（B-E025） | 【历史/旧链口径】 |
| 2026-07-13 | HLD run：`manifest.md` L12–15 定 canonical v3.0 唯一事实源、人审前不得进入 LLD（B-E019）；`artifacts/12-hld-integrity-report.md` L25 HLD-TRACE-CLOSURE P1 open、L32–34 fail/pending_required/blocked_revision_required（B-E020）；`artifacts/final-hld-package.md` L20–22 fail/pending/blocked（B-E021）；`gate-report.md` 列下一道人类评审门（B-E022） | 【历史/旧链口径】 |
| 引擎侧 | `engine/harnesses/novel-hld-autonomous/manifest.yaml` L1–27：13 阶段 HB0–HF1、implementation-candidate、codex-only；L44–48 not-run（B-E037） | 【流程规范】＋【未完成项】 |

- 旧链隔离核验（B-E050）：7 个旧链专有词×3 份批准文件＝0 命中（旧链未渗入批准口径）；6 个新批准专名×`canonical-world-facts-v3.0.md`＝0 命中（新链未回写旧文档）；`HLD-TRACE-CLOSURE` 全树 `git grep` 仅 2 文件命中。`canonical-world-facts-v2.0.md` 与 `v3.0.md` 并存（B-E023），以 manifest 指定的 v3.0 为准。
- **F04 修正后的表述**：2026-07-13 的 open/pending 是**冻结记录内**的状态判定，不延伸为“至今无处置”——现实处置在树外不可知。同理，新版 HLD 在 BASE 未见运行留痕（账本设计不入库），因此**无法判断**新版是否运行过或是否开工，不得写“未运行/零运行/正文未开工”。
- 层级不外推：proposal 的 Agent pass、旧 HLD 的 pending、引擎 harness 的 implementation-candidate、2026-08-17 构思批准，四者分属不同层与不同版本，任一层状态不得替代另一层的准入判断【流程规范】。
- 命名与布局两则补充：其一，K1–K10 场景号、“陆远”等旧链专名只在各自来源内使用，未渗入批准口径（零命中核验见 B-E050，人物侧另见第五节）；其二，`engine/README.md:L27` 确立“引擎内部一律以 engine/ 为根做仓库相对寻址”的布局约定（B-E003），因此 engine 内部代码里的旧式相对路径属有效约定，与项目侧自仓库根重复拼 engine 前缀的缺陷性质不同。该 run 交付物 `HLD-断线设计稿.md` 为带引号中文名文件，计入 duanxian 的 148 个文件。

## 五、写作产物与批准口径一致性

七类高风险控制逐类双向对照（批准要求→写作片段；检索范围均为 `novel-text` 508 行全文＋`duanxian/writing/` 17 件逐件扫描）：

1. **R-07 新主体、非顾衡复生**：要求 L277–289“记忆非录像”＋隔离套间、L147/L169 关系界定（B-E012）；支持片段 L183–199/L201–205 记忆回放被重构、L474“这不是前序的记忆结构。这是我的。”（B-E013）。判定：支持。【当前权威口径】
2. **无当前视听/身体/现实行动权**：要求 L239–243 文字会话隔离室；`duanxian-narrative-contract.md` L28 无当前视听（B-E014）；写作侧 L407/L417 私密层为内部状态描写，检索范围内未见越权感官叙述。三个试读样片的局部感官写法按规范不晋升为新设定【流程规范】。
3. **现实核验与授权链**：要求 L295–309 专家/硬件/授权核验＋跨国处置、L468–475 授权链、L524–531 行动指挥由现实团队完成（B-E012）；检索范围内未见机器输出直接产生权限或自行完成现实行动的段落。判定：支持（限旧稿范围）。
4. **沈逾与顾衡/R-07 关系**：要求 L382–389/L396 新感情不属顾衡、不写旧爱复活（B-E012）；旧正文情感线未见反向改写。判定：支持。
5. **程予安/周岚主体性**：要求 L423–427 周岚非情报筹码、L445–449 程予安同意边界（B-E012）；检索范围内未见将亲属工具化的消费段落。判定：未见反例。
6. **关停且无活动备份**：要求 L510–517 关停不可逆、L271/L283 权限/封存（B-E012）；写作侧证据：正文 L464–476 自终止段（郑柏舟 82%、七节点）与 `writer-R07.md` L67–70/L88–91“它启动了关闭序列。不是外部指令——是内部选择。”（B-E027）。**差异登记**：旧稿写自主终止，新版契约 L26 定“无自行终止权限，以可能重载的希望让沈逾执行终止”（B-E014）——属旧稿与新版契约的差异，非当前违规；新版写作须按契约执行【历史/旧链口径→流程规范】。
7. **开放边界**：要求 L325–329 法律身份、连续性与互信保持开放（B-E012）；旧正文结尾未封闭这些议题。判定：支持。

- 迁移线索：`writer-qianxu.md` L1/L15“灰鸟（陆远）”属旧链人名设定（B-E027），与批准口径人物表并存，作历史素材对待，不自动进入新版。样片中人物的误解不等于作者叙述违规（B-E011 `characters.constraints`：“人物可能误解，但知情、权限、选择与后果必须分开。”）。
- 汇总：七类中 5 类获写作层支持、1 类未见反例、1 类登记为旧稿差异；写作产物整体属 2026-06-07 旧链，其一致性不能替代新版 HLD/LLD 之后写作的一致性判断【历史/旧链口径】。
- 样片非权威与误读处理：批准报告内三个试读场景为非权威体验样片，其中雨声、动作等局部写法不得补为新设定（`final-delivery-contract.md` L26–30 的 P1 权威边界，B-E044）；本报告未将任何样片措辞用作故事事实。文内人物对 R-07 身份或能力的误判属人物认知，不构成口径违规；一致性判定一律回退到批准报告的要求行核对。

## 六、代码层与流水线契约可用性

**项目 CLI（B-E028，全文 1082 行）**：`duanxian/conception-production/run.py` L14 `ROOT` 已解析到 `<仓库根>/engine`；但 `_s1_runtime`（L51–55）、STAGE_SPECS（L58–99）与 Q1/P1 装载（L123–135）共 7 条路径仍写 `"engine/skills/<skill>/scripts/run_v2.py"`（S1/W1/E1/T1/C1/Q1/P1），拼接后为 `<仓库根>/engine/engine/skills/…`——7 条组合路径在 BASE 全部不存在；去掉重复前缀后的正确路径全部存在（novel-storyline-architecture-designer、novel-world-model-designer、novel-environment-system-designer、novel-event-timeline-designer、novel-character-system-designer、novel-conception-reviewer、novel-conception-deliverable-assembler 七个技能目录逐一核对）。
- **失效机理（F07 修正）**：`_load_stage_runtime` L43–44 仅在 spec/spec.loader 为 None 时抛 `RuntimeError("cannot load stage runtime: …")`，实际装载读取在 L47 `spec.loader.exec_module(module)`。以 `python3 -I` 仅标准库观察（未 import 仓库代码）：`spec_from_file_location` 对不存在的 `.py` 仍返回 spec 与 SourceFileLoader，失败发生在其后 `exec_module` 抛 `FileNotFoundError`。故正确表述为“正常冻结布局下目标源码缺失导致加载不可完成”，撤回“必然抛 cannot load stage runtime”【推断】（静态分析，未运行 CLI）。
- 影响范围：7 条 runtime 装载路径同型受影响；需要装载对应 runtime 的 issue/start/submit/finalize 子命令不可完成装载，不泛称每条子命令都在入口失败。

**CLI 测试（B-E029）**：`tests/test_attempt_selection_cli.py`、`test_line_sequence_review_cli.py`、`test_topology_review_cli.py` 三件同型：L12 `ROOT=parents[4]`、L13 `ENTRYPOINT=ROOT/"projects"/"duanxian"/"conception-production"/"run.py"`，指向仓库外旧布局。按上述标准库观察，L19–20 的 spec 断言不一定失败，实际失败点在其后 L23 `exec_module`；撤回“fixture 的 spec 断言必失败”【推断】。

**驱动与迁移（B-E030）**：`duanxian/testing/run_duanxian_conception_v2.py` L16–23 RUN_ID 环境变量默认 `20260802-04`——默认值可被覆盖只说明可配置，实际八月运行是否使用该入口、如何多轮迭代不可由代码与命名推出；L27–35 迁移读取旧根 `engine/projects`；L43–55 三段回退 ENGINE→ENGINE.parent→NOVEL。驱动代码仅证明能力设计，**不证明任何实际运行历史**【推断】。

**runtime 存量（F06 修正，B-E031）**：`engine/harnesses/novel-conception-autonomous/runtime/` 直接 `.py` 19 件（分母含 `__init__.py` 189 行，如排除则为 18——前稿“18 模块”与“20446 行”分母不一致，现统一为 19 件 20446 行）、共 20446 行；行数前列：production_orchestrator 8133、production_store 2706、baseline 2184、production_coordinator 1388、conception_revision 1153、h1_completion 1073。行级闭环样本：production_orchestrator.py L3466–3497 `initialize_production_run`；production_store.py L617–620 `ensure_uninitialized` 防重复初始化；author_decision.py L80–88 `_validate_sealed`＋L202–255 P1 不匹配拒绝；return_routing.py L147–156 责任阶段退回。

**契约与 schema（F06 修正，B-E032）**：`engine/docs/ai-novel-workflow/contracts/autonomous-v2/` 为 **32 份 `.schema.json`＋`contract-index.md`＝33 个文件**；前稿“33 份 JSON Schema”计数错误，更正为 32 schema＋1 索引。

**五 validator 与测试（B-E039）**：`engine/scripts/` validate_design_tasks.py、validate_hld_contract.py、validate_hld_release.py、validate_prd_contract.py、validate_proposal_contract.py，与 `engine/tests/` 5 件 `test_validate_*.py`＋conftest 一一对应。行级样本：`engine/tests/test_validate_hld_contract.py` L1185/L1190 正例、L1418/L1500/L1512 拒绝例；validate_hld_release.py L192–193 root-not-cwd 机制及其测试 L80/L90/L130/L160；proposal/prd/design_tasks 校验器与测试入口行同法核对。**IC004 边界反例**：validate_hld_contract.py L13–17 `ROOT=parents[1]`，其路径相对 `engine/` 根有效（`engine/README.md` L27 亦约定引擎内部以 engine/ 为根寻址）——engine 内部旧式相对路径不是缺陷，缺陷仅限自仓库根再拼 engine 前缀的调用点。

**`duanxian/testing/` 归类（17 件，B-E030 及入口核对）**：运行驱动 1 件（run_duanxian_conception_v2.py）；run08 阶段构建辅助 3 件（build_run08_hi1_000230/000237/000238）；阶段构建与装配脚本 10 件（c1/e1/t1/w1 构建器、q1 语义与交接、h1 计划/片段/HTML/装配）；评审生成 1 件（generate_duanxian_editorial_review.py）；树内测试 2 件（test_c1_determinism.py、test_duanxian_title_provenance.py）。该组为项目侧测试与辅助资产，存在不等于通过，本轮仅做只读归类，未执行。

**技能与 harness 存量（B-E033/B-E035/B-E036）**：skills 一级目录 82 个、各含 SKILL.md，其中 `novel-hld-*` 21 个（HLD 阶段技能族，含 Legacy 标记的 novel-hld-writer 与交接提示涉及 14 个既有失败的 novel-hld-lld-readiness-evaluator）；构思生产技能 7 个，与 run.py 的 S1/W1/E1/T1/C1/Q1/P1 路由一一对应；另有 novel-interview-b0-migrator、novel-lld-writer、novel-narrative-contract-designer 等设计、访谈与迁移族，以及测试辅助类技能。树内 `test_*.py` 56 件分布于各技能 tests/ 子目录，构成“一技能一契约一测试”的形态；本轮对 7 个生产技能、b0-migrator、novel-hld-writer、lld-readiness-evaluator 做跨文件核对，其余为结构级核对。harness 文件数：novel-conception-interview 92（0 测试）、novel-conception-autonomous 107（25 测试）、novel-hld-autonomous 152（12 测试）、kun-workshop-intranet-delivery 53（0 测试）。**计数漂移（IC003）**：`README.md` L5 与 `engine/README.md` L9 写“81 个技能”，实测 82。zip 31 个、唯一 sha256 23 个、8 对重复（interview 1.0.0 releases＋dist 六件、autonomous 1.0.0 codex=source、harness releases codex=source）（B-E034）。

**字节稳定（F08 修正，B-E005/B-E006）**：根 `.gitattributes` L3–23 模式为 `harnesses/novel-hld-autonomous/**/*`、`skills/novel-hld-*`、`skills/novel-development-baseline-preparer/**`——均无 `engine/` 前缀，保留旧根布局；对 3 个真实路径（engine/skills/novel-hld-finalizer/SKILL.md、engine/harnesses/novel-hld-autonomous/manifest.yaml、engine/skills/novel-development-baseline-preparer/SKILL.md）执行 `git check-attr --cached text eol`，六项属性全部 `unspecified`。结论：规则文本承载历史意图，**当前布局下未生效**；撤回“已强制 LF/字节稳定策略已生效”，仅登记为未生效的配置缺口，本轮不修改 `.gitattributes`【推断→未完成项】。

**历史与标记类存量**：`engine/skills/novel-hld-writer/SKILL.md` L3–5 标 Legacy（B-E040）；engine/testing 契约测试 L108/L130 与 e2e L119“production never synthesizes this gate”（作者门不可由生产侧合成）（B-E041）；`engine/skills/novel-interview-b0-migrator/SKILL.md` L2–10＋runtime `migration_handoff.py` L1–6 迁移交接（B-E042）；`engine/harnesses/novel-hld-autonomous/releases/0.1.0-acceptance.json` declaration-only（42 bounded、15 skills、18 tokens、stable_major False、4 suites、5 eval cases）＋`0.1.0.md` L3–5【历史/旧链口径】（B-E038）；`engine/harnesses/kun-workshop-intranet-delivery/README.md` L11（B-E047）；`.zcode/plans/plan-sess_316609e2-5263-4909-a27a-c47b17476339.md` 记录 engine 内部旧根布局为当时设计状态（B-E046）。

**测试与运行证据边界**：本轮未执行任何测试（作业契约禁用）。编排交接提到的 engine/tests 12 个、novel-hld-lld-readiness-evaluator 14 个既有失败属交接提示，非本轮实测，也未发现前稿将其冒充新回归——维持边界：测试存量≠通过；负例预期拒绝≠测试失败；历史日志≠当前基线事实【流程规范】。

## 七、实现程度总评与未决事项

| 对象 | 程度 | 依据与边界 |
| --- | --- | --- |
| 构思批准与留存绑定 | 已完成（限定：approved/ready＋3 对象重算一致） | 第三节；不含全链 validator 重放 |
| P1 机器本体/handoff/运行态留存 | 缺口（留存类） | 三 basename 零命中＋账本设计不入库；是否要求入库交 Owner 裁决【未完成项】 |
| 旧链隔离（proposal/旧 HLD/旧 LLD/旧稿） | 历史遗留（隔离已核，迁移责任仍在） | 第四节双向零命中 |
| 新版 HLD/LLD/写作现实进度 | 无法判断 | 留痕未见＋账本不入库；不写“未运行/未开工” |
| 项目 CLI 可用性 | 部分完成（静态断裂） | 7 条 runtime 路径；静态结论，非实测失败 |
| 引擎工具链（harness/validator/schema/测试存量） | 部分完成（能力与存量在，发布为历史或候选态） | implementation-candidate＋Legacy 标记 |
| 文档一致性 | 部分完成（81/82、章节号、旧路径引用） | IC003/IC004/IC005 |

- 不设全仓完成百分比；以上分对象结论与各节一致。下一证据需求及理由：①编排方提供 rint2 阶段执行记录（命令、退出码、忽略区写入范围、模型重派记录）——它是核验红线遵守与自检真实性的共同输入（F10 待提供输入）；②Owner 裁决机器本体留存政策——决定 IC008 应否立为缺陷还是政策选择；③新版 HLD 人审门记录——判断“构思之后”阶段是否推进的唯一合规依据；④路径修复须在授权后以 CLI selftest 与 validator 实测复核，静态复验只能确认路径存在与拼装正确。

## 八、ISSUE 候选清单

每条含问题、应然依据、实际证据、影响、版本、强度、根因、建议、验证、归并；均未创建 ISSUE、不预填编号。已具证问题与线索/建议分列。

- **B-IC001**（已具证，强）run.py 七条 runtime 路径重复 engine 前缀。应然：CLI 应能在冻结布局下装载各阶段 runtime（`run.py` L14 自身 ROOT 约定）。实际：`duanxian/conception-production/run.py:L14,L41–55,L58–99,L123–135`；7 条组合路径全不存在、正确路径全存在。影响：S1/W1/E1/T1/C1/Q1/P1 装载不可完成（静态）。版本：当前。强度：静态可定位。根因：目录重构未同步路径前缀（高置信，未运行验证）。建议：去除重复前缀或改为 ROOT 相对拼装。验证：修复后 `python3 -I` 两步装载观察＋获授权 selftest。归并：与 IC002/IC004 同族（根路径迁移）。
- **B-IC002**（已具证，强）3 件 CLI 测试 ENTRYPOINT 指向仓库外旧布局。应然：测试应自足定位被测入口。实际：`duanxian/conception-production/tests/test_attempt_selection_cli.py:L12–13,L19–23` 及 `test_line_sequence_review_cli.py`、`test_topology_review_cli.py` 同型（parents[4]＋projects 拼装）。影响：测试无法在当前布局定位入口；spec 断言不一定失败，失败点在 exec_module。版本：当前。强度：静态可定位。根因：同 IC001。建议：改仓库相对定位。验证：静态路径核对＋获授权 pytest。归并：可并入 IC001。
- **B-IC003**（已具证，中）技能计数漂移。实际：`README.md:L5`、`engine/README.md:L9` 写 81，BASE 实测 82（B-E033/B-E036）。应然：导览计数与树一致。影响：误导存量认知，不损运行。版本：当前。强度：直接留存。根因：新增技能后未同步文档。建议：两处改 82 或去掉具体数字。验证：一级目录计数复跑。归并：独立文档缺陷。
- **B-IC004**（已具证，中）全树旧根路径引用。实际：superpowers 专项 79 文件 219 行（duanxian 31 文件 88 行、engine 47 文件 119 行，B-E045）；`duanxian/writing/` 17 件各 1 个反引号 LLD 旧路径（B-E027），替换为 `duanxian/design/specs/lld/` 后均可定位。应然：重构后引用应可解析。**边界规则**：自仓库根再拼 engine 前缀的引用失效；engine 内部相对 engine/ 根的引用有效（反例 `engine/scripts/validate_hld_contract.py:L13–17`、`engine/README.md:L27`），不得全树一律改链。影响：文档与素材可解析性。版本：历史遗留兼当前。强度：静态可定位。根因：目录重构（f7ac2db 一族）。建议：按上述两分规则修复。验证：grep 抽样回放＋engine 例外人工复核。归并：IC001/IC002 与 `.gitattributes` 前缀缺失（B-E005/B-E006）同族，可合立一项。
- **B-IC005a**（已具证，中）HLD 章节号错位。实际：`duanxian/writing/characters/2026-06-07-writer-R07.md:L13–16` 引 §10.x，现 HLD 风格章为 §9（`duanxian/design/specs/2026-06-06-hld-digital-life-novel.md:L312–337`；L10 记 v4.0 重构）。影响：写作素材引用悬空。版本：历史遗留。强度：静态可定位。根因：v4.0 重构改号未同步引用（静态推断）。建议：素材改引 §9 或加迁移注。验证：章节号核对。归并：并入 IC004 迁移族。
- **B-IC005b**（线索，待取证）部分 writing 素材无 frontmatter。与 005a 根因不同，且未见明确规范要求素材必须带 frontmatter，降为线索：须先取证规范依据再定是否立项。
- **B-IC006**（已具证，中）HLD-TRACE-CLOSURE P1 open。实际：`duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/artifacts/12-hld-integrity-report.md:L25,L32–34,L57–58`；同 run `final-hld-package.md:L20–22`。影响：该 run 记录内 LLD 准入被阻。版本：历史遗留（记录属 2026-07-13）。强度：直接留存。根因：trace 未逐字段绑定（记录自述）。建议：新版 HLD 流程接管时关闭或显式作废该门槛。验证：新版 integrity 复核。表述边界：仅判定冻结记录仍 open，现实处置不可知（检索范围：全树 `git grep`，仅 2 文件命中）。归并：独立或与 IC007 同 run 记录族。
- **B-IC007**（已具证，中）v2.0/v3.0 标签混用。实际：integrity 报告 L33“v2.0 is newly presented after material world reconstruction.”而同 run `manifest.md` L12–15 定 v3.0 唯一事实源；`canonical-world-facts-v2.0.md` 与 `v3.0.md` 并存（B-E023）。影响：版本指称混乱，不改变 v3.0 权威。版本：历史遗留。强度：直接留存。根因：同 run 内报告与 manifest 口径未对齐（推断）。建议：以 manifest 为准，后续报告统一版本指称。验证：两文件对读。归并：可并入 IC006。
- **B-IC008**（已具证，中；处置归 Owner）机器本体留存缺口。实际：`conception-completion.json` `/p1_manifest`、`/development_handoff`、`/run_state` 等 Pointer 引用的本体未入库（B-E009）；根 `.gitignore:L11–18` 设计性忽略（B-E004）；三机器 basename 全树零命中（B-E048）。应然：`engine/harnesses/novel-conception-autonomous/docs/final-delivery-contract.md` L26–30 定 P1 为构思事实最终权威，其机器本体留存政策应有明示。影响：下游无法在仓库内消费机器包。版本：当前政策缺口（不作违约断言）。强度：直接留存（缺口事实）＋引用值。根因：入库政策未定。建议：Owner 裁决脱敏入库或另设留存库；**留存政策与路径缺陷（IC001/IC004）分别处理**。验证：裁决后复跑 basename 检索。归并：独立。
- **B-IC009**（建议性，弱）写作目录局部口径提示。实际反证：`duanxian/README.md:L22–23` 已声明历史链与批准优先、旧 proposal L276 亦有非冻结说明——前稿“仓库缺历史口径声明”的判断予以撤回。剩余改进点：`duanxian/writing/` 文件内无就地提示，读者直达旧稿时可能误当现行设定。建议：writing 目录加局部 README 或迁移注。影响：低。版本：建议。强度：建议性归纳【推断】。验证：采纳后以评审确认。归并：可并入 IC004 迁移族或独立小项。

## 九、证据索引与自检记录

**唯一键索引（B-E→完整路径＋定位）**：

| 键 | 定位 |
| --- | --- |
| B-E001 | `duanxian/novel-goals.md`：六章＋S01–S23 索引；L25、L49–51、L79–89、L113–119 |
| B-E002 | 根 `README.md:L5`（“81 个技能”声明） |
| B-E003 | `engine/README.md:L9`（同 81）；L27（引擎内部以 engine/ 为根寻址） |
| B-E004 | 根 `.gitignore:L11–18`（duanxian 运行账本目录忽略）；L19（.kunora/） |
| B-E005 | 根 `.gitattributes:L3–23`（harnesses/novel-hld-autonomous/**/* 等旧根模式） |
| B-E006 | `git check-attr --cached text eol` 三真实路径输出均 unspecified（命令记录） |
| B-E007 | `duanxian/conception-approved/README.md`：L3 留存声明；L18/L21 终态 revision-038 与 SHA；L22 completion SHA |
| B-E008 | `duanxian/conception-approved/author-decision.json`：/approval_scope、/decision、/run_id、/approval_record/text、/human_review_package/*、/machine_package/* |
| B-E009 | `duanxian/conception-approved/conception-completion.json`：/status、/run_id、/author_decision/sha256、/p1_manifest、/development_handoff、/h1_html_manifest、/run_state、/stage_completions 九键（B0=774ac64a…、C1=83994b8d…、E1=b5d777c8…、H1=28ec088d…、P1=42e307d1…、Q1=4dab74a1…、S1=04d25ec9…、T1=6e462e88…、W1=dd719e9f…）、/validation/sha256、/review_path 五项 |
| B-E010 | `duanxian/conception-approved/human-review-report.html`：sha256 见第三节；5 svg、0 外链、0 script |
| B-E011 | `duanxian/conception-approved/human-review-report.json`：characters.constraints 等结构化字段 |
| B-E012 | `duanxian/conception-approved/human-review-report.md`：L147/L169、L239–243、L251–255、L271/L283、L277–289、L295–309、L325–329、L382–389/L396、L423–427、L445–449、L468–475、L510–517、L524–531、L608–615 |
| B-E013 | `duanxian/novel-text/2026-06-07-duanxian-novel.md`：L161、L183–199、L201–205、L407/L417、L464–476 |
| B-E014 | `duanxian/design/workflow-docs/duanxian-narrative-contract.md`：L26、L28 |
| B-E015 | `duanxian/design/workflow-docs/duanxian-intent-card.md`：L7–11、L31 |
| B-E016 | `duanxian/design/specs/2026-07-05-duanxian-proposal.md`：L39、L45–46、L276 |
| B-E017 | `duanxian/design/specs/2026-06-06-hld-digital-life-novel.md`：L10、L312–337 |
| B-E018 | `duanxian/design/specs/2026-06-06-lld-digital-life-novel.md`：L36–39 |
| B-E019 | `duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/manifest.md`：L12–15 |
| B-E020 | 同 run `artifacts/12-hld-integrity-report.md`：L25、L32–34、L57–58 |
| B-E021 | 同 run `artifacts/final-hld-package.md`：L20–22 |
| B-E022 | 同 run `gate-report.md`（下一道人类评审门） |
| B-E023 | 同 run `canonical-world-facts-v2.0.md`、`canonical-world-facts-v3.0.md` |
| B-E024 | `duanxian/design/runs/lld/2026-07-08-duanxian-lld-workflow-blocked/manifest.md` |
| B-E025 | `engine/docs/superpowers/runs/design/2026-07-08-hld-lld-design-task-dispatch/manifest.md` |
| B-E026 | `duanxian/README.md`：L22–23 |
| B-E027 | `duanxian/writing/` 17 件；`characters/2026-06-07-writer-R07.md` L13–16、L67–70、L88–91；`characters/2026-06-07-writer-qianxu.md` L1、L15 |
| B-E028 | `duanxian/conception-production/run.py`：L14、L41–48、L51–55、L58–99、L123–135、L921–944 |
| B-E029 | `duanxian/conception-production/tests/test_attempt_selection_cli.py` L12–13、L19–23；`test_line_sequence_review_cli.py`、`test_topology_review_cli.py` 同型 |
| B-E030 | `duanxian/testing/run_duanxian_conception_v2.py`：L16–23、L27–35、L43–55 |
| B-E031 | `engine/harnesses/novel-conception-autonomous/runtime/`：19 `.py`＝20446 行；production_orchestrator.py L3466–3497；production_store.py L617–620；author_decision.py L80–88、L202–255；return_routing.py L147–156；migration_handoff.py L1–6 |
| B-E032 | `engine/docs/ai-novel-workflow/contracts/autonomous-v2/`：32 `.schema.json`＋contract-index.md |
| B-E033 | `engine/skills/` 82 一级目录各含 SKILL.md；21 个 novel-hld-*；树内 test_*.py 56 |
| B-E034 | zip 31 个、唯一 sha256 23、8 重复对（interview/autonomous/harness releases 族） |
| B-E035 | 四 harness 文件数：interview 92/0、autonomous 107/25、hld-autonomous 152/12、kun-workshop 53/0 |
| B-E036 | 实测 82 对 `README.md:L5`、`engine/README.md:L9` 的 81 |
| B-E037 | `engine/harnesses/novel-hld-autonomous/manifest.yaml`：L1–27、L44–48 |
| B-E038 | `engine/harnesses/novel-hld-autonomous/releases/0.1.0-acceptance.json` 与 `0.1.0.md` L3–5 |
| B-E039 | `engine/scripts/validate_{design_tasks,hld_contract,hld_release,prd_contract,proposal_contract}.py`；对应 `engine/tests/test_validate_*.py` |
| B-E040 | `engine/skills/novel-hld-writer/SKILL.md`：L3–5 |
| B-E041 | `engine/testing/test_conception_autonomous_v2_contracts.py` L108/L130；`test_conception_autonomous_v2_e2e.py` L119 |
| B-E042 | `engine/skills/novel-interview-b0-migrator/SKILL.md`：L2–10 |
| B-E043 | `engine/docs/ai-novel-workflow/development-phase.md`：L137–152 |
| B-E044 | `engine/harnesses/novel-conception-autonomous/docs/final-delivery-contract.md`：L26–30、L64–79 |
| B-E045 | superpowers 旧根引用专项：79 文件 219 行（duanxian 31/88、engine 47/119；另根 1 文件 11 行） |
| B-E046 | `.zcode/plans/plan-sess_316609e2-5263-4909-a27a-c47b17476339.md` |
| B-E047 | `engine/harnesses/kun-workshop-intranet-delivery/README.md`：L11 |
| B-E048 | 三机器 basename 全树零命中（`git ls-tree -r --name-only` 全名单精确匹配） |
| B-E049 | 树总量 1444＝根 6＋duanxian 148＋engine 1290 |
| B-E050 | 双向零命中：7 旧词×3 批准文件＝0；6 新名×canonical v3.0＝0；HLD-TRACE-CLOSURE 全树 2 文件 |

**自检记录（F10 时序更正）**：定义书 §6.1 文件检查（UTF-8、6000–12000 中文字、九节、五口径、BASE 串、秘密/占位模式）在**提交前**对本文件运行，通过后连同 `git status --short --untracked-files=all`、`git diff --check` 作为提交前置门；**范围检查**（BASE..HEAD 单文件新增/修改、逐提交历史、HEAD 内文件与工作树一致）必须在**提交后**对完整候选运行，其结果连同完整提交号、报告 SHA-256、远端 SHA 写入交付交接，本报告不预写该通过状态。前稿“本提交前运行两段”的时序表述错误，予以更正。
- 本轮执行边界：未运行仓库 CLI/pytest/validator/构建；除最终推送外无网络动作；未向忽略区写入业务文件；凭据零打印零写入，仅经命令替换引用并脱敏输出。
- 剩余限制：全量逐字阅读未完成（第一节账目如实保留）；机器本体不可复验（第三节）；现实运行史不可判断（第四节）；以上缺口均不反向推断为“未发生”。
