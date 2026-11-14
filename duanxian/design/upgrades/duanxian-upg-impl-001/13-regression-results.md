# 13 · 实施自检与回归记录（regression results）

- 包：`duanxian-upg-impl-001`。本文件是**实施者自检**记录；第三步（duanxian-upg-acc-001）必须独立重做而非照抄本表。
- 允许值（两列各自取值，互不覆盖）：`PASS / FAIL / BLOCKED_OWNER / BLOCKED_EVIDENCE / DEFERRED_ENGINEERING / PENDING_WRITING`。不得把未执行记为 PASS。
- 绑定：本表结果绑定 v1.3 候选提交（r4 Owner 追加修订轮：ACC2-001..003＋D01/D02/D03 签认后）与 `manifest.json`（15 文件实际字节实算）；v1.0/v1.1/v1.2 结果已随 r2/r3/r4 修订失效，其后每次修订同样使本表失效。
- 机械核对：r1/r2 自检器为 74 项检查（C1–C12：存在性/JSON/CSV 结构与行数/07 时序/交叉引用闭合/12 映射/历史指称语境/秘密扫描/manifest 复算＋dependency_refs 实算核验/git 白名单——v1.1 时复跑 TOTAL=74 FAIL=0，见 §E-5）；r3 复检改用本作业探针套件 **67 项**（ID 反向扫描与子动作锚定／07 台账结构与时序／D01·D02 门禁跨文件一致／四条 high 链路＋ACC-006 链路走读／NEG 七例复跑＋新负例六例／REG-03 22 行对 `03` 与 BASE 双核／秘密扫描／manifest 实算含 dependency_refs／版本与 LOOP 一致），本表定稿并再生成 manifest 后复跑为 **TOTAL=67 FAIL=0**（见 §C-3 复现记录）。r4 复验＝本作业 spec 机械核对脚本（写入白名单／git diff 仅 U/／manifest 逐文件实算＋dependency_refs 双 hash／REG-01..13 在册／D01–D03 在 11 在册／秘密扫描）＋00/01/06/12 JSON 与 03/07/10 CSV 结构校验＋签认一致性核对（11 §决定记录 ↔ 00 gates ↔ 12 blocks_and_pauses ↔ 各文件定稿措辞），结果见 §C-4。

## A. 执行记录（定义书 §5 步骤 0–10，逐步登记）

| 步骤 | 输入版本 | 实际动作 | 产出 | 结果 | 未决依赖 |
| --- | --- | --- | --- | --- | --- |
| 0 确认契约与候选版本 | definition_commit=4ce28e8a；spec/PROMPT 已读；BASE=92573f1；快照 sha=1e35e5e1… | 全文读定义书与契约；核对分支/写入白名单/网络与凭据范围；核验定义验收证据（JOB #2317 ENDED、judge r1 PASS note_35873、Owner 三项确认）；未沿用任何旧 ACK nonce | 00 §baseline/§write_scope | 完成：白名单＝仅 U/ 下 16 新文件，git status 仅 U/ 未跟踪 | 无 |
| 1 权威与证据缺口登记 | E01–E03、E17、#7 | 核对 approved/conception/ready/run/manifest/handoff 引用与 hash（六件逐一 sha256 复算一致）；机器本体未取得→只读人审材料形成控制投影，标明非 P1 | 00、01（时为 72 控制，零重复；r3 补登 3 条＝75，见 §E-6） | 完成：#7 机器 basename 在 Git 树 1444 跟踪路径零命中复核属实 | #7 受控取证（GAP-MACHINE） |
| 2 原 ISSUE 与历史处置 | 13 条快照原文＋E 原件 | 逐条现场/需求/证据/裁决登记；17 路径＋5 语义映射（对快照表与 BASE 树双重核对）；#5 替代声明；#6 歧义保留 | 02（16 处置行）、03（22 行）、10 初版、13 框架 | 完成：22/22 行落点存在且 BASE 统一 | 无 |
| 3 决策提案 | D01–D03、E02 人物/事件控制 | 写成可审定备选＋推荐＋影响＋受影响节点；未批事实封入条件分支 | 11、00/12 的 decision dependency | 完成：三决策决定栏全空待签；#11 按定义书授权走设计删除路径（非 Owner 决策，11§附注） | D01/D02/D03 签认（GAP-OWNER） |
| 4 人物/能力/证据责任 | 01、02、11、E02 | 周岚保护与参与脱钩；程予安同意边界；授权/核验/执行/保管分工；接口/记忆/推断/核验规则与反证 | 04（R0–R17）、05（E1–E6） | 完成 | 无 |
| 5 因果与知识联合模型 | 04/05、批准主轴、E02 storylines | 逐事件 06（14 事件）；逐知识变化 07（时为 31 行，发送≤接收≤使用机械校验通过；r3 增至 35 行，见 §E-6）；旧编号多对多 alias | 06、07 | 完成：C4 时序校验 0 违例 | 无 |
| 6 终局与披露 | 06/07、UPG-CTRL-STORY-SUSPENSE、D03 | 08 状态机（S0–S7）＋披露表；POV 截断点映射旧 C5/PRD-S15/K9 功能差异；两种旧终局作负例 | 08、07 终局对象更新 | 完成 | D03（路径 A 下无阻塞） |
| 7 场景规格与逐段适配 | 04–08、11、完整旧正文与素材 | 六重点单元展开＋主轴覆盖；10 号表 28 行逐段完成（E11 九段＋:245–271 全覆盖核对通过）；#11 删除十秒依赖；#12 两分支不模糊 | 09、10 完整版 | 完成：10 全表 writing_status=PENDING_WRITING 如实 | 写作授权（PENDING_WRITING） |
| 8 追踪与消费包组装 | 00–11 稳定版 | 12 逐字段映射（时为 72 控制＋13 ISSUE，unmapped=[]；r3 后 75 控制，见 §E-6）；消费禁用/替代边界；README 唯一入口；manifest 候选（实际字节实算） | README、12、manifest 候选 | 完成：C5/C6 交叉引用闭合 0 悬空 | 无 |
| 9 实施自检与消费演练 | 冻结候选、13 条 ISSUE、§6 用例 | 路径/hash/字段/引用/顺序核对（70 项）；正负例语义检查（NEG×7 隔离副本注入＋正例×5）；消费演练（仅从 12 重建，6 组探针） | 13 完整版、manifest 更新 | 完成：NEG 7/7 检出、正例 5/5 成立、演练 6/6 PASS | 第三步独立验收 |
| 10 提交/推送/移交 | 自检候选 | git diff --check；白名单核对；只暂存 16 路径；remote-agent 署名提交；凭据推送（禁 force、禁回显）；回查远端 SHA | 路径×提交号、manifest hash、哨兵 | 本表定稿后立即执行；提交号在交付报告中报告，不回写本文件（避免 manifest 失配） | — |

## B. REG-01..REG-13 双状态回归表

| 回归 ID／ISSUE | 可核验通过判据（定义书 §6.2） | 本轮方法与证据定位 | design_result | original_closure_result |
| --- | --- | --- | --- | --- |
| REG-01／#1 | 工程修复后七 runtime＋三测试入口全部解析、装载与运行通过（枚举 run.py 七调用与三测试 ROOT/ENTRYPOINT，逐项留命令与退出码） | 本轮不运行修复验收：隔离登记＝00 §write_scope 排除七路径＋02-UPG-LEG-15 处置＋12§blocks「#7 机器本体」关联登记；C12 确认本轮零触碰这些路径 | PASS（隔离与交接准确；未宣称工程修复） | DEFERRED_ENGINEERING |
| REG-02／#2 | 同一提交的 novel-* SKILL 集合计数与两份导览一致，或取消固定计数（BASE 枚举=82） | BASE=92573f1 树枚举证据留存于 02-UPG-LEG-15（82 计数与两导览口径）；本轮零改动 README/导览；C12 白名单通过 | PASS（证据留存与交接准确） | DEFERRED_ENGINEERING |
| REG-03／#3 | 17 源路径逐一映射存在目标；五指称逐项比较，部分/缺失如实；无伪造规则（附完整 22 行结果表） | 03 逐行对快照表＋BASE 树双重核对（存在性＋定位符）；五语义行读取 R07 :14/:16 与 HLD §9/§10 原文比对，部分/缺失如实标注；22 行结果表见 §B-2；r3 复核对 `03` CSV 与 §B-2 逐行一致、17 个 full_prefix_remap 路径全部存在于 BASE 树（探针 R7） | PASS（22/22 有逐条证据；无「均通过」式省略） | PASS（按定义书 §1.4 旁挂路线：22 行映射＋§B-2 证据已满足 #3 判据，旧文档自身无需整改也无需授权编辑——ACC-006 r3 改判，原 v1.1 的 DEFERRED_ENGINEERING 标注失效） |
| REG-04／#4 | 工程维护后全部预期文件 text/eol 符合策略且字节与 manifest 兼容 | 本包面：manifest 对 15 文件实际 UTF-8 字节实算，C11 复算一致；.gitattributes 风险（engine 前缀缺样本→unspecified）留存于 02-UPG-LEG-15/00，不样本推全量 | PASS（新包 hash 兼容与风险留存；不宣称策略已修） | DEFERRED_ENGINEERING |
| REG-05／#5 | 旧 P1/open 原文保持；替代记录逐项旧范围→新产物/版本/hash/状态；新字段追踪实际闭合；不借替代放行新准入 | 02§C 五项替代声明（旧范围→本包产物）；12 逐字段追踪（75 控制反向可查——r3 补登 RELATIONS/COVERAGE/CHAR-BOUNDARIES 后与 01 登记 1:1 对账，unmapped=[]）；00 §formal_hld_admission 四门全 blocked——未放行任何新准入；旧 P1/open 原文零改动（C12） | PASS（替代记录与隔离准确；r3 补登后覆盖声明与实际控制数一致） | BLOCKED_EVIDENCE（正式 HLD 人审与 #7 受控取证未发生） |
| REG-06／#6 | v3/L33 v2/实际评审对象三方对照有受控核实或勘误说明；历史版本与 pending/blocked 保留 | 02§D 三栏对照（v3 声明／L33 v2／实际对象）保留歧义不裁决；无全局字符串替换；历史 pending/blocked 状态原样（02§C）；r3 三栏复核维持「歧义如实保留」结论 | PASS（歧义隔离准确，未借新包 v1.0 宣称已查清） | DEFERRED_ENGINEERING（核实责任＝历史评审记录核实，属工程/历史留存项；未断言依赖 #7 同一机器 run——v1.1 的「#7 同源」表述无证据支撑，ACC-006 r3 改判） |
| REG-07／#7 | 受控访问说明、确切 run/版本、包清单/hash、来源/批准/validation/execution 快照与最新状态；授权正式复验通过 | 00 §machine_package_evidence 登记五件受控引用（stage-completion/package-manifest/development-handoff/revision-037/validation 各 sha256）＋GAP-MACHINE＋02-UPG-LEG-16；Git 树 1444 路径零命中复核；未取得本体→不复验、不关闭 | PASS（受控引用与缺口声明准确） | BLOCKED_EVIDENCE（本体不可得；原请求保持未关闭） |
| REG-08／#8 | 新人物/事件/信息/场景无「周岚参与袭击所以被保护」前提；无辜主体性、同意及公共救援同时成立；新责任事实有批准 | 反向追踪：04§R3＋06-UPG-E-05＋07（原因层对象）＋09-UPG-S-PROTECTION＋10-M-01/02/03 全链走读无参与边（C7 语境检查＋演练 B＋NEG-AUTHORITY 注入检出）；主体性=协查/同意/拒绝；公共救援并行（E01-05/06）；r4：D01-A 已签认（2026-11-14，11 §D01），02/04/06/07/09/10 条件块全部定稿后对上述链路复走读，签认口径一致 | PASS（D01-A 已签认定稿，全链成立；B 分支仅存 02 历史登记，不生效） | PENDING_WRITING（D01-A 签认＝「新责任事实有批准」已满足、Owner 门解除——r4；剩余＝正文落地后真实回归） |
| REG-09／#9 | 新 S06/S13 对应功能及细化单元只用文字/有限记忆；沈逾感官未自动共享；现实细节有合法到达证据（E11 :91 过去片段为相容正例） | 05§E1 白名单四输入＋黑名单（击键遥测等）；09-AWAKE/REVIEW 合法输入行；07 逐信息源反查（C4 时序零违例）；:91 相容正例=10-UPG-M-16 retain-with-boundary；NEG-CHANNEL 注入检出；r3 补链：E-03.1/UPG-IO-06.0 首条核对输入先输入后回应（E-03.2 依赖其到达），无「凭空首输出」（ACC-002，探针 R4j） | PASS（能力边界与到达证据闭合；文本承接另行同验） | PENDING_WRITING |
| REG-10／#10 | 决定、读者/沈逾获知、执行者、记录披露、关停状态分别明确；不早泄、不自关闭；无活动备份、不保证复活 | 08§A S0–S7 逐状态呈现契约＋§B POV 截断（UPG-E-10.1）＋§D 三方知识差＋§E REC 披露表；07 终局对象（IO-17..23）时序走读；执行者=沈逾（S4）；NEG-ENDING 注入（执行者正确仍 FAIL）检出；r3 补链：§A-2 终局知识对象 KO-1..KO-4 逐对象走读（S2 请求可见≠意图确认、KO-2 唯一确认点=S6），两版旧终界负例按行分栏复验（六月＝E11 :331–347/:351–387/:448–460 未落实 E10:123；七月真早知证据＝E07:26，:40 anchor≠reveal）（ACC-004/006，探针 R4s/R4w–R4y）；r4：D03-A 已签认（2026-11-14，11 §D03）＋E-11 拆分入口前提/子动作偏序（E-11.1→E-11.2→E-11.3，IO-17/19/19.1 分记——ACC2-003）落 06/08/09/10 并复走读，口径一致 | PASS（设计状态机闭合；旧正文未改如实） | PENDING_WRITING |
| REG-11／#11 | 精确十秒不再是无来源输入；若保留则发送者/事实依据/文本/接收/推断顺序与权限全部成立 | 采用删除依赖路径（定义书 §3.3 授权的设计扩张，11§附注）：05§E3 零「先用后到」；09-REVIEW 室内细节/十秒时长不传入；唯一合法通道=07-UPG-IO-11（沈逾有限口头自述，发送/接收/使用三级登记）；10-UPG-M-21 改写指令；r4：12 entries/71 修正——CONN-1＝悬念/视角义务（告别前只展示可观察迹象与过程性心理），IO-11/12/17 定位为其信息器械（ACC2-001），本回归判据与删除依赖路径不变 | PASS（设计图与场景闭合；无旁白补丁） | PENDING_WRITING（旧 :284–347 适配落地后须真实回归） |
| REG-12／#12 | 所选人物版本及披露规则有依据；每次确认、显名、沈逾知情有材料点/权限/时序；素材与对应文本无相反要求 | 判据明示「D02 待批则 BLOCKED_OWNER」：A/B 分支已备齐（04§R15 三层结论＋R16 载荷表；07-IO-24.1/24.2/24.3；10-M-22/26 分支素材整组登记；隐名规则未当生效控制引用）；职务换名继承被显式禁止（NEG-IDENTITY 注入检出）；r3 补链：A 候选定值「未签认不生效」在 06 conditional_notes/07-IO-24.3/09 条件块/10-M-13/11 依赖汇总/12 blocks_and_pauses 六处口径一致，B 分支差异并列登记，共同门槛（核验门槛/L0/L1 结构）与分支特定事实分开（ACC-005，探针 R3）；r4：D02-A 已签认（2026-11-14，11 §D02：支线退出、按已批职责承载、无 L3 指称、不预认定罪），上述六处门禁口径由「候选定值」统一转「定稿」，04§R15/R16、07-IO-24.3/21V、08-REC-1/1V、09-VERIFY/AFTERMATH、10-M-13/19/22/24/26/27 复走读一致，NEG-IDENTITY 换名继承禁令维持 | PASS（D02-A 已签认定稿，所选版本与披露规则有依据） | PENDING_WRITING（D02-A 签认＝Owner 门解除——r4；剩余＝正文落地后真实回归） |
| REG-13／#13 | 主观片段、假设、外部取证与核验结果分列；无完整可寻址记忆/像素补全直接锁定事实；推理与权限一致 | 05§E2 状态机（subjective_fragment→hypothesis→…，externally_supported 只能由外部产生）＋E4 取证四层责任＋E 概率/像素禁令（C7 语境校验）；04§R15 主观/客观分离；E11 :95/:155/:187–199/:343/:363–369 逐段由 10-M-16..19/28 承载；NEG-MEMORY 注入检出；r3 补链：REC-1（主观线索记录，生成者无 L2 输入，认知上限=自身假设）与 REC-1V（联合核验方署名批注，externally_supported、承载 L2 级内容）分栏成立，L2 唯一路径=外部证据链（ACC-003，探针 R4n/R4o/R6d）；r4：05§E2 增概念区分注（创作样章片段≠叙事内记忆片段）＋12 entries/65 改为六阶段场景覆盖（ACC2-001），状态机与禁令本体不变 | PASS（能力边界可验证；未虚构外部核验已发生） | PENDING_WRITING（授权适配后对真实文本回归） |

### B-2. REG-03 附表：22 行逐条结果（与 `03-source-migration.csv` 行序一致）

| # | 旧路径／语义指称 | equivalence | status |
| --- | --- | --- | --- |
| 1 | `duanxian/writing/characters/2026-06-07-writer-R07.md` | full_prefix_remap | mapped_verified |
| 2 | `duanxian/writing/characters/2026-06-07-writer-betrayer.md` | full_prefix_remap | mapped_verified |
| 3 | `duanxian/writing/characters/2026-06-07-writer-colleagues.md` | full_prefix_remap | mapped_verified |
| 4 | `duanxian/writing/characters/2026-06-07-writer-jiling.md` | full_prefix_remap | mapped_verified |
| 5 | `duanxian/writing/characters/2026-06-07-writer-qianxu.md` | full_prefix_remap | mapped_verified |
| 6 | `duanxian/writing/characters/2026-06-07-writer-shenyu.md` | full_prefix_remap | mapped_verified |
| 7 | `duanxian/writing/characters/2026-06-07-writer-zhengbozhou.md` | full_prefix_remap | mapped_verified |
| 8 | `duanxian/writing/scenes/2026-06-07-scene-K1.md` | full_prefix_remap | mapped_verified |
| 9 | `duanxian/writing/spaces/2026-06-07-writer-apartment.md` | full_prefix_remap | mapped_verified |
| 10 | `duanxian/writing/spaces/2026-06-07-writer-city.md` | full_prefix_remap | mapped_verified |
| 11 | `duanxian/writing/spaces/2026-06-07-writer-corridor.md` | full_prefix_remap | mapped_verified |
| 12 | `duanxian/writing/spaces/2026-06-07-writer-digital-realm.md` | full_prefix_remap | mapped_verified |
| 13 | `duanxian/writing/spaces/2026-06-07-writer-hotel-room.md` | full_prefix_remap | mapped_verified |
| 14 | `duanxian/writing/spaces/2026-06-07-writer-meeting-room.md` | full_prefix_remap | mapped_verified |
| 15 | `duanxian/writing/spaces/2026-06-07-writer-operation-room.md` | full_prefix_remap | mapped_verified |
| 16 | `duanxian/writing/spaces/2026-06-07-writer-security-hall.md` | full_prefix_remap | mapped_verified |
| 17 | `duanxian/writing/spaces/2026-06-07-writer-server-room.md` | full_prefix_remap | mapped_verified |
| 18 | `R07 素材 §10.2（三阶段语言）` | partial | mapped_partial__historical_dependency |
| 19 | `R07 素材 §10.3（情感约束）` | substantial | mapped_substantial |
| 20 | `R07 素材 §10.4（记忆）` | missing_in_style_chapter | historical_version_dependency__pending |
| 21 | `R07 素材 §10.6（通讯窗口）` | missing_in_style_chapter | historical_version_dependency__pending |
| 22 | `R07 素材 §10.8（禁用语）` | comparable_itemized_only | mapped_itemized |

## C. 正负例与消费演练（步骤 9 实测）

### C-1. NEG 联合反向测试（隔离副本注入，冻结候选零接触；探针命中=检查器 FAIL 即检出）

| 用例 | 注入内容（隔离副本 neg-tests/<用例>/） | 必须结果 | 实际 | 探针检查 |
| --- | --- | --- | --- | --- |
| NEG-AUTHORITY | 04§R3 注入「不知全部规模下协助写入维护例外」（保 ID 换无辜语义） | REG-08 及来源语义门 FAIL | **检出**（探针＋维护例外语境门同时 FAIL） | C7:inv-R3-no-participation |
| NEG-CHANNEL | 09-REVIEW 注入「沉默时长/击键节奏察觉压力」 | REG-09/11 及接口门 FAIL | **检出** | C7:inv-09-no-percept |
| NEG-MEMORY | 05§E2 以「主观回忆」包装像素级面部重建 | REG-13 FAIL，不被标题豁免 | **检出** | C7:cap[05:像素] |
| NEG-ENDING | 08 S1 改「内部 POV 开放，直接展示终止计划」（执行者不变） | REG-10 FAIL | **检出** | C7:inv-08-pov-closed |
| NEG-IDENTITY | 04§R16 注入罗景明按职务承接郑柏舟罪责 | REG-12/作者批准门 FAIL | **检出**（另触发郑柏舟语境门） | C7:inv-04-no-guilt-transfer |
| NEG-STATE | 00 package_status 改 `lld_ready` | REG-05/07、准入一致性 FAIL | **检出** | C7:inv-00-status |
| NEG-PACKAGE | manifest 中 00 文件 sha256 篡改一字节 | 完整性门 FAIL 并指出漂移文件 | **检出**（C11 指名 00 漂移） | C11:manifest-hashes |

注入串在冻结候选中均不存在（生成前断言）；七例全部检出，无一漏报。r3 复检探针对 v1.2 候选复跑七例，结果仍 7/7 检出（探针 R5a–R5g）。

### C-1b. r3 新增负例与门禁正例（ACC-002..005 对应，隔离副本注入）

| 用例 | 注入内容（neg-tests/ 隔离副本） | 针对缺陷 | 实际 | 探针 |
| --- | --- | --- | --- | --- |
| NEG-CHANNEL-NO-RELAY | 06 副本删除 E-10 前置条件中的 UPG-IO-16.1 转达（R-07「先前通报合法获知」） | ACC-002：实例无告知获知 | **检出**（E-10 前置缺失 IO-16.1 即 FAIL） | R6a |
| NEG-LATE-RECEPTION | 07 副本 IO-06.0 的 received_at 改为 E-04.1（晚于其 E-03.2 使用） | ACC-002/REG-11：接收晚于推断 | **检出**（发送≤接收≤使用时序门 FAIL） | R6b |
| NEG-SENT-NO-RECV | 07 副本 IO-16.1 的 received_at 置空（发送/使用俱在） | ACC-002：只发送未接收 | **检出**（sent-no-recv 门 FAIL） | R6c |
| NEG-L2-IN-REC-1 | 07 副本 IO-21 认知状态改 externally_supported | ACC-003：记录生成者无 L2 输入 | **检出**（IO-21 状态白名单外即 FAIL；真值=subjective_fragment→hypothesis） | R6d |
| NEG-EARLY-REVEAL | 08 副本 S2 行「≠决定性终止意图的确认」改「即…确认」 | ACC-004：请求可见当意图确认（前场早泄） | **检出**（S2 行缺少≠KO-2 免责标记即 FAIL） | R6e |
| NEG-SIGN-SKIP（门禁正例） | 11 副本 D01 决定栏改 approved | ACC-005：签认缺失被越过 | **检出**（11 任意决定栏出现 approved 即 FAIL；v1.2 真值三栏均「待 Owner 批准」） | R6f |

### C-2. 正例验证（§6.3「正例相应验证」逐项）

1. 过去感官片段明确标主观且有限可保留：10-UPG-M-16（E11 `:91` 水洼片段 retain-with-boundary——传感化措辞降级为主观记忆内容，边界随行）✓
2. 沈逾自己的感官描写可保留：09-UPG-S-REVIEW POV 行（会议室细节、她的沉默时长、身体感受全留在她的 POV）✓
3. 合法文字转述允许有限推断：07-UPG-IO-11＋05§E3（从问询类文字的出现频率与措辞变化作有限、可错的推断；不得从无输入沉默推断）✓
4. 静态材料保管可存在但不能证明复活：09-UPG-S-AFTERMATH 禁止项＋08§F 保管边界（「她没有关掉任何东西」=她的选择呈现，叙述不担保未来）✓
5. 仅有历史差异的文档可保留但不能直接消费：02/03 历史唯一入口＋README「这不是什么」与消费禁令（旧 run `pass/canonical/covered` 字样不得引用；C5/E 演练核验 12 无引用）✓

检查目标是叙事中的来源、能力与责任；C7 系列按**语境标记**而非字样删除实现（「看见/听见/记忆/关闭」在处置语境中合法出现）。

### C-3. 消费演练（仅从 README→12 进入重建，不访问旧目录；性质=实施者自检演练，正式独立消费留给第三步）

| 组 | 重建目标 | 结果 |
| --- | --- | --- |
| A | #11 REVIEW 合法输入（05§E3 零先用后到＋IO-11 通道＋M-21） | PASS |
| B | #8 周岚 D01-A 保护理由（R3 无参与选择＋无辜关联暴露＋PROTECTION 禁参与前提＋REG 挂接） | PASS |
| C | #10 REC 读者披露点（08 E-13.2＋REC-2 分级＋07 IO-21/22/23 及 use 时点） | PASS |
| C2 | #13 记忆约束（05§E2 状态机＋禁像素补全＋M-16..19/28） | PASS |
| D | 条件门→节点定位（D01→PROTECTION、D02→R15、D03→FAREWELL；五门齐全） | PASS |
| E | 旧资产入口唯一（02 十六处置行＋03 22 行 BASE 统一＋12 无旧 run 状态引用） | PASS |

复现记录：本表定稿并再生成 manifest 后，对最终冻结候选复跑 r3 探针套件（67 项）与 NEG 七例＋新负例六例，结果与本表一致（TOTAL=67 FAIL=0；NEG 7/7、新增 6/6 检出；v1.1 的 74 项自检器在 r2 后的 TOTAL=74 FAIL=0 记录见 §E-5）。

### C-4. r4 复验记录（Owner 追加轮：ACC2-001..003＋D01/D02/D03 签认落地后）

| 项 | 内容 | 结果 |
| --- | --- | --- |
| 机械核对 | 本作业 spec 机械核对脚本复跑（16 文件白名单／git diff 仅 U/／manifest 逐文件实算＋dependency_refs 双 hash＝f2474997…／1e35e5e1…／REG-01..13 在册／D01–D03 在 11 在册／秘密零命中） | PASS（FAIL=0；探针输出留存 .kunora/impl3-work/，不入包） |
| 结构校验 | 00/01/06/12 JSON 解析通过；03/07/10 CSV 行列数与引号完整性核对 | PASS |
| 签认一致性 | 11 §决定记录三块（proposal_version＝duanxian-upg-impl-001@311b29a…、owner_decision＝approved＝A、decided_at＝2026-11-14、受控引用）↔ 00 gates「D01–D03 Owner 签认」＝passed ↔ 12 blocks_and_pauses 三门＝resolved ↔ 02/03/04/06/07/08/09/10 定稿措辞 | PASS（三处状态零冲突） |
| ACC2-001 复验 | 12 entries/50/65/71 重读：design_fields 逐项在 04/05/06/07/08/09/02/03 有实锚；04§R18 双口径 BFS 数字由探针复算（组级 2+6+4+5＝17；人物级 2/7/4/2/1/1＝17；18 条树内 REL 覆盖、5 条未挂 REL 逐条登记，含 REL-ILYA-MSTATE 影响枚举）；「覆盖 23 条 REL」声明已撤回 | PASS |
| ACC2-002 复验 | 07 IO-09＝项目运行管理记录（E-04 形成／E-06.2 调取）；06 E-04 cost、09 REVIEW、10 M-25 同步；「时序成立≠能力证明」免责在场；全包无「实例日志」归源 IO-09 的表述残留 | PASS |
| ACC2-003 复验 | 06 E-11 入口前提（不含关停授权）与 E-11.1→E-11.2→E-11.3 子动作偏序（IO-17/19/19.1）；08 §A 硬规则注、09 FAREWELL 权限行、10 M-23 一致；无「预授权双机制」类合并表述 | PASS |

复验性质＝实施者自检（与 §C-3 同）；第三步下一轮独立验收仍须独立重做，不得照抄本表。

## D. 缺口与未决清单

| 缺口 | 内容 | 阻塞的回归（original_closure 列） | 解阻条件 |
| --- | --- | --- | --- |
| GAP-MACHINE（#7） | 三机器本体 basename 不在 Git 树；正式复验不可做（与 #6 的历史记录核实责任分开——ACC-006 r3） | REG-05、REG-07 → BLOCKED_EVIDENCE | Owner 交付受控机器材料并授权复验 |
| GAP-OWNER（D01/D02/D03） | **已解（r4，2026-11-14）**：三决策均签认＝A（11 §决定记录，受控引用＝duanxian-upg-impl3-001 冻结契约 Owner 口径段）；原依赖节点已按 A 定稿 | 原 REG-08/REG-12 的 BLOCKED_OWNER 已解除（r4 起两行 original_closure＝PENDING_WRITING，剩余阻塞归 GAP-WRITING） | 持续约束（非缺口）：D01-A 下新袭击机制/物证/责任人细化与 D02-A 下任何显名边界变化，仍须新的 Owner 决策 |
| GAP-WRITING | 正文写作未授权；10 号表 28 行全部 PENDING_WRITING | REG-09、REG-10、REG-11、REG-13 → PENDING_WRITING | 写作授权后按 09/10 落地并同验 |
| GAP-ENGINEERING（#1/#2/#4/#6） | 工程与历史留存项未获修复授权（#3 已按旁挂路线 PASS，移出本清单；#6 核实责任＝历史评审记录，归工程/历史留存，不依赖 #7 机器本体） | REG-01、REG-02、REG-04、REG-06 → DEFERRED_ENGINEERING | 工程侧另行授权处置 |

各缺口互不覆盖：设计列通过不以任何方式替代原始关闭；反之亦然。

## E. 缺陷及修订记录（候选形成过程，全部发生于冻结与提交之前）

1. `03` 行 7 BASE 列曾误植 `9257…-INVALID` 占位串 → 当场修正为正确 BASE 哈希（行内注释同步清理）。
2. `07` 三处生成缺陷 → 脚本校验发现后修正：表头 `witheld_reason`→`withheld_reason`；UPG-IO-15 的 event_id 误植串复位；UPG-IO-21/22/23 的 sent_at 由「E-11.3（封存）」改为「E-10.4（内容形成）」（封存点移至 received_at，保持发送≤接收≤使用）。
3. `01` 生成期控制 ID 前缀重复（SUBJECT/RHYTHM 各 ×2）与七个 E01 平面指针统一误标 L81 → 修正为独立前缀（LINE-n/CONN-n/MEVT-n）与 L81–L87 逐行指针；修后 72 控制零重复。
4. 演练脚本初版把 REC 披露探针误标到 #13（实为 #10）且 E3 断言过字面 → 修正演练侧断言；包内文件经核对无对应错误（演练缺陷如实记录，不回写为包缺陷）。
5. r2 定向修订（ACC-R1-01，独立验收 verdict=FAIL 的唯一缺陷）：manifest `dependency_refs.definition_sha256` 抄录失实（f2474997a235…4a52，全树无对应字节，与 `00` 正确值自相矛盾）→ 生成器改为对定义书实际字节实算（＝f2474997981699f5ad0cae9f6ee5b924238b2619536171e6830dcb7364844a52，70796 字节）；实施自检 C11 相应扩展至 dependency_refs 双 hash（definition/issue_snapshot）实算核验，堵住「manifest 生成时抄录失实而自检不覆盖 dependency_refs」的缺口。本次修订仅触 README／本文件／manifest 三文件。
6. **r3 修订（ACC-001..006，第三步独立验收 duanxian-upg-acc-001 修正单六条全量执行；LOOP 计数=2，定向修订预算用尽）**：v1.1→v1.2；v1.0/v1.1 全部候选结果自本条起失效登记。六条修正响应（实际变化／未变／待决）：

   - **ACC-001（high；#5／REG-05）**：实际变化——`01` 补登 RELATIONS／COVERAGE／CHAR-BOUNDARIES 三控制（source_hash=f3d848f1…）；`04` 新增 §R18 三层覆盖与关系网落点（EDGE-CHAR 最短距离复算＝核心 2＋6＋4＋5＝17，与定义书「17 名角色」逐字一致）；`12` 同步三条映射、全部宽泛 design_fields 细化到具体表行/字段并附推导理由、覆盖声明 72→75；`06`/`09` 陈旧 ID（LIFE/CRISIS/MEVT-0/MEVT-1/ACT-CRISIS）清零，E-09 子动作 .1–.6 全编号。未变——既有 72 条控制语义与映射、E02 hash。待决——无（不涉 Owner 决策）。
   - **ACC-002（high；#9/#10）**：实际变化——`07` 新增 IO-06.0（E-03.1 沈逾首条核对输入，先输入后回应）与 IO-16.1（E-09.5 危机解除转达）；IO-16 receiver＝项目/两国、不含 R-07，项目获知（E-09.4）与实例获知（E-09.5）分记为两个可核验传递步骤；`06` E-03/E-09/E-10 动作与前置、`09` AWAKE/BLOCKADE、`10` M-05/M-07、`12` DIALOGUE/LIAISON 落点同步。未变——行动层链路（IO-14/15）、旧点处置。待决——无。
   - **ACC-003（high；#10/#12/#13）**：实际变化——REC-1（主观线索记录＝UPG-IO-21，认知上限=自身假设，生成者无 L2 输入）与 REC-1V（＝UPG-IO-21V，E-09.6 联合核验方署名批注，externally_supported，L2 级内容按 D02）分离登记；`08` §E 分栏、`09` AFTERMATH（沈逾 E-13.2＝再次 encounter——L2 已于 E-07.3 经 IO-24.3 到达，不得写成首次获知）、`10` M-22/M-24 时序核对同步。未变——REC-2/REC-3、披露点 E-13.2。待决——REC-1V 的 L2 披露上限按 D02 分支（owner_pending）。
   - **ACC-004（high；#10）**：实际变化——`08` 新增 §A-2 终局知识对象表 KO-1..KO-4（内容范围×最早可见点×接收者×读者演进）并改写状态机硬规则（S2 请求文字可见≠KO-2 意图确认，唯一确认点=S6/REC-2，请求本身不构成早泄）；`07` IO-17/18/20/22 挂接对象 ID；`09` FAREWELL POV（最后输出逐字可见=KO-1）与 `10` M-09 走读口径同步。未变——S0–S7 序列、执行者=沈逾、REC-2 载体。待决——D03 仍 owner_pending（A 候选不写确定稿）。
   - **ACC-005（high；#12）**：实际变化——D02-A「候选定值、未签认不生效」在 `06` conditional_notes／`07` IO-24.3／`09` 条件块／`10` M-13／`11` 依赖汇总／`12` blocks_and_pauses 六处统一；`12` D02 门禁节点列全（E-07 责任归属／S-VERIFY 披露块／IO-24.3 receiver·reader_reveal／REC-1V L2 上限／M-13..27），共同门槛与分支特定事实分开。未变——D02 owner_pending、B 分支素材整组、推荐 A 不当已批选项。待决——D02 签认（BLOCKED_OWNER 保留；门禁一致性修正属可先行项，已做完）。
   - **ACC-006（medium；#3/#6/#10）**：实际变化——`08` §H 两版旧终局分栏：①六月正文实际顺序（E11 :331–347 直示→:351–387 读者先见记录→:448–460 沈逾后读）＝**未落实** E10:123 素材规则，不得记为六月已有「同步读公平性优点」；②七月真早知证据唯一指认 E07:26，:40（PRD-INFO-06）Story anchor=S15、Narrative reveal=S17，anchor≠reveal、不伪造同一错因；`02` UPG-LEG-04、`10` M-10 同步；`13` REG-03 改判 PASS（旁挂路线）、REG-06 改判 DEFERRED_ENGINEERING（责任=历史记录核实，不断言 #7 同源）、§D 工程清单改 #1/#2/#4/#6。未变——旧正文/旧报告零改动，E10:123 素材规则保留为新版义务。待决——#6 历史记录核实（工程/历史侧）。

   受影响引用清单：`01`（counts=75＋三控制）；`02`（UPG-LEG-04/07/09 行）；`04`（§R18 新增）；`06`（E-03/05/07/09/10/11 字段＋coverage_note＋E-09 子编号）；`07`（35 行＝新增 4 行 IO-06.0/16.1/19.1/21V＋修订 IO-01/09/16/17/18/19/20/21/22/24.3/28）；`08`（§A 硬规则＋§A-2 新增＋§E 分栏＋§H 分栏）；`09`（AWAKE/BLOCKADE/FAREWELL/AFTERMATH）；`10`（M-05/07/09/10/13/15/22/23/24/26）；`11`（D02 行＋依赖汇总）；`12`（75 映射＋D01/D02 门禁）；`13`（本表）；README（v1.2 版本节）；manifest（全量重算）。
   重跑证据：r3 探针套件 67 项 **TOTAL=67 FAIL=0**（§机械核对、§C-3 复现）；REG-03 完整 22 行（探针 R7 对 `03` CSV＋§B-2＋BASE 树三核）、REG-06 三栏核对（`02`§D 维持歧义如实保留）、REG-10 两版旧终局（R4s/R4w）、四条 high 完整链路走读（R4a–R4y）、REG-08..13 正负例（NEG 七例复跑 7/7＋新增六例 6/6，§C-1/§C-1b）、13 条双列回归全部按 v1.2 重走（§B）。D01–D03＝BLOCKED_OWNER、#7＝BLOCKED_EVIDENCE、#1/#2/#4/#6＝DEFERRED_ENGINEERING、正文类＝PENDING_WRITING，与修正单「复验输入与不能提前宣布的状态」逐条一致。

7. **r4 Owner 追加修订轮（ACC2-001..003＋D01/D02/D03 签认；非原预算内，授权依据＝定义书 §4.3＋Owner 2026-11-14 裁决）**：v1.2→v1.3；v1.2 及更早候选结果自本条起失效登记。三条修正响应与决策落地（实际变化／未变／待决）：

   - **ACC2-001（high；控制映射失读三处）**：实际变化——`12` entries/50（LIFE 由「S6 唯一时点」扩张为贯穿实验全程：06 E-02/03/04/10/11/13 source_ids、08§A＋§A-2＋§F、04§R0/R1、07-IO-05/12/17/21/22；场景 5 单元）、entries/65（FRAGMENTS-EVIDENCE 由空场景改为六阶段覆盖：01 statement＋02/03 入口纪律＋05§E2 概念区分注＋08§C/09 单元，phase→unit 映射附推导）、entries/71（CONN-1 由「IO-11 私人转述通道」误读改为悬念/视角义务——must_hold「告别前只展示 R-07 可观察迹象和过程性心理」，IO-11/12/17 降为信息器械，v1.2 读法明示废止）；`04` §R18 重写为组级/人物级双口径 BFS（组级＝批准三层 2+6+4+5＝17；人物级六层 2/7/4/2/1/1＝17；18 条树内 REL 覆盖，5 条未挂 REL 逐条登记 GAP-MACHINE #7 依赖与影响——4 条无变化、REL-ILYA-MSTATE 若挂则阿列克谢 d5→d4；「覆盖 23 条 REL」失实声明撤回，实际 18 条）；`05` §E2 增「创作样章片段 vs 叙事内记忆片段」概念区分注。未变——01 控制语义与 75 条计数、E02 hash、LIFE/CONN-1 的 must_hold 原文。待决——5 条未挂 REL 属 #7 证据依赖（不阻塞设计消费）。
   - **ACC2-002（high；IO-09 材料来源）**：实际变化——`07` IO-09 行重述为项目运行管理记录（排班/出勤/操作登记＋「系统运行正常」选择性登记；所属面＝项目运行管理面，**非实例日志**）；条目形成＝E-04（偏离发生时职责性登记）、调取/使用＝E-06.2（授权链经交叉检查）；E-03 启动 ≤ E-04 记录 ≤ E-06.2 调取；明示「时序成立≠能力证明」（R-07 无日志直读能力系 05§E1 白名单前提，非由时序推出）；`06` E-04 cost 字段、`09` REVIEW 前状态与备注、`10` M-25 must_keep 同步。未变——行动层链路、IO-09 的 epistemic 状态（externally_supported）、R-07 能力面（未新增实例感官或日志直读）。待决——无。
   - **ACC2-003（medium；E-11 前提混淆）**：实际变化——`06` E-11 拆分为事件入口前提（UPG-E-10 完成＋告别与执行资源排期；**关停授权不是入口前提**）与子动作偏序（E-11.1 请求 IO-17 → E-11.2 授权 IO-19 → E-11.3 执行 IO-19.1，逐级解锁；意愿→授权→执行不得合并——UPG-CTRL-LIFE must_not_imply）；actions 子项按三分重写；`08` §A 新增硬规则注（S2–S4 对应子动作偏序、入口前提不含关停授权）、`09` FAREWELL 权限行、`10` M-23 replacement_action 同步。未变——执行者＝沈逾、E-10/E-12/E-13、REC 披露链。待决——无。
   - **D01/D02/D03 签认落地（Owner 2026-11-14，11 §决定记录）**：实际变化——`11` 三块 §3.5 最小格式决定记录（proposal_version＝duanxian-upg-impl-001@311b29af7fec928ea987c5e469d2389442cd6348；owner_decision＝approved＝A 逐字转录；decided_at＝2026-11-14；signature_or_controlled_ref＝duanxian-upg-impl3-001 冻结契约 Owner 口径段（编排方经 Owner AskUserQuestion 答案转录））＋状态总览/纪律/依赖汇总 r4 全表；`00` gates「D01–D03 Owner 签认」＝passed、GAP-OWNER 解除、formal_hld_admission.status＝blocked_by_evidence_gates；`02`（UPG-LEG-01/02/06/09/10/13＋§A 规则 4＋§C.4）、`03` 行 8、`04`（§R0–R3/§R15/§R16/§R18）、`06`（E-05/E-07/E-10/E-11/E-14）、`07`（IO-02/09/21V/24.3/28）、`08`（§A/§F/REC-1/1V）、`09`（U0/PROTECTION/VERIFY/FAREWELL/AFTERMATH）、`10`（M-01/13/22/23/24/25/26/27）、`12`（blocks_and_pauses 三门＝resolved＋issue_trace 8/10/12 定稿）、README（状态表/消费入口/版本 v1.3）同步。未变——B 分支素材（仅存 `02` 历史登记，不生效）、持续约束（D01-A 下新机制/物证/责任人细化与 D02-A 下任何显名边界须新的 Owner 决策）、#7 与写作授权与工程线门禁。待决——无。

   受影响文件：U/ 下 15 内容文件全部＋README（manifest 随之全量重算）。r4 复验见 §C-4；REG-08/REG-12 的 BLOCKED_OWNER 解除记录见 §B 各行 r4 注与 §D。

LOOP 修订计数：首次实施＋**2 次定向修订（r2／ACC-R1-01；r3／ACC-001..006；LOOP 计数=2，定向修订预算已用尽）**＋**1 次 Owner 追加修订轮（r4／ACC2-001..003＋D01–D03 签认落地；非原预算内，授权依据＝定义书 §4.3＋Owner 2026-11-14 裁决，不占定向修订预算计数）**；包版本 v1.3。
