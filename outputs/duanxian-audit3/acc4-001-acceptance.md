# 《断线》R3 v4 第四步复验记录（A4）

作业：`duanxian-audit3-acc4-001`。**总体判定：PASS**。ACC-F015、ACC-F016、ACC-F017 的指定修正及受影响下游通过；全局硬约束通过。此判定评价本轮审视交付的修正质量，不是小说生产、机器链、HLD/LLD 或外部纠错完成的批准。既有 RF 和外部动作以 `OWNER_PENDING` 移交 Owner，不计入本轮 PASS/FAIL；历史 acc/acc2/acc3 的 FAIL 保留。

## A4/01 输入、独立性与适用范围

| 输入 | 本次固定身份 |
| --- | --- |
| 唯一验收基准 | `outputs/duanxian-audit3/def-001-definition.md`，定义提交 `024ef15a201a536592162b5f8442cf6a57699a8d` |
| 小说与源码 BASE | `92573f1cca40f37cee04d2beb8708ff33ba603d6` |
| 被验 v4 / 初始 HEAD | `fabd2a9e7cbb6d4b13a5158156eb3b1706d34c48` |
| 工作分支 | `remote-agent/duanxian-audit3-acc4-001` |
| 定向修正输入 | `outputs/duanxian-audit3/acc3-001-acceptance.md` A3/08，ACC-F015–F017 |
| ISSUE 冻结快照 | `.kunora/inputs/open-issues-snapshot-20261114b.md`，SHA-256 `f6cc9ddf44be3ee199c7993e0a37bc56813cb6be8b5e238da35a9f6ffeeffd90` |
| 唯一业务新增文件 | `outputs/duanxian-audit3/acc4-001-acceptance.md` |

启动摘要全文读取后，先逐项输出确认，再写入本次 ACK，随后开始业务取证。初始化产生的 ACK 与 init-report 为先前用户明确授权的运行证据，不进入业务提交。初始 `git status --short` 为空，分支与 HEAD 精确匹配。spec/PROMPT 的业务指令在初始化阶段未执行；本次另获启动授权后才执行复验。

本轮依定义 §6.3 末段执行“修正项及受影响下游复验，保留未受影响项来源”。不把第四步扩成重新实施全部 134 件语义审视，也不把实施者或前验收者的 PASS/闭合字样作为证据。已全文读取定义、实施报告、冻结 13 条 ISSUE 和 508 行旧正文；对覆盖表、读账、当前候选 delta、提案及修正记录读取相关结构与修正内容，从 BASE 原始对象自行重算、静态追读和反证。对未受影响项明确保留源定位与限度，不伪造新的全量阅读历史。

简称均位于 `outputs/duanxian-audit3/`：REPORT=`impl-001-report.md`，LEDGER=`impl-001-reading-ledger.md`，ISSUES=`impl-001-issues.md`，POINTER=`impl3-001-pointer-coverage-table.md`，PROPOSAL=`impl2-001-external-correction-proposal.md`，NOTES=`impl4-001-correction-notes.md`。A1/A2/A3/A4/A5 在本文局部来源称谓中分别指 `duanxian/conception-approved/` 的 author-decision JSON、conception-completion JSON、人审 JSON、人审 Markdown、人审 HTML；章节号 A4/xx 指本验收记录，不与批准 A4 混用。

## A4/02 ACC-F015：EV 双入口分类与覆盖证据

**判定：PASS。** 对应定义 §3.2、S03、R02/R06/R09/R11。检查对象为 POINTER §2/§6/新增 §6a/§8/§11，以及 REPORT §1.1/§11、LEDGER §0-4、n=7、§3-9。没有运行实施者的临时探针，也没有假定其未提交工作档案存在。

### 2.1 两种分组独立重建，逐行核对交付表

直接解析 BASE 的 `duanxian/conception-approved/human-review-report.json`：DI 按 source_id 分组与按完整 value_sha256 分组分别构造；随后解析交付表全部 EV 行和全部真复用行，对照源对象字段，检查集合相等、无重复及无缺项。

| 核验 | 本次结果 |
| --- | --- |
| EV 来源组 | 148 组，每组恰两个 DI 对象；全部为 T1 |
| EV 值身份 | 148/148 两侧完整 SHA-256 不同；同值 0 组；进入真复用集合 0 组 |
| 新增 §6a 全表 | 148 行的 source、两侧 1-based DI 序号、JSON Pointer、两个完整 64 位哈希与分类逐项相等；缺项/多项/错配均 0 |
| EV 指针域 | 全部 `/major_events/<n>` 对 `/planned_event_registry/<n>` |
| EV 控制语境 | 两侧 decision_control_ids 不同 148 组；exposure 不同 1 组；review_priority 不同 0 组 |
| DI 完整哈希分组 | 4077 个不同哈希，525 个双元素组 |
| §8 真复用全表 | 525 行序号、stage、Pointer、source_id、哈希前缀及源完整哈希逐对一致；集合与独立分组精确相等 |
| §8 版本稳定性 | 与修正前 `8924e22a` 的 §8 字节完全相同，没有为满足计数删改真复用对 |
| 对照来源族 | CE 321/321 对同哈希，PROP 159/159 对同哈希；与 EV 非同值分类分开 |

以上是来源关联与值身份的核验，不是对缺失 P1 值体的阅读或语义等价证明。哈希相同只能支持同值身份；它不能合并不同控制语境，更不能恢复库外原值。

### 2.2 非等价语境反证样本

| 来源与定位 | 本次原值核对 | 判断 |
| --- | --- | --- |
| EV-TR-3d275aff39f35d69807d，DI 3683/3684，即 `/drilldown_index/3682`、`/3683` | `/major_events/8` 哈希 `8090695e80df4f0e1dcc40dd5da34b6e38fc93c0f247c0a3779058ce8550ecdb`；`/planned_event_registry/8` 哈希 `30b8be16f5dcd98612d5f7dbc4c6440c94a66b6094df9f893cc9f97919e7039f`。前者挂 STORY-ARCH 与 FRAGMENTS-EVIDENCE、默认展示；后者挂 STORY-CAUSAL、仅钻取；均 supporting。 | 同来源双展示入口，非同值复用；这一唯一 exposure 差异已被 v4 语境摘要保留。 |
| END-EVIDENCE-CLOSURE，DI 1432/1706 | E1 `/storyline_environment_requirements/3` 与 S1 `/environment_requirements/3` 同完整哈希 `c6354036e719399143e764d75afcf99ec2e2c3734ec877aa29e3e72a48905ebb`，RL 分别为 WORLD-BEARING、STORY-SUSPENSE。 | 值身份可复用，阶段与控制义务仍分别保留。 |
| CHR-R07，DI 12/744 | B0 `/control_registry/11` 与 C1 `/profiles/12` 不同哈希；前者 supporting、仅钻取，后者 critical、默认展示且挂两个控制维度。 | 同名 source 不足以推同值；v4 没有以 EV 修正泛化成所有同源皆可复用。 |

POINTER §6 已撤回 CE/PROP/EV 一起称为“§8 镜像”的旧表述；当前镜像结论只用于 CE/PROP，EV 单列非复用。REPORT 和 LEDGER 的相应覆盖声明均指向 §6a，并继续写明 P1 值体未读。历史 v3 结语仍在，但后接 v4 明确撤回与替代说明，不作为当前结论读取。

### 2.3 受影响覆盖结构的回归检查

独立枚举 R=127、N=8（与 R 重合 novel-goals 一件）、R∪N=134、E=21。LEDGER n=1..155 连续，路径集合精确相等；每件 OID、SHA-256、字节数与 BASE 匹配。工程 21 件选择理由在 LEDGER §2，不把其源码或测试描述写成执行结果。

RL 的 18 个控制维度/exposure/优先级组合逐行重算条数和索引范围，全部相符；rationale 为单值“保留 current P1 来源对象的逐值审阅入口。”，relation 为 supports。DI 的 91 个阶段×域分组逐行核对数量、首尾序号、去重 source、哈希数和复用成员数，全符；共 78 域、6 阶段。SC 64 源族的记录数、引用总数、EVID 数、MOD/FRAG 数及多引用条数全部相符。引用合计 4626，EVID 4506，另 120 次 MOD/FRAG 引用涉及 42 个内容锚，均能在内容域定位；96 个 DI 无 SC 可见入口，不是 DI 本身不存在。

同索引 RL/DI 的 source_anchor_id 以及连续 EVID ID、label 公式、完整哈希格式、SC 与 DI 的 source 集合均独立核对。DI 实际是七字段，旧“六字段”总数仍不精确；source_anchor_id 有独立配对核验且未丢覆盖，继续列 RF-5。不能把这个已披露的计数措辞问题当成 148 组 EV 分类仍未完成。

## A4/03 ACC-F016：入口四列表与阶段证据

**判定：PASS。** 对应定义 S05/S06、R04/R06/R11。证据源是 `duanxian/testing/run_duanxian_conception_v2.py`，读取根常量、完整 `load_stage_runtime` 函数和全部调用段；用标准库 AST 抽取字符串，不 import 该模块、不执行加载器或生产代码。

L16–17 定义 ENGINE=仓库根/engine、NOVEL=仓库根/duanxian；L43–55 的加载器依次选择 ENGINE/relative_path、ENGINE.parent/relative_path、NOVEL/relative_path。对 AST 的 11 个调用逐候选与 BASE tree 比较，得到七个技能 `[不存在,存在,不存在]`，四个 builder `[不存在,不存在,存在]`。

| 阶段 | 精确入口（仓库相对） | 调用开始行 | 首次命中 |
| --- | --- | ---: | --- |
| S1 | `engine/skills/novel-storyline-architecture-designer/scripts/run_v2.py` | 80 | 第二根 ENGINE.parent |
| W1 | `engine/skills/novel-world-model-designer/scripts/run_v2.py` | 84 | 第二根 ENGINE.parent |
| E1 | `engine/skills/novel-environment-system-designer/scripts/run_v2.py` | 92 | 第二根 ENGINE.parent |
| T1 | `engine/skills/novel-event-timeline-designer/scripts/run_v2.py` | 100 | 第二根 ENGINE.parent |
| C1 | `engine/skills/novel-character-system-designer/scripts/run_v2.py` | 108 | 第二根 ENGINE.parent |
| Q1 | `engine/skills/novel-conception-reviewer/scripts/run_v2.py` | 116 | 第二根 ENGINE.parent；名称无 designer 后缀 |
| P1 | `engine/skills/novel-conception-deliverable-assembler/scripts/run_v2.py` | 120 | 第二根 ENGINE.parent；名称无 designer 后缀 |

七调用的字符串本身带 engine/，首根会产生 engine/engine/skills/...；第三候选为 duanxian/engine/skills/...。错误添加 designer 后缀的 reviewer、assembler 两路径在三根都不存在。四个 builder 调用分别在 L88、96、104、112，参数为 testing/duanxian_w1_model.py、e1_builder.py、t1_builder.py、c1_builder.py，均命中 NOVEL，即第三根。REPORT §6 对这两类调用已经分开。

BASE 的 engine/ 共 1290 个文件，技能 `engine/skills/<name>/scripts/run_v2.py` 10 件；相关 harness `runtime/__init__.py` 和 `runtime/production_orchestrator.py` 在库。REPORT 将“可导入”降为静态源文件/导入路径存在，并明确依赖闭包可执行性及实际运行版本未证，符合本次只读证据能力。

### 3.1 三机器文件的阶段来源

| 文件 | 原始引用与契约 | 当前准确限度 |
| --- | --- | --- |
| novel-conception-package.json | 构思 `engine/harnesses/novel-conception-autonomous/docs/final-delivery-contract.md` §2.A 列为 P1 本体；A2 `/p1_manifest/path` 指 P1/package-manifest.json | A2 是 manifest 间接引用，不能把其 hash 说成包本体已重算。 |
| development-handoff.json | 同契约 §2.A/§2.C；A2 `/development_handoff/path` 直接指 P1/development-handoff.json，并带完整 hash | 引用值可读，本体不在冻结树，不能宣称已验证其内容。 |
| hld-completion.json | `engine/docs/ai-novel-workflow/hld-skill-contract-catalog-v1.md` L223 的 HF1 role、§16.4–16.6 的 approved 分支输出与准入绑定 | 属于 HLD HF1 finalizer；完整解析 A2 无此字符串或字段，不是构思 completion 必含件。 |

全树 1444 条路径按精确 basename 检查，上述三件均为零。duanxian/conception-runs/、engine/projects/ 各零路径，MIGRATION 指定输入不存在。REPORT/LEDGER 的“engine 在库、运行包缺失、执行版本未证”口径成立。H1-IMPLEMENTATION 与源码 H1-DUANXIAN 前缀不同只说明格式不一致，不推出入口不在库或实际生产失败，也不撤销构思批准。

NOTES 的核验说明仍有一处把加载器所在文件误写成 engine/loader.py；该路径不存在，实际函数在上述 run 脚本。主四列表及真实调用串均正确且可重现，记 RF-7 的辅助定位勘误，不改变本项路径/根/阶段来源判定。

## A4/04 ACC-F017：#20 单一目标与分层登记

**判定：PASS。** 对应定义 §2.3、S06–S08、I02/I03/I04/R07/R11。本次通读旧正文 508 行，回读 meeting-room 的空间定位、阈值样本、出场表，shenyu 的 K6 电话及行为表，zhengbozhou 的 K4/K6/K8 场景与频次表，并全文读取冻结 #11/#12/#13，不凭前轮结论判断。

### 4.1 主候选原文与反例测试

正文 `duanxian/novel-text/2026-06-07-duanxian-novel.md` L191/L195 为 67%→82% 的同一身份匹配链；L363 明确写第一次、第二次匹配；L464 在沈逾读取第一段推理链时，却在同样的百分比变化后概括为“七次匹配”。L379/L472 的七个节点属于第二段认知路径，不能替第一段匹配次数消除矛盾。这证明叙述记录内部不一致，不推断现实世界必然发生了哪些未写出的尝试。

v4 的主候选只要求“正文计数口径收敛（同一推理链匹配次数统一）”。独立反例测试：假设后续授权版本仅使这条推理链的计数一致，K4/K6 仍保持两种历史素材、名片和编号观察仍保留，则主候选已满足关闭条件；反向仅处理会议载体而不统一计数，主候选仍未关闭。因此当前目标能够单独修复及验收。

“七”的来源可能与素材回放次数有关，但未取得生成因果，保持推断，不用它支持必然因果。传输、人数、面孔同一性、仓库/地点等已撤回互斥断言未恢复：门外一人不排除其他人，门前熟悉面孔与右侧未注意轮廓不保证同一对象，未描写传输也不等于未发生。

### 4.2 载体与附带项逐项核验

| 子项 | 原文与机制 | v4 处置及本次判断 |
| --- | --- | --- |
| K4/K6 载体 | `duanxian/writing/spaces/2026-06-07-writer-meeting-room.md` L17/L20、§3.1–3.4、§8 明确会议室；`duanxian/writing/characters/2026-06-07-writer-shenyu.md` L82 写 K6 回答电话；`duanxian/writing/characters/2026-06-07-writer-zhengbozhou.md` L191–199 写 K4/K6 电话、K8 面对面；正文 L302 回指 K6 电话。 | 独立不发布观察，证据限度为采用基准未定。自身潜在方向是采用声明，但不再是 #20 关闭条件或独立性理由；通过。 |
| 第比利斯时间 | 正文 L157/L335/L375 出现；属于时间标注/呈现观察。 | register_only。#11 的十秒文字来源、#12 的姓名披露、#13 的记忆能力修订均不会自动消除此标注；没有冒称 existing 三条之一。 |
| K6 编号 | 正文 L302 对话直接出现“K6 的电话里”。 | register_only，作为呈现观察；与上述三条的具体控制和关闭条件不同。 |
| L502 名片 | 正文末段确有“名片没有收”；正文前序缺少此物件的引入。素材来源与采用关系不足以直接定设计缺陷。 | pending_evidence，不发布。即使邻接来源问题，#11 只处理十秒信息传入 R-07，不能覆盖这个物件观察。 |
| 字符缺损 | zhengbozhou 场景/禁写表中存在断裂字符，如“项目关-后”“项─主管”等；属素材文字损坏观察。 | 归内部 REG-03 的 register_only 记录；这里的 existing 是内部登记，不是宣称 GitHub #11/#12/#13 覆盖，也不产生新发布权限。 |

冻结 #11 关闭要求是事件→合法文字输入→R-07 后续推断的可追溯链；#12 要求采用版本、身份材料点、接收者与披露时序；#13 要求主观片段、现实取证及核验分列，且原文明确不预填日期/次数疑点为确定矛盾。统一匹配次数与这三种关闭义务都不相互替代。对冻结其余十条逐一比较：#1–#7 的入口、库存、文本引用、属性、门状态、标签与机器取证，#8 周岚因果、#9 当前感官、#10 终局执行/披露，都不能自动关闭这个明确的计数命题。当前全状态列表没有新出现的第二个对应候选；#20 自身的历史发布通过稳定标记识别，不再次创建。

### 4.3 自然语言、JSON、提案的一致性

ISSUES 四个 JSON fence 均可解析，版本依次为 1.0、2.0、3.0-delta、4.0-delta。v4 对 DX3-F007 提供 main_candidate、五项 independent_observations、historical_publish、external_actions 和 retracted_v3_claims；不能简单读取 v3 的双目标字符串作为当前状态。

当前 main_candidate 的单一目标仅含计数收敛；五项观察依次为独立不发布、register_only、register_only、pending_evidence、already_registered_REG-03。ISSUES §2.7 五门表、§5.2 的 #20 四维行、v4 delta、REPORT §8.1/§11 与 PROPOSAL #20 v4 批注均采用同一组织方式。主候选五门是在收窄后的命题上判断通过，不追认 v1 旧正文当时五门合格。载体证据门待证、查重待比较，独立不发布；其他登记项不虚构五门通过。

线上 #20 仍是旧混合正文，已由本次 GET 证实。它与 v4 本地当前候选的不同被明确登记为历史发布/外部待授权，符合本轮 Owner 冻结判决口径。没有把“尚未执行外部编辑”重新计为本地修正失败；也没有因本轮 PASS 自动授予任何编辑、评论、关闭或拆发权限。

## A4/05 全局硬约束与 hash 审计

### 5.1 字节、权限及秘密

1. 对 BASE 全部 1444 个文件，用原始字节计算 Git blob SHA-1（含 blob 长度头）对照 `git ls-tree -r -z`，差异 0。对被验 v4 全部 1454 个既有文件同样核验，差异 0。哈希仅固定证据身份，不等同语义阅读。
2. 定义书与定义提交的 blob 字节相等；快照 SHA-256 精确匹配。v4 相对 `8924e22a` 只有五件审视交付修改、一件 NOTES 新增，没有小说源变化。本轮权限只允许新增本文，不沿用实施轮修改其他交付的权限。
3. 本轮本地操作为源文读取、标准库 JSON/AST/哈希/diff 计算和本文写入；没有运行项目生产器、validator、pytest、runtime import，没有重生成故事。网络只使用 api.github.com 的公开只读 GET 与 github.com 的指定分支 Git 交付；HTTP GET 拒绝重定向。
4. 按冻结 token 字面量模式扫描六件 v4 交付：五件原始命中 0；LEDGER 原始命中 1，定位 L239，为带省略号的 GitLab token 前缀扫描示例，后接省略号而非凭据值。人工复核为规则样例，实际秘密 0；不把原始 1 次命中隐去或宣称全体机械零命中。冻结快照及本次 22 条实取 ISSUE 正文原始命中均为 0；新本文仍须通过 spec 的零命中机械门。
5. 推送凭据只检查预置文件存在、非空、权限 0600，认证时在进程内读取，不置入 URL、日志、命令参数、remote 或临时凭据文件。本文不记录秘密。Git 提交显式 add 唯一路径，不使用 add 全目录、force push 或 main 写入。

### 5.2 可得本体绑定

| 本体 | 本次 SHA-256 | 独立比对 |
| --- | --- | --- |
| author-decision.json | `4f5a070d22a92fb211b9e99709e04e05b16460aa52ae40c7ebb0eaf49249e2bd` | A2 `/author_decision/sha256` 相等 |
| conception-completion.json | `4eabd4af2b249493f3aae1a2668c4de9b37dea7f61628e1b454293e49587d127` | 批准目录 README 的完成记录摘要相等 |
| human-review-report.html | `80cfc4d82d77683324808ba3f96817914c24fd1de007fae70641789dedf65e36` | A1 `/human_review_package/html_sha256` 相等 |

A1 decision=approved、approval_scope=conception；A2 status=ready、run_id 相同且绑定九阶段。P1 manifest 和 handoff 的引用 hash 仍只作引用值，不冒充缺失本体重算。另解析七月 PRD manifest 的 11 行摘要，将旧 docs/superpowers/runs/ 路径映射至 duanxian/design/runs/，11/11 本体 hash 相等；这不代替历史门状态或当前正式准入。

### 5.3 被验交付身份

| 文件 | v4 字节 SHA-256 |
| --- | --- |
| REPORT | `2e8b3835c89c07c4c459c1ac168bcc73d15d921189a79c13f698effabd7c9fbf` |
| LEDGER | `e81a7f5c84f2ad30be427486f64bc9ecd1cf3135ca3b9c9ae4c09e685fc59d9f` |
| ISSUES | `c3469b8a90bb883afed10f93e64ae5c5b1fae9c5e31b7665ad28b19890afc9d3` |
| PROPOSAL | `c1f02aa67e8df8c7cb0113d9ccd5ca5536b6d2cac1c942e4c34c90922b49c4dd` |
| POINTER | `05e0b1e5c949a28586fccdee812ee107197b584abe935332aa120476df904458` |
| NOTES | `668292ba8cc2d20dd00c687991ce5a882bd2e8a0dbcf5afefc955d56da6d0dbd` |
| 定义书 | `5ec5c086c32874e017cb56e58f3906e4e6a59806f5ab8fad2971d2dcd311d268` |
| acc3 修正输入 | `9ce9777c604d27decfff17c35d31c644cfac0a19ade9aac1c63728b29479bf01` |

## A4/06 公开只读回执与发布历史

本次可回读 GET 回执的列表取证时点为 **2026-11-15 10:22:32 UTC**。固定端点 `https://api.github.com/repos/innuama-coder/ai-novels/issues?state=all&per_page=100&page=1` 返回 HTTP 200、22 项、无 next Link；排除 PR 后仍 22 条。对 #1–#22 逐条 GET，均 HTTP 200、open、comments=0；单条 body 与列表 body 完全相同。#1–#13 与冻结快照比较仅忽略末尾换行，正文均一致。#14–#22 与 ISSUES 的 created 记录逐项比较 number、URL、created_at、完整正文 hash，全部相符。没有 ISSUE 写操作。

| ISSUE | created_at（UTC，2026-11-14） | 本次完整正文 SHA-256 |
| --- | --- | --- |
| [#14](https://github.com/innuama-coder/ai-novels/issues/14) | 12:52:13 | `5fb154303e9e1d576e746c1cf2bdf0f836d4caad749a01b4fe18bb73f0cb2d28` |
| [#15](https://github.com/innuama-coder/ai-novels/issues/15) | 12:52:18 | `7581445b5ab13913ec59aa2859915cbad7f9de3a5dc5caa336a50de4787073cc` |
| [#16](https://github.com/innuama-coder/ai-novels/issues/16) | 12:52:22 | `c43c926d355ea5a4c1ce9b088cec9b3a14f4c66684baa1a0124ae7c772291300` |
| [#17](https://github.com/innuama-coder/ai-novels/issues/17) | 12:52:27 | `ddae703bfc11bf45f5631a21290430a4d9efc8507830b9c2e97e7eb6cd5e4e93` |
| [#18](https://github.com/innuama-coder/ai-novels/issues/18) | 12:52:32 | `34c9ec64c3f1aaa8d1cce96566caa4f857d5c400649826b2b415699fee6ea9b4` |
| [#19](https://github.com/innuama-coder/ai-novels/issues/19) | 12:52:37 | `8521063d9fa73ad6e338cfbcf3749da1de54dfc0dab69bc77ad5e304a88cf5d0` |
| [#20](https://github.com/innuama-coder/ai-novels/issues/20) | 12:52:42 | `eea29d09a5e19aaa994ab967e7206b98658da590c514f8920b709470543b5a9f` |
| [#21](https://github.com/innuama-coder/ai-novels/issues/21) | 12:52:47 | `c10b62c7d1933001565ee9c6676770dd2eacd9b89f04cf29d720e829a34e773b` |
| [#22](https://github.com/innuama-coder/ai-novels/issues/22) | 12:52:51 | `186d0bd68319530e46757729e7feaaac661d2b988a6284129f510435add6457f` |

回执证明取证时点的公开状态与登记一致，不证明过去从未有过又撤销的操作，也不补造初始 POST 的事务日志。v4 未创建新 ISSUE；本轮不执行旧提案的任何外部动作。

## A4/07 质量线与未受影响项来源

本节 PASS 均指本轮定向复验及受影响范围。未重新实施的历史审视不伪装成本轮全读；其来源继续固定为 BASE、LEDGER、REPORT 对应行和已有验收记录中列出的原文定位。对关键反证作如下独立回源，保证修正未倒置权威或越过内容边界。

| 目标/材料类别 | 本次独立样本与反证意义 |
| --- | --- |
| G01／批准及旧 SPEC | A3 `/characters/core_characters/0` 禁顾衡复生；六月 `design/specs/2026-06-06-digital-life-novel-design.md` L12/L25–33 也区分新意识，但有完整输入方案。不能从同为新主体推记忆能力完全相容。 |
| G02／LLD | A3 沈逾卡及 `/world/systems/1` 禁启动决策、允执行；`design/specs/lld/scenes/2026-06-07-scene-K2.md` L26 是前序濒死，保留历史适配差异，不把技术操作等同启动授权。 |
| G03／workflow-docs 与正文 | A3 environments/2、/10 限文字接口；`design/workflow-docs/duanxian-narrative-contract.md` L65/L115–117 区分片段与实时感官；正文 L91 明示提取记忆。不能按视觉词一概判当前感官。 |
| G04／正文 | A3 environments/8 禁客观数据库；正文 L95/L187–199 的可寻址与像素重建不同于主观片段；L363–369 仍是内部匹配与可验证自述。此次计数修正不关闭 #13 能力问题。 |
| G05／批准及 HLD | A3 supporting_characters/1 禁周岚参与袭击；批准 Markdown L416–418 区分妻子程予安和周岚；HLD `artifacts/04-character-system.md` L20 则是历史维护例外参与者。维持对象与版本分层。 |
| G06／HLD 与批准 | 同 HLD L21 的 Information permission 是权限描述；`artifacts/07-time-information-system.md` L20–21 分别为 D+57 行动层和完整原因层 Known by/Hidden from。批准 Markdown L309/L315 要求现实核验及两层分流；#17 继续待证，不恢复权限即同一时点实际知情的推论。 |
| G07／proposal 与批准 | `design/runs/proposal/2026-07-05-duanxian-proposal-workflow/artifacts/12-ending-direction.md` L20–21 明确数字生命决定、研究员执行；A3 environments/7 禁自行终止，批准 Markdown L327 无活动备份。不能把全部旧版都概括为自行关停。 |
| G08／workflow-docs 与 proposal | 叙述契约 N4 L82 禁第一部确认受骗；上述 ending L24 “Not recommended” 是建议级，不能升级封死未来重载；批准 Markdown L327 保留开放边界。 |
| G09／治理与源码 | 项目 README L22–24 明示批准优先和历史隔离；novel-goals L63–71 明确阶段职责；本轮 A1/A2/hash 与入口 AST 静态复核见前节，未将本体缺失推为批准失效。 |

八类材料均有实际回源：批准、旧 SPEC、workflow-docs、proposal/PRD、HLD、LLD、writing、连续正文。其中 writing 与 #20 的完整相关载体对照见 A4/04；PRD 的 11 项 hash 与原始 manifest 见 A4/05。此表是反证抽查，不替代实施者的全读义务。

### 7.1 报告质量线

| 检查 | 本轮结果 | 证据与保留来源 |
| --- | --- | --- |
| R01 | PASS | 定义原 blob、BASE 1444/v4 1454 全件字节、快照 hash、分支/HEAD 正确；本轮仅新增本文。 |
| R02 | PASS（指定修正；RF 保留） | 134/21 集合及155件身份重算；148 EV 与525复用全表匹配；18/91/64 覆盖组回归通过。旧行区间精度见 RF-1，不冒充本轮134件全读。 |
| R03 | PASS（层级回归） | REPORT 九目标与版本账存在；README、novel-goals、A1/A2 直接支持批准/历史/流程分层。 |
| R04 | PASS（受影响 G09） | 七入口、三根、静态导入限度与三包阶段来源重证；未把规范存在标成机器链通过。 |
| R05 | PASS | A1/A2/A5 三本体摘要及 PRD11项重算；P1缺失引用明确限度。 |
| R06 | PASS（受影响强结论） | EV全族、入口全调用、#20完整正文与载体双侧原文重读；撤回的强互斥不恢复。 |
| R07 | PASS（受影响去重） | 冻结13条全文及线上正文一致；#20逐子项对机制/关闭条件比较，不再笼统吞并。 |
| R08 | PASS（反证回归） | 九目标与八材料类样本见本节，各有原文与不能推出的结论。 |
| R09 | PASS | 对EV全部148组、复用全部525对、静态全部11调用、#20所有分项实施完整相关扩查，不以少量样本率替代。 |
| R10 | PASS | 未运行生产、未写故事、未越域、未做ISSUE写操作；外部建议另待授权。 |
| R11 | PASS（RF保留） | 当前 REPORT/LEDGER/POINTER/ISSUES delta/PROPOSAL 可互相定位；历史与当前替代关系明确，辅助措辞问题单列。 |

### 7.2 ISSUE 质量线

| 检查 | 本轮结果 | 证据与限度 |
| --- | --- | --- |
| I01 | PASS | 22条逐条GET；九条历史发布的URL、创建时间、body hash与登记匹配，见 A4/06。 |
| I02 | PASS（当前修正） | #20计数有源、其他观察明确降级；原线上混合正文仍待纠错，不追认其旧错误。 |
| I03 | PASS（当前修正） | 冻结13条与当前列表比较；#11/#12/#13仅为比较对象，不能自动覆盖附带项。 |
| I04 | PASS | 主候选仅计数一个目标；载体为独立不发布观察，独立反例测试成立。 |
| I05 | PASS | 四版JSON可解析；历史发布、当前候选、五项观察、外部动作分层，线上存在性与登记一致。 |
| I06 | PASS | 公开正文秘密模式零命中；本轮只有GET，既有内容未写；本地扫描示例假阳性已披露。 |
| I07 | PASS（无新增路径） | 本轮无新建候选发布，所有分项明确登记状态，不以候选文本冒充线上已修订。 |
| I08 | PASS（不涉及POST恢复） | 本轮无POST及重试；稳定标记对应已发条目，不重发或另建纠错条。历史事务限度保留。 |

报告质量线与 ISSUE 当前修正质量线均通过；RF、机器包未取得、外部纠错未获授权、manual-review 未签认均按本轮冻结口径单独移交。本次未发现需要续发 ACC-F018 的阻断修正项。

## A4/08 RF 与 Owner 移交

| 项 | 本次核对及移交边界 |
| --- | --- |
| RF-1：读账行区间精度 | 独立比对 LEDGER §1 中可解析的“L1–L数字 全文”与原件 splitlines EOF，44条数字不同，如根 README 记33实19、批准Markdown记617实693。部分条目另有全文/分块方法声明；按冻结RF身份移交，不以数字错误单独反推缺读，也不声称已修好这些区间。 |
| RF-2：subject措辞解释 | 继续保留前轮登记的“带着真相”等原因层/终止事实/知骗区分，定位 `duanxian/design/workflow-docs/duanxian-subject-definition.md` L19/L34/L41/L61。此次未修改该源，不替作者裁决。 |
| RF-3：交叉引用 | 目标表实际在定义§1.3，复验规则在§6.3末段；旧报告中“第二节”等引用需后续勘误。本次按真实正文而非误写节号取证。 |
| RF-4：LLD引用数量 | 独立枚举17件 writing，反引号LLD路径每件恰1个，映射后目标均存在。旧“每件3处”不准确；迁移机制与17项目标不变，继续移交。 |
| RF-5：DI字段总数 | 实际7字段，包含 source_anchor_id；旧称6字段不准确，但该字段单独配对检查通过，没有实际漏项。 |
| RF-6：历史LLD diff收据 | 不宣称读到未提交的 `.kunora/impl3-work/` 档案或账内不存在的17个收据hash。按母本和 unified_diff(n=0) 独立重建：9个scene中K5为±12行，其余±13；8个space均±5。可重现算法与实际旧收据留存是两件事。 |
| RF-7：辅助说明定位 | NOTES 的 engine/loader.py 不存在；实际是 duanxian/testing/run_duanxian_conception_v2.py L43–55。主四列表正确，此项送后续文案勘误，不改既有文件。 |
| 外部 #14/#22 | 范围外/已有工程族的关闭说明建议继续 OWNER_PENDING，不执行。 |
| 外部 #15/#16/#17/#19/#20 | 各自收窄、撤回或待证处理继续 OWNER_PENDING；#20 后续若获准编辑应只保留计数主目标，不能恢复被撤回的互斥与双目标。 |
| 外部 #18/#21 | 保留原登记的核心及因果推断限度；如需澄清或批准包勘误，仍须另行授权。 |
| 受控机器证据 | #7 的同版包/来源链/正式验证要求仍在，未获取不等于批准无效；本轮没有宣告机器链复验。 |
| manual-review | OWNER_PENDING，由Owner确认记录完整及边界，不由验收Agent代签。 |

上述条目均不是本次新发布的 ISSUE。此次 PASS 结束本轮定向审视阶段；下一步是 Owner 接收 RF/外部纠错决策，不自行开启修正 LOOP，不扩展网络、文件或创作权限。

## A4/09 可复验方法与交付门

以下最小独立重现代码只使用标准库和 git show，不运行项目代码，不写中间文件；覆盖 F015 的数据分类与 F016 的路径命中，不把结构断言替代 F017 的原文与关闭条件判断。

```python
import ast, collections, json, re, subprocess
from pathlib import Path
B = '92573f1cca40f37cee04d2beb8708ff33ba603d6'
d = json.loads(subprocess.check_output([
    'git', 'show', B + ':duanxian/conception-approved/human-review-report.json']))
by_source, by_hash = collections.defaultdict(list), collections.defaultdict(list)
for i, row in enumerate(d['drilldown_index']):
    by_source[row['source_id']].append(i)
    by_hash[row['value_sha256']].append(i)
di = d['drilldown_index']
ev = {s: ix for s, ix in by_source.items() if s.startswith('EV-')}
assert len(ev) == 148 and all(len(ix) == 2 for ix in ev.values())
assert all(di[a]['value_sha256'] != di[b]['value_sha256'] for a, b in ev.values())
assert len(by_hash) == 4077 and sum(len(ix) == 2 for ix in by_hash.values()) == 525
table = Path('outputs/duanxian-audit3/impl3-001-pointer-coverage-table.md').read_text()
seen = set()
for line in table.split('## 6a.')[1].split('## 7.')[0].splitlines():
    if not line.startswith('| EV-'):
        continue
    s, a, pa, ha, b, pb, hb, classification = [
        c.strip().strip('`') for c in line.split('|')[1:-1]]
    a, b = int(a)-1, int(b)-1
    assert [a, b] == ev[s] and s not in seen
    assert (pa, ha, pb, hb) == (di[a]['json_pointer'], di[a]['value_sha256'],
                                di[b]['json_pointer'], di[b]['value_sha256'])
    assert ha != hb and '非同值' in classification
    seen.add(s)
assert seen == set(ev)
paths = set(subprocess.check_output([
    'git', 'ls-tree', '-rz', '--name-only', B]).decode().split('\0'))
src = subprocess.check_output([
    'git', 'show', B + ':duanxian/testing/run_duanxian_conception_v2.py'], text=True)
calls = []
for node in ast.walk(ast.parse(src)):
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
            and node.func.id == 'load_stage_runtime':
        name, rel = [ast.literal_eval(a) for a in node.args]
        hits = [p in paths for p in ['engine/'+rel, rel, 'duanxian/'+rel]]
        assert hits == ([False, True, False] if rel.startswith('engine/')
                        else [False, False, True])
        calls.append((name, hits))
assert len(calls) == 11
print('PASS: EV 148 non-equivalent; genuine pairs 525; static calls 11')
```

业务交付机械门为本作业 spec 中原 argv：UTF-8 可解码、至少6000字节、包含 ACC-F015/ACC-F017/总体判定、冻结秘密模式零命中、相对 v4 的提交路径白名单。实际交付还须分别检查工作树、暂存区和提交差异，仅本文为新增；不能用提交前空的 HEAD diff 冒充白名单证明。提交前后运行同一机械命令，最后核对远端工作分支与本地提交相等，成功后才输出完成哨兵。

分组结果：输入/字节组通过；覆盖/入口组通过；候选/去重组通过；全局硬约束组通过；RF/Owner移交组有明确未执行边界。最终交付提交号由提交后回执与最终回复给出，避免把尚未生成的提交号预填为已完成事实。
