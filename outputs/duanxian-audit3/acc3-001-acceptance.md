# 《断线》R3 v3 第三步终验记录（A3）

作业：`duanxian-audit3-acc3-001`。总体判定：**FAIL**；`design_verdict=FAIL`。本记录评价审视交付质量，不评价小说是否获批，不撤销已有构思批准。终验后交 Owner 裁决，不自行启动下一实施 LOOP。

## A3/01 判定、输入与独立性

本次重新核验 ACC-F011–F014 及受影响下游，重跑定义书 §6.1 的 **11 项 R 检查**和 §6.2 的 **8 项 I 检查**。启动材料所称“§6.4 复验规则”，在冻结定义正文中实际位于 §6.3 末段；§6.4 是定义书自身交付检查。按正文适用，不因简称“八项”漏掉 R01–R11。

| 输入 | 固定身份 |
| --- | --- |
| 唯一验收基准 | `outputs/duanxian-audit3/def-001-definition.md`，定义提交 `024ef15a201a536592162b5f8442cf6a57699a8d` |
| 小说与源码 BASE | `92573f1cca40f37cee04d2beb8708ff33ba603d6` |
| 被验 v3 / 本作业初始 HEAD | `f3c69866ed4e3c29c79c229905a85af3795e099d` |
| 修正输入 | `outputs/duanxian-audit3/acc2-001-acceptance.md`，A2/07 的四项动作、产物、禁止项与复验方法 |
| 工作分支 | `remote-agent/duanxian-audit3-acc3-001`，初始 `git status --short` 为空 |
| ISSUE 冻结快照 | `.kunora/inputs/open-issues-snapshot-20261114b.md`，SHA-256 `f6cc9ddf44be3ee199c7993e0a37bc56813cb6be8b5e238da35a9f6ffeeffd90` |
| 唯一业务新增文件 | `outputs/duanxian-audit3/acc3-001-acceptance.md`（本文） |

已全文读取本次启动摘要、作业 spec/PROMPT、定义书、实施报告、冻结 ISSUE 快照；先逐项确认，再写本次 ACK，随后才业务取证。实施者及前验收者结论只作为待复验对象和历史定位，不作为本次 PASS 的证据。所有源文均从 BASE 对应文件取证：先用 Git blob 算法核对全部 1444 个源文件与 BASE 相等，再读取工作区原文；没有把“哈希一致”当作语义阅读。

本文简称：REPORT=`impl-001-report.md`；LEDGER=`impl-001-reading-ledger.md`；ISSUES=`impl-001-issues.md`；POINTER=`impl3-001-pointer-coverage-table.md`；PROPOSAL=`impl2-001-external-correction-proposal.md`。这些简称均在 `outputs/duanxian-audit3/` 下。A1/A2/A3/A4/A5 分别是 `duanxian/conception-approved/` 内的作者决定、完成记录、JSON 人审报告、Markdown 人审报告、HTML 人审报告。

| 四项复验 | 本次结果 | 原因 |
| --- | --- | --- |
| ACC-F011 | **FAIL（主要结构证明已补，语境映射仍有误）** | 18/91/64 分组、525 对实际同哈希复用均重算正确；但 POINTER §6 把另 148 组不同哈希的 EV 双入口也称为 §8 同值复用对的镜像。非等价语境未被正确表达，续 ACC-F015。 |
| ACC-F012 | **FAIL（缺失范围已纠正，四列表仍不准确）** | engine 在库及缺运行包限度正确；七技能实际经第二候选根命中，表却写首根，并构造两个不存在的技能名，还把 HLD completion 归为 A2 引用，续 ACC-F016。 |
| ACC-F013 | **FAIL（#17 已修正，#19 有明确理由，#20 未闭合）** | #20 的当前单一关闭字段仍含两个不同目标，附带项又笼统归 #11/#12/#13，缺逐子项机制对应，续 ACC-F017。 |
| ACC-F014 | **PASS（指定机制/关闭标准纠正成立，附 RF）** | #3 文本引用、#4 text/eol 属性、#7 受控同版取证的区别恢复；#14/#22 范围外撤回维持。“每件 3 处 LLD 引用”为轻微数量表述错误，单列 RF，不凭此判 FAIL。 |

FAIL 由上述交付内部仍可复现的错误决定。RF、未公开 P1 值体、外部 ISSUE 纠错尚待授权以及 manual-review 的 `OWNER_PENDING`，均不单独计入本次 FAIL。

## A3/02 ACC-F011：覆盖、复用与非等价语境

### 2.1 集合与身份复算

从 BASE 枚举 R 为 `duanxian/` 排除 `conception-production/`、`testing/` 的 127 件；N 为定义的八份基准，与 R 重合 novel-goals 一件，故 R∪N=134；E=21。LEDGER 的 n=1..155 连续、路径集合精确相等，N/R/E 标签为 7/127/21；逐件 OID、SHA-256、字节数均匹配，21 件工程选择理由均在 §2。解析 Markdown 时要保留单元格内额外竖线，不能用固定总列数漏掉 proposal 的 ending/risk 两行。本次按六个身份前缀字段解析后是 155 件，而非误计的 153 件。

A3 SHA-256 为 `f3d848f15547e77bcb0a0d54b288efe9989e53e286470a200544966af173c640`，blob 为 `2bad572c1d6f2aee42fae2faa2ba0433195772c5`。三阵列枚举结果：

| 域 | 记录 | 标量叶节点 | 已独立验证的覆盖映射 |
| --- | ---: | ---: | --- |
| `/reduction_ledger` | 4602 | 27618 | 六字段；按控制 ID 集合、exposure、priority、rationale、relation 重建 18 组合，逐组合计数与表相等；锚顺序及 DI 配对成立。 |
| `/drilldown_index` | 4602 | 32214 | 实际七字段，含 `source_anchor_id`；按 stage 与去掉末尾数组下标的 Pointer 域重建 91 组，78 域、6 阶段，组数、成员数、最小/最大序号全匹配。 |
| `/source_coverage` | 3924 | 8550 | 64 源族逐族核对记录数、引用总数、EVID/MOD/FRAG 数及多引用记录数，全部吻合。 |

68382 个库内标量叶节点的结构定位可由这些分组谓词及 BASE 索引重建。4626 次引用中 4506 次 EVID 引用指向 4506 个 DI 条目；120 次 MOD/FRAG 引用对应 42 个内容锚，实际内容对象中全部存在。96 个 DI 条目没有 SC 可见入口、20 条 SC 引用非字典序，也均可复算；前者仍可从 DI 访问，后者不是断引用，均不自行升级为故事缺陷。

同值复用表 §8 的 525 行已逐行解析：两侧序号、stage、Pointer、source_id、哈希前缀与原始完整哈希均匹配；与按完整 value_sha256 分组所得双元素集合比较，缺项 0、多项 0、错配 0。4077 个不同哈希成立。未取得 P1 值体，故既不验证值体语义，也不把相同哈希解释为已经阅读缺失本体。

### 2.2 定向语境抽查与扩查

以下序号如注明 DI 序号则从 1 开始；JSON Pointer 的数组下标从 0 开始。

| 样本与选样理由 | 原始内容与本次判断 |
| --- | --- |
| CHR-R07，检查同 source 不同层级 | DI 12 是 B0 `/control_registry/11`，DI 744 是 C1 `/profiles/12`，两者哈希不同；SC 同时列这两条 EVID 和 `MOD-CHAR-PROFILE-R07`。RL 前者 supporting/drilldown-only，后者 critical/default-and-drilldown 且挂两个控制 ID。同名 source 不自动等价。 |
| CHR-SHEN-YU，检查角色控制分配 | DI 745 `/profiles/13` 的 RL 为 `DCTRL-CHAR-NETWORK`、critical；实际 A3 沈逾卡允许执行、禁止项目启动决策。控制分配标签与角色事实须分开读取，不能按 R-07 卡复用。 |
| END-EVIDENCE-CLOSURE，检查跨阶段同值 | DI 1432 E1 `/storyline_environment_requirements/3` 与 DI 1706 S1 `/environment_requirements/3` 同哈希 `c6354036e719…`；前者 RL WORLD-BEARING，后者 STORY-SUSPENSE。值身份可复用，控制语境不可合并。 |
| CE-24-04f84de7cd705ac7a271，检查计划/因果双入口 | DI 2652 `/causal_edges/34` 与 DI 2653 `/planned_causal_edges/34` 同哈希 `0ec5aad0d52c…`，RL 分别 STORY-CAUSAL 与 STORY-SUSPENSE。§8 保留两侧定位，复用声明在这个样本成立。 |
| EV-TR-3d275aff39f35d69807d，挑战 §6 的“复用镜像” | DI 3683 `/major_events/8` 与 DI 3684 `/planned_event_registry/8` 同 source_id，却不同哈希；SC 还包含 FRAG-DX-03。两条 EVID 可见不等于两条同值复用。 |

最后一例触发定义 R09，本次扩查 **全部 148 个 EV source_id**：每个恰有两个 DI 对象，**148/148 对哈希不同，0 对同值**。例如 `/drilldown_index/3682/value_sha256` 为 `8090695e80df4f0e1dcc40dd5da34b6e38fc93c0f247c0a3779058ce8550ecdb`；下一项为 `30b8be16f5dcd98612d5f7dbc4c6440c94a66b6094df9f893cc9f97919e7039f`。

POINTER L284 却将“CE 321、PROP 159、EV 148×2（296+1）”并列等同“§8 复用对在 SC 侧的镜像”。§8 的七类型确实没有 EV major_events/planned_event_registry 对，§4 G010/G015 也各记复用成员 0。因此问题不是数据未遍历或计数漏算，而是新覆盖证据内部把“同来源、多展示入口”误写成“同值复用”。ACC-F011 明确要求非等价语境核验，此项尚未消除。不能用 525 真复用对正确抵消另 148 组的错误归因。

### 2.3 LLD 模板覆盖边界

LEDGER 给出 scenes 母本 K1、spaces 母本 operation-room，其他成员相对母本采用 `difflib.unified_diff(n=0)`。本次从 BASE 对应字节独立重建 9+8=17 个差异：scene K5 为 ±12 行，其余八个 scene 为 ±13 行；八个 space 为 ±5 行，与 v3 披露一致。没有要求将可精确复现的相同段重复抄入报告。

但所称 `.kunora/impl3-work/lld-diff-receipts.txt` 等工作档案在本 worktree 不存在，LEDGER §5 也未实际列出声称“账内一致”的 17 个收据 hash。本次接受明确母本/成员/算法作为可复现映射，不声称读到了那些历史收据，不补造其时间或哈希；该表述问题移交 RF。它不是本次 ACC-F011 FAIL 的依据；失败依据是上面的 EV 非等价语境错误。

## A3/03 ACC-F012：引擎可得性与四列表

独立 `git ls-tree -r -z BASE` 得 engine/ 共 1290 件；七个实际调用的技能入口，以及 `engine/harnesses/novel-conception-autonomous/runtime/__init__.py` 和该目录的 `production_orchestrator.py` 均在库。`duanxian/conception-runs/` 与 `engine/projects/` 各 0 件，三个机器文件 basename 各 0 项。REPORT、矩阵和 LEDGER 已撤回“engine 全缺失”，实际运行版本未证及 H1 前缀差异的限定也正确，不以此推翻批准。

静态追读 `duanxian/testing/run_duanxian_conception_v2.py` L16–48、L80–122，得到下表。没有 import、运行入口或调用生产 validator。

| 阶段 | 真实仓库路径（均存在） | 实际命中根 |
| --- | --- | --- |
| S1 | `engine/skills/novel-storyline-architecture-designer/scripts/run_v2.py` | `ENGINE.parent`，第二候选 |
| W1 | `engine/skills/novel-world-model-designer/scripts/run_v2.py` | 同上 |
| E1 | `engine/skills/novel-environment-system-designer/scripts/run_v2.py` | 同上 |
| T1 | `engine/skills/novel-event-timeline-designer/scripts/run_v2.py` | 同上 |
| C1 | `engine/skills/novel-character-system-designer/scripts/run_v2.py` | 同上 |
| Q1 | `engine/skills/novel-conception-reviewer/scripts/run_v2.py` | 同上，名称没有 designer 后缀 |
| P1 | `engine/skills/novel-conception-deliverable-assembler/scripts/run_v2.py` | 同上，名称没有 designer 后缀 |

原因可由源码直接重演：ENGINE 是仓库根/engine，传参本身已以 `engine/skills/` 起始，首候选为 `engine/engine/skills/...`，不在树中；第二候选去掉一次多余根，才命中真实入口。REPORT L124 却写“三根回退首根（ENGINE）”，并用统一 `-designer` 后缀的花括号表达式把 Q1/P1 写成两个不存在的路径。逐件 `git cat-file -e BASE:<path>` 证实有后缀的两件不存在，无后缀的两件存在。这是 ACC-F012 新要求的核心四列表中“路径/解析根”两列错误，不只是行号偏差。

同表 L128 还把三个机器文件统一列为“A2 manifest 哈希引用”。实际 A2 有 P1 manifest、development handoff 和阶段 completion，但没有任何 `hld-completion.json` 引用；冻结 #7 已明确该 basename 的缺失是独立 HLD 证据边界，不能说成构思完成记录应含它。L125 的“模块可导入”亦应限定为“源文件和导入路径存在”，静态核验未证明依赖闭包可成功执行。

ACC-F012 因上述四列表事实未闭合而 FAIL；不要求运行生产来证明导入，不改脚本，不要求取得库外运行包。影响限 G09 可复现证据及 REPORT 的强结论，已正确修正的 engine 在库与前缀限度继续保留。

## A3/04 ACC-F013：证据状态、子集合与候选资格

### 4.1 #17：未过门的修正成立

独立回读 `duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/artifacts/04-character-system.md` 与 `07-time-information-system.md`，包括正文两表及 Fact Trace：前者 HLD-04-05 行的 Information permission 写“掌握行动层；原因层须复核申请”，Concrete motive evidence 是危机解除后要求完整原因；后者 HLD-07-04 是 D+57、具体行动情报、Known by/Hidden from，不能把两列改名 visible_to，亦不能直接当同时点同粒度权限矛盾。HLD-07-05 完整原因层仍隐藏于处置组与读者，不能借行动层结论补造实际知情。

ISSUES §2.4、REPORT §8.1、PROPOSAL #17 和 v3 delta 均明确撤回“窄命题过门”，维持门②未过，历史 published_open 与当前候选资格已分离。本次确认该修正 PASS；没有采用 v2 JSON 仍保存的旧说法作为当前门判。v3 delta 按 finding_id 覆盖 v2 相应字段，v1/v2 作为历史保留是允许的。

### 4.2 #19：隔离判断已明确，限定为未来复用适配

独立原文：项目 README L22–23 已明确批准包优先；novel-goals §三.3 明确旧链隔离。六月 `design/specs/lld/scenes/2026-06-07-scene-K2.md` L26 仍写“前序濒死且转移流程启动”；`design-scenes-draft.md` L18 明写脑死亡前、第一次传输活人；六月 `design/specs/2026-06-06-prd-digital-life-novel.md` L38/L120/L190 则分别是脑死亡前输入、角色濒死身份、必须活着完成转移。批准 A3/A4 的顾衡为已死亡记忆来源；沈逾卡和 `/world/systems/1/must_hold` 同时允许知情执行、禁止项目启动决策。

v3 正确撤回“执行即违规”和“全库无隔离”，明确区分层级误用与事实级再利用，提出旧条目将来被消费时须明确适配。该判断有真实双侧事实，窄子集不是任意换对象，且与 #8 周岚参与链、#10 终局执行不同。本次认可其作为历史适配义务的修正；**不把“素材仍可被消费”当成已发生错误消费的证据**，也不把提案中的 Owner 逐项声明解释为本次必须取得的新签认。是否采用旧素材、怎样做后续适配仍须授权，不能因此要求现在改写旧稿。

### 4.3 #20：计数核心成立，但登记仍未单一化

独立通读 508 行 `duanxian/novel-text/2026-06-07-duanxian-novel.md`。其 L191/L195 的 67%→82% 匹配，在 L363 明说第一次、第二次；L464 对同一推理链却说“七次匹配”。L379/L472 的七个认知节点属于另一计数对象，不能相互抵消。计数矛盾可以保留，素材“第七次回放”只是潜在成因，不作为已证生成因果。

撤回传输、人数、面孔、地点的强互斥合理：正文“不是一个人”与另一版本门口一人不排除多人；门正前方的熟悉面孔和右侧未注意的轮廓不保证同一人；省略传输不等于未发生。没有恢复这些已撤回断言。

载体项独立回读：`duanxian/writing/spaces/2026-06-07-writer-meeting-room.md` §1/§3/§8 明写 K4/K6/K8 在会议室；`writing/characters/2026-06-07-writer-shenyu.md` L82 写 K6 回答电话；`writer-zhengbozhou.md` L191–199 写 K4/K6 电话、K8 面对面；正文 L302 回指 K6 电话。这是另一版本采用/载体协调问题，不由计数口径修正自动解决。

ISSUES L107 明说两个关闭目标“明确非同一”；v3 JSON L344 的 `closure_target_single_verifiable` 仍同时装入“正文计数口径收敛”和“K4/K6 采用基准声明”。`publish_gate` 只列子项处置，没有为后者从 #20 主候选中退出给出独立 not_published/insufficient_evidence 状态；`difference_reason` L106 仍把载体子集合与计数一起作为 #20 独立性理由。PROPOSAL 也保留两目标。**称为独立子项尚未完成候选级剥离**：现行记录不能唯一回答“只解决计数，#20 的修订目标是否已完成”。不要求拆发两条 ISSUE，但必须将待证载体作为另项不发布观察，或明确整个候选目标门未过。

另一残余是“工程/道具/披露附带项剥离归 #11/#12/#13”的笼统映射。线上 #20 的第7项实含第比利斯时间、K6 编号泄漏、L502 名片无来源及素材字符缺损。冻结 #11 是十秒沉默传入 R-07 的文字来源；#12 是郑柏舟身份披露；#13 是记忆数据库化及现实核验，正文明确次数疑点不预判为矛盾。修正计数不必修复记忆能力，名片、字符缺损也不能仅因同一载体自动归给这三条。应逐子项说明 existing 的机制/关闭条件对应，不能覆盖的改 register_only/out_of_scope/待证，不能把“比较对象”改成“已有覆盖”。

本次未把线上旧正文未改当作 FAIL；失败是 v3 **当前本地**候选分类与目标仍不闭合，违反定义 §2.3、I03/I04/R11，续 ACC-F017。

## A3/05 ACC-F014 与十三条去重复核

冻结 13 条全文已读，本次公开 GET 的 #1–#13 与快照 BODY 内容相等（仅规范化末尾换行）；当前仍 open、评论数均 0。四维复核按对象、控制、机制、关闭条件进行，不按标题或文件载体替代机制。

| 条目 | 本次核对与处置 |
| --- | --- |
| #1 | 原正文限定 run.py 七路径和三测试入口；静态装载问题，不证明所有命令运行失败。#22 不因换脚本获得范围授权，维持工程范围外。 |
| #2 | 两 README 计数声明问题，不是小说内容质量门；不新增技能库存审计。 |
| #3 | 快照 L98、映射表与 writing 原文相符：17 件各一个反引号 LLD 路径；R07 L14/L16 另有五个风格指称。机制是文本引用及内容指称迁移，非属性匹配。v3 正确恢复两类关闭要求；每件“3处”的数字错误见 RF。 |
| #4 | 根 .gitattributes 的 text/eol 与 engine 路径匹配问题；关闭应覆盖全预期集，非 ignore。只确认风险，不宣称已发生字节损坏。 |
| #5 | 历史 HLD trace open、语义自述通过、人审 pending 必须分列；不借本次审视改门状态。 |
| #6 | 旧 HLD v2/v3 标签指称，不证明实际审错版本；与 #5 关闭条件不同。 |
| #7 | A0/A1/A2、novel-goals 与原 ISSUE 均明确不入库政策；请求受控同版证据，不要求公开 P1 或改变政策。v3 恢复 run、清单/hash、manifest/决定/validation/execution/实现及来源链、受控重放的区别，指定修正成立。 |
| #8 | A3 `/characters/supporting_characters/1/must_not_imply` 禁止暗示参与袭击；旧 canonical-world-facts-v3.0 L38–44/L67–73 与 HLD-04 周岚行主动维护例外链相反，但明确不知道完整规模、不得直白恋爱化。归既有适配问题。 |
| #9 | A3 `/world/environments/2` 与 `/10` 为当前文字接口；七月 PRD `03-trunk-scenes.md` L23/L30 确有当前光声/听见沉默。正文 L91 明示过去记忆是反证，不以视觉词全判违规。 |
| #10 | A3 `/world/environments/7`、`/decision_controls/4` 对照六月正文 L331–460 的决定直示/自行关停/她事后返回；七月 `05-information-flow.md` L26–28 则是提前披露、研究员执行，不能合称所有版本自行关闭。 |
| #11 | 完整正文 L284–341 的会议室十秒到 R-07 推断缺少文字传入，成立的是来源缺口，不虚构麦克风。关闭不覆盖所有道具、术语或文本损坏。 |
| #12 | writer-betrayer L15/L40/L76–102 限制内部人员类别和披露；writer-zhengbozhou L211 限名；正文 L193–199/L365–369/L464–466 显名。只保留历史版本采用义务，不变成当前作者绝对禁令。 |
| #13 | A3 `/world/environments/8` 对照六月 design L12/L25–26、正文 L95/L187–199/L343 的完整记忆与像素重建。L363–369 只是自述可验证，不是现实核验已完成；次数另有独立判断。 |

指定 #3/#4/#7 的核心修正判 PASS；#14/#22 已撤回范围资格亦保持。复核其余候选时发现 #20 对附带项的无区分归并，单列续 ACC-F013 的 ACC-F017，不以原三行修好推整个四维表全无问题。

## A3/06 九目标反证样本及全局质量线

### 6.1 非发现行反证样本

本表每项为本次实际回读，不继承前验收的 PASS。它补足复验的全局反证要求，不自称重新实施 134 件全量语义审视，也不降低实施者全读义务。

| 目标 | 样本、选样理由与源文 | 判断及限度 |
| --- | --- | --- |
| G01 | A3 `/characters/core_characters/0` 与六月 design L12、L25–34，挑战“记忆继承即原人复活” | 批准卡禁止顾衡复生/预装恋爱；旧 design 也写新意识，完整输入另归 G04。没有把旧输入方案直接提升为批准事实。 |
| G02 | A3 沈逾卡与 systems/1，六月 LLD K2 全文、旧 PRD L38/L120/L190 | 禁启动决策但允执行；生前/死后为真实历史适配差异。不能用 M1–M6 操作反推决策权。 |
| G03 | A3 environments/2、/10；叙述契约 L65；旧正文 L91 | 过去记忆可含感官；现时文字接口限制不等于全篇禁感官词，反证界限成立。 |
| G04 | A3 environments/8；正文 L95、L187–199、L363–369 全上下文 | 记忆只能线索，内部匹配不等于现实验证；既有 #13 包含真实反例，不自动包含计数矛盾。 |
| G05 | A3 周岚卡及 A4 L408–448；旧 HLD canonical §5 | 周岚儿时守护者、程予安在世妻子，恋爱五年结婚两年归程予安；禁止重复对象混淆。旧 HLD 的参与链保留历史适配身份。 |
| G06 | A4 L310–327 与两张 HLD 权限/知情表 | 行动/原因分层、亲属保护不妨碍救援；权限、时点和实际知情不是同一字段，#17 不能宣告矛盾已确证。 |
| G07 | A4 L271/L283/L327/L510；proposal `12-ending-direction.md` 全文 | A4 多次直写无活动备份；proposal 也写数字生命决定、研究员执行。撤回“md 无覆盖”和“旧版全自行关闭”合理。 |
| G08 | 同 proposal L24 的 Series hook=Not recommended，叙述契约 N4；subject-definition L34/L41/L61，PRD FREEZE-10 | 建议级不等于封死未来；创伤/第二部线索/delegated 不自动证明第一部知骗。FREEZE-10 要求事后理解骗局则确需历史适配，不能恢复“全部相容”。 |
| G09 | 项目 README、novel-goals、A1/A2/A5 绑定及入口源码 | 权威、历史与实际 run 分层正确；局部绑定不可升级机器链复验，四列表残余按 ACC-F016 处理。 |

批准内容、旧 SPEC、workflow-docs、proposal/PRD、HLD、LLD、writing、连续正文八类均有实取样本。#18 的 final-prd-package L34 等待人评与 L281 已确认原文亦独立回读，保留历史终包自述矛盾；#21 的 A3 环境实数 12、片段实数 3 与 statement 十/六不符，保留计数核心，未以数量证明体验控制满足。

### 6.2 报告质量线（定义 §6.1）

| 检查 | 结果 | 本次证据、影响与限度 |
| --- | --- | --- |
| R01 | PASS | 定义原提交字节相等，BASE 1444 件逐件相等，快照 hash、初始分支/HEAD 正确；本文为唯一新增。 |
| R02 | FAIL（语境复用，不是集合缺件） | 134/21、155 件身份及工程选择理由通过；A3 覆盖分组可复算，但 EV 非等价对象被误归同值复用，见 A3/02、ACC-F015。 |
| R03 | PASS | 实施报告全文有九目标、四层版本账；A1/A2 身份、批准范围及历史层区别成立，未虚构根宪法。 |
| R04 | FAIL | 12 字段矩阵存在，缺包限度已修正；支撑 G09 的四列表路径/解析根及 A2 引用仍失真，见 ACC-F016。 |
| R05 | PASS | 三个可得本体 hash 重新计算并核对绑定；缺失 P1/运行本体不宣告已复算，见 A3/07。 |
| R06 | FAIL | 受影响强结论直接回源；七入口命中根、A2 无 HLD 引用、EV 全族非同值构成反例；未以不存在包推现实生产失败。 |
| R07 | FAIL（受影响下游） | 13 条逐条核对，指定三行机制已恢复；#20 附带项归并仍无法从 #11/#12/#13 关闭条件推出，见 ACC-F017。 |
| R08 | PASS | 九目标与八类材料反证样本见 A3/06.1；保留相容原文与不成立的强推论。 |
| R09 | FAIL（被验交付） | 本验收已扩查全部 148 EV、全部七入口和 #20 所有子类；v3 的“闭合/无同类问题”声明仍不能覆盖这些反例。 |
| R10 | PASS | 本次未运行生产、未修改故事、未进行 ISSUE 写操作或越域网络；外部纠错保持 OWNER_PENDING，修正指令可恢复。 |
| R11 | FAIL | 三版 JSON 可解析、历史保留可识别；但 POINTER 内部复用说明、G09 四列表和 #20 单一目标仍不一致。 |

### 6.3 ISSUE 质量线（定义 §6.2）

本轮按 Owner 冻结口径审视当前修正质量；线上旧误报所需的编辑/关闭授权单独移交，不因尚未执行而重复扣分。

| 检查 | 结果 | 本次证据、影响与限度 |
| --- | --- | --- |
| I01 | PASS | 无认证全状态列表及 22 次单条 GET；九条 number/URL/created_at/正文 hash 与登记一致。 |
| I02 | FAIL（当前 #20 组织） | #17 门②已降为未过；#19 已给隔离充分性理由；#20 核心有证据但候选目标及附带项状态仍不闭合。旧线上问题本身不作本轮独立失败理由。 |
| I03 | FAIL | 当前 22 条与冻结13条对照；#14/#22 撤回保持，但 #20 的“剥离归”缺逐项机制对应，不能借其他关闭范围吞并。 |
| I04 | FAIL | JSON 单一关闭目标同时写两个明确不同的目标；待证载体未独立标为不发布观察或明确使目标门失败。 |
| I05 | PASS（登记事实） | 九条实际发布均存在；未发布 REG/REJ 保留，v3 delta 不冒充新线上正文；语义组织错误另在 I02–I04。 |
| I06 | PASS（可见证据范围） | 五件 v3 交付及本次公开正文按冻结秘密模式扫描零命中；评论0、状态open、正文未变。当前状态不证明历史上从未发生任何又被撤销的操作，本次自身只有 GET。 |
| I07 | PASS（不发布路径如实） | impl3 及本次未新增 ISSUE，不把候选当新发布成功；修正仍不合格不由“零新增”掩盖。 |
| I08 | PASS（本轮无 POST） | 当前九个标记对应九条已发记录，未发现重复发布对象；未补造历史 POST 日志，不在本次重试发布。 |

报告质量线 FAIL，ISSUE 质量线 FAIL，故总体 FAIL；机械交付成功不能覆盖上述语义结果。

## A3/07 全局硬约束、hash 审计与公开收据

### 7.1 字节、集合与权限

1. BASE 的全部 1444 个既有文件：用 `SHA1("blob " + byte_length + NUL + raw_bytes)` 对照 `git ls-tree -r -z BASE` 的 blob OID，0 差异；这是字节核验，不是全仓阅读声明。
2. 定义书与 `024ef15a…` 原始 blob 相等；快照精确匹配约定 SHA-256。v3 相对 acc2 提交只修改 REPORT/ISSUES/LEDGER/PROPOSAL，新增 POINTER，范围与本次冻结描述一致，不把 v3 已获授权改旧交付判作本作业越权。
3. 本次只新增本文。小说、实施包、前验收报告、定义和冻结输入零改动；提交时必须显式 add 本路径，复验提交 diff 仍只该文件。初始化 ACK/报告是前序用户明确授权的运行证据，不进入业务提交。
4. 本次只进行本地只读源文分析、JSON/AST 解析、哈希与差异计算；不 import 项目 runtime、不调用生产 CLI、pytest 或 validator。网络仅固定 `api.github.com` 公开 GET 和 `github.com` 指定工作分支 Git 交付，GET 拒绝重定向。
5. 冻结 token 字面量规则扫描：已有审视交付及 22 条实取正文均 0 命中。最终还对本文扫描；不打印、记录或拼入 URL/命令参数任何凭据。推送凭据只能在进程内读取用于认证，不写文件或 Git 配置。

三个可得批准本体重算值：

| 本体 | SHA-256 | 本次核对的引用 |
| --- | --- | --- |
| A1 author-decision.json | `4f5a070d22a92fb211b9e99709e04e05b16460aa52ae40c7ebb0eaf49249e2bd` | A2 `/author_decision/sha256` |
| A2 conception-completion.json | `4eabd4af2b249493f3aae1a2668c4de9b37dea7f61628e1b454293e49587d127` | 批准目录 README |
| A5 human-review-report.html | `80cfc4d82d77683324808ba3f96817914c24fd1de007fae70641789dedf65e36` | A1 `/human_review_package/html_sha256` |

A1 的 decision=approved、approval_scope=conception；A2 status=ready、九阶段绑定和 run_id 均可读。P1 manifest 的 `bba81d35…`、handoff 的 `d48194db…` 仅为引用值，不冒充缺失本体重算；没有从构思 ready 推 HLD/LLD 已通过。HTML hash 匹配也不代替页面全部语义验收。

### 7.2 GitHub 只读收据

本次全状态列表取证时点：**2026-11-15 06:52:13 UTC**（本地 America/Los_Angeles 为 11月14日）。端点 `https://api.github.com/repos/innuama-coder/ai-novels/issues?state=all&per_page=100&page=1` 返回 HTTP 200、22 项、0 PR，无 next Link。随后对全部 22 个 number 单条 GET，全部成功，单条 body 与列表 body 完全一致；全部 open、comments=0。未做任何 ISSUE 写操作。

九条已发的创建时间均为 2026-11-14 UTC；正文哈希均匹配 ISSUES v1/v2 登记。标记使用 `duanxian-audit3-impl-001:DX3-Fnnn` 和完整 BASE，不通过新标记绕过去重。

| number / URL | created_at UTC | 本次完整正文 SHA-256 |
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

ISSUES 的三个 JSON fence 分别可解析为 schema 1.0、2.0、3.0-delta；前两版各19候选/9 created，delta 有3条 candidate_updates。自然语言与 delta 的 #17 未过门一致；#20 两目标问题也是两者共同存在，并非只读错旧版本。该核验确认记录存在和内容对应，不恢复未留存的历史 POST 事务或当时的发布前全量核查。

### 7.3 被验交付的身份固定

| 文件 | SHA-256（f3c69866 交付字节） |
| --- | --- |
| REPORT | `1179f594a913198d163ec504f6d45caf67a41a13e6f6d06f8dcc8cbbb388c728` |
| LEDGER | `f22c8bbfa04ec4e9521f857ad58c3b1010833c03b96e71a6bfa90c9a09ec7449` |
| ISSUES | `5060bf26b0bd56eb344723c468d424dc3e52b58ddfd54a2fa5dc2b5fd5118556` |
| PROPOSAL | `c55ce86fbbed543f8cf602f87e8a47f1a9c37e3c44902db0e3185956b8704428` |
| POINTER | `ed7635f92297953944e54b8dd90758582d9b5984bced1316c09e3b9273c5d888` |
| 定义书 | `5ec5c086c32874e017cb56e58f3906e4e6a59806f5ab8fad2971d2dcd311d268` |
| acc2 修正输入 | `439c6641f6e07c6117ab6cb1649fff800d64139330588d334a868b96609bae17` |

## A3/08 续接修正指令（仅交 Owner，不代执行）

### ACC-F015：区分 EV 同来源双入口与同值复用（续 ACC-F011）

- 违反：定义 §3.2、S03、R02/R06/R09/R11；A2 ACC-F011 的“逐对象语境和绑定、非等价语境核验”。
- 对象与原文：POINTER L284 把 CE/PROP/EV 均等同 §8 复用镜像；§4 G010/G015 的复用成员却为0，§8 七类也无 EV。
- 独立反例：A3 `/drilldown_index/3682` 与 `/3683` 同 source 不同 hash；扩查148个 EV 对全部不同，详 A3/02.2。
- 正确边界：SC 双入口证明来源展示关联，value_sha256 相同才支持值身份复用；二者均不证明缺失 P1 原值已读。
- 要求动作：在后续授权版本修正 §6 映射，将148组明确列为同来源但不等价；保留525个真同值复用对，不为凑数删除条目；同步报告/读账的覆盖闭合描述。
- 预期产物：可解析的 source→两侧 DI→各自 hash→复用/非复用分类，以及语境摘要；不需要公开或生成 P1 值体。
- 复验方法：从 BASE 按 source_id 分组，与按完整 value_sha256 分组的结果分开比对，要求EV=148个双入口、同值0，525真复用集合不变；再抽控制/阶段不同的样本。
- 影响与返回：A3 索引覆盖可信度、九目标全称声明；回 S03→S05→S08，不自动发布。

### ACC-F016：四列入口表恢复精确路径、回退根和阶段来源（续 ACC-F012）

- 违反：定义 S05/S06、R04/R06/R11；A2 ACC-F012 明确要求的四列表及精确路径核验。
- 对象与原文：REPORT L124 的统一 designer 后缀及“首根 ENGINE”；L125“模块可导入”；L128 三机器文件统归 A2 manifest。
- 独立反例：七个调用参数均带 engine/，第一个候选多拼一次 engine、第二候选命中；Q1/P1 真名不带 designer；A2 没有 hld-completion 引用。
- 正确边界：源码存在/可静态定位与实际导入、运行绑定是不同证据；HLD completion 缺失是独立阶段限度，不属于构思完成记录必含项。
- 要求动作：逐一列七个精确路径和三候选命中；把导入措辞降为静态存在；拆分 P1/handoff 与 HLD completion 的来源说明，检查报告、矩阵、读账同类表述。
- 预期产物：准确四列表，保留1290件engine在库、缺运行目录/migration/机器包、前缀差异不证明入口缺失这些已修正结论。
- 复验方法：AST 静态读取调用字符串，按 L43–48 依次拼根，对每个候选用 BASE tree/cat-file 验证；解析A2字段验证阶段归属。禁止 import 或生产执行来补证。
- 影响与返回：G09 的路径可得性和复算限度；回 S05→S06→S08。

### ACC-F017：#20 主候选单一目标与附带项分类闭合（续 ACC-F013）

- 违反：定义 §2.3、S06–S08、I02/I03/I04/R07/R11；A2 ACC-F013 要求单一可验关闭目标、各子项证据及自然语言/JSON一致。
- 对象与原文：ISSUES L106–110、L344；REPORT §8.1 #20；PROPOSAL #20。名为 single 的目标字段保留两个明确不同目标，附带项一并“归 #11/#12/#13”。
- 独立反例：计数修正无需决定K4/K6电话或会议室；会议载体采用声明不能修正文两次/七次。第比利斯时间、K6编号、名片无来源、字符缺损与既有三条的具体关闭条件不一一对应。
- 正确边界：允许只保留计数作为主候选，把载体待证项单独登记不发布；也允许承认整体目标门未过。无需自动拆发、不得擅改线上，外部待授权状态本身不扣分。
- 要求动作：作出一种明确当前分类，主候选只一个关闭目标；载体另有独立状态、证据限度和不发布理由；原附带项逐项给 disposition 与既有机制/关闭条件对应，未覆盖者如实待证、登记或范围外。
- 预期产物：可直接读出五门状态的当前候选与子项表；JSON能区分主候选、历史发布、独立观察、外部动作待授权。有效计数证据不丢失，撤回的传输/人数/面孔/地点不恢复。
- 复验方法：完整比对正文、meeting-room、shenyu、zhengbozhou相关条目及冻结#11/#12/#13；执行“只解决计数是否满足主目标”的反例测试，再检查自然语言/delta/提案一致。
- 影响与返回：#20、去重及候选总表；回 S06→S07→S08。本轮停止于 Owner 裁决，不执行新 LOOP。

## A3/09 RF、外部纠错及 Owner 移交

| 移交项 | 内容及处理边界 |
| --- | --- |
| RF-1（既有，minor） | 读账显式行区间数字与实际 EOF 的精度问题继续移交；不把数字不精确直接等同缺读，不用它判本次 FAIL。 |
| RF-2（既有，minor） | subject L19“带着真相”须区分原因层、终止事实与知骗，不自动推第一部确认受骗；本次没有替作者裁决。 |
| RF-3（既有，cosmetic） | 目标表实际定义§1.3、复验实际§6.3末段、ISSUES收据定位等交叉引用问题；不计入FAIL。 |
| RF-4（本次，minor） | #3 的“17件各3处LLD引用”不准确；实际17件各1处，其他HLD/风格引用不能充作LLD引用。核心迁移机制/17目标/五个风格指称不受影响，移交Owner修辞勘误。 |
| RF-5（本次，minor） | POINTER称DI“六字段”而实际七字段，source_anchor_id另在V6处理，未造成实际覆盖丢项；移交更正字段总数。 |
| RF-6（本次，minor） | LLD差异历史收据及17个hash未随交付可回读；已独立复现母本/成员/算法及差异行数，不能宣称见到了旧工作档案。建议后续给确定生成命令或嵌入摘要。 |
| 外部#14/#22 | 范围外工程扩展；PROPOSAL建议允许时关闭并说明，`OWNER_PENDING`，本次不执行。 |
| 外部#15/#16 | 收窄引用失配/撤回违规强断言或证据不足关闭，`OWNER_PENDING`；保留当前作者与历史层区别。 |
| 外部#17/#19/#20 | #17待证、#19限定历史适配、#20保留计数核心及当前分类残余；后续外部动作须Owner另授权，本文不授新编辑/评论/关闭权限。 |
| 外部#18/#21 | #18历史终包状态核心与#21计数不符可保留；成因与体验判断不越证据，若需澄清仍另授权。 |
| manual-review | `OWNER_PENDING`。由Owner确认记录完整与边界；本验收不代签。该状态不代替本次已证内部FAIL。 |
| 续作裁决 | 本轮终验仍FAIL，ACC-F015–F017完整移交。Owner可另行授权定向修正或暂停；本次不请求扩大权限，不自行启动修正。 |

## A3/10 机械交付与可复验摘要

本文满足冻结机械检查的 UTF-8、至少6000字节、ACC-F011/ACC-F014/总体判定关键词及秘密模式要求；实际命令输出、提交与远端核验在本次执行记录中保存。提交前、提交后均须按冻结 spec 的同一 argv 检查；另用 index/HEAD diff 确认相对 `f3c69866…` 只有本文新增，不能仅以尚未提交时空的 HEAD diff 作为白名单证明。

最低独立重现方法如下（只读，不运行项目代码）：

```python
import collections, json, subprocess
B = '92573f1cca40f37cee04d2beb8708ff33ba603d6'
raw = subprocess.check_output(['git', 'show', B + ':duanxian/conception-approved/human-review-report.json'])
d = json.loads(raw)
by_source = collections.defaultdict(list)
by_hash = collections.defaultdict(list)
for index, row in enumerate(d['drilldown_index']):
    by_source[row['source_id']].append((index, row))
    by_hash[row['value_sha256']].append(index)
ev = [rows for source, rows in by_source.items() if source.startswith('EV-')]
assert len(ev) == 148 and all(len(rows) == 2 for rows in ev)
assert all(rows[0][1]['value_sha256'] != rows[1][1]['value_sha256'] for rows in ev)
assert len(by_hash) == 4077
assert sum(len(rows) == 2 for rows in by_hash.values()) == 525
print('EV different-value pairs=148; genuine same-value pairs=525')
```

本次完成的是终验并交付 FAIL 记录：输入/覆盖组、事实/反证组、候选/去重组、全局硬约束/移交组均形成可回读结果。未受影响修正保留其源定位，原 acc/acc2 FAIL 历史不抹去；无任何外部纠错、小说修改、生产重跑或 Owner 签认发生。
