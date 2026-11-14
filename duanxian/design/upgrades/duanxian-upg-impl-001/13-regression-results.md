# 13 · 实施自检与回归记录（regression results）

- 包：`duanxian-upg-impl-001`。本文件是**实施者自检**记录；第三步（duanxian-upg-acc-001）必须独立重做而非照抄本表。
- 允许值（两列各自取值，互不覆盖）：`PASS / FAIL / BLOCKED_OWNER / BLOCKED_EVIDENCE / DEFERRED_ENGINEERING / PENDING_WRITING`。不得把未执行记为 PASS。
- 绑定：本表结果绑定本包首版候选提交与 `manifest.json`（15 文件实际字节实算）；修订后旧结果失效。
- 机械核对：自检器共 73 项检查（C1–C12：存在性/JSON/CSV 结构与行数/07 时序/交叉引用闭合/12 映射/历史指称语境/秘密扫描/manifest 复算/git 白名单），除依赖本表定稿的项外全部通过；本表定稿并再生成 manifest 后复跑为 **TOTAL=73 FAIL=0**（见 §C-3 复现记录）。

## A. 执行记录（定义书 §5 步骤 0–10，逐步登记）

| 步骤 | 输入版本 | 实际动作 | 产出 | 结果 | 未决依赖 |
| --- | --- | --- | --- | --- | --- |
| 0 确认契约与候选版本 | definition_commit=4ce28e8a；spec/PROMPT 已读；BASE=92573f1；快照 sha=1e35e5e1… | 全文读定义书与契约；核对分支/写入白名单/网络与凭据范围；核验定义验收证据（JOB #2317 ENDED、judge r1 PASS note_35873、Owner 三项确认）；未沿用任何旧 ACK nonce | 00 §baseline/§write_scope | 完成：白名单＝仅 U/ 下 16 新文件，git status 仅 U/ 未跟踪 | 无 |
| 1 权威与证据缺口登记 | E01–E03、E17、#7 | 核对 approved/conception/ready/run/manifest/handoff 引用与 hash（六件逐一 sha256 复算一致）；机器本体未取得→只读人审材料形成控制投影，标明非 P1 | 00、01（72 控制，零重复） | 完成：#7 机器 basename 在 Git 树 1444 跟踪路径零命中复核属实 | #7 受控取证（GAP-MACHINE） |
| 2 原 ISSUE 与历史处置 | 13 条快照原文＋E 原件 | 逐条现场/需求/证据/裁决登记；17 路径＋5 语义映射（对快照表与 BASE 树双重核对）；#5 替代声明；#6 歧义保留 | 02（16 处置行）、03（22 行）、10 初版、13 框架 | 完成：22/22 行落点存在且 BASE 统一 | 无 |
| 3 决策提案 | D01–D03、E02 人物/事件控制 | 写成可审定备选＋推荐＋影响＋受影响节点；未批事实封入条件分支 | 11、00/12 的 decision dependency | 完成：三决策决定栏全空待签；#11 按定义书授权走设计删除路径（非 Owner 决策，11§附注） | D01/D02/D03 签认（GAP-OWNER） |
| 4 人物/能力/证据责任 | 01、02、11、E02 | 周岚保护与参与脱钩；程予安同意边界；授权/核验/执行/保管分工；接口/记忆/推断/核验规则与反证 | 04（R0–R17）、05（E1–E6） | 完成 | 无 |
| 5 因果与知识联合模型 | 04/05、批准主轴、E02 storylines | 逐事件 06（14 事件）；逐知识变化 07（31 行，发送≤接收≤使用机械校验通过）；旧编号多对多 alias | 06、07 | 完成：C4 时序校验 0 违例 | 无 |
| 6 终局与披露 | 06/07、UPG-CTRL-STORY-SUSPENSE、D03 | 08 状态机（S0–S7）＋披露表；POV 截断点映射旧 C5/PRD-S15/K9 功能差异；两种旧终局作负例 | 08、07 终局对象更新 | 完成 | D03（路径 A 下无阻塞） |
| 7 场景规格与逐段适配 | 04–08、11、完整旧正文与素材 | 六重点单元展开＋主轴覆盖；10 号表 28 行逐段完成（E11 九段＋:245–271 全覆盖核对通过）；#11 删除十秒依赖；#12 两分支不模糊 | 09、10 完整版 | 完成：10 全表 writing_status=PENDING_WRITING 如实 | 写作授权（PENDING_WRITING） |
| 8 追踪与消费包组装 | 00–11 稳定版 | 12 逐字段映射（72 控制＋13 ISSUE，unmapped=[]）；消费禁用/替代边界；README 唯一入口；manifest 候选（实际字节实算） | README、12、manifest 候选 | 完成：C5/C6 交叉引用闭合 0 悬空 | 无 |
| 9 实施自检与消费演练 | 冻结候选、13 条 ISSUE、§6 用例 | 路径/hash/字段/引用/顺序核对（70 项）；正负例语义检查（NEG×7 隔离副本注入＋正例×5）；消费演练（仅从 12 重建，6 组探针） | 13 完整版、manifest 更新 | 完成：NEG 7/7 检出、正例 5/5 成立、演练 6/6 PASS | 第三步独立验收 |
| 10 提交/推送/移交 | 自检候选 | git diff --check；白名单核对；只暂存 16 路径；remote-agent 署名提交；凭据推送（禁 force、禁回显）；回查远端 SHA | 路径×提交号、manifest hash、哨兵 | 本表定稿后立即执行；提交号在交付报告中报告，不回写本文件（避免 manifest 失配） | — |

## B. REG-01..REG-13 双状态回归表

| 回归 ID／ISSUE | 可核验通过判据（定义书 §6.2） | 本轮方法与证据定位 | design_result | original_closure_result |
| --- | --- | --- | --- | --- |
| REG-01／#1 | 工程修复后七 runtime＋三测试入口全部解析、装载与运行通过（枚举 run.py 七调用与三测试 ROOT/ENTRYPOINT，逐项留命令与退出码） | 本轮不运行修复验收：隔离登记＝00 §write_scope 排除七路径＋02-UPG-LEG-15 处置＋12§blocks「#7 机器本体」关联登记；C12 确认本轮零触碰这些路径 | PASS（隔离与交接准确；未宣称工程修复） | DEFERRED_ENGINEERING |
| REG-02／#2 | 同一提交的 novel-* SKILL 集合计数与两份导览一致，或取消固定计数（BASE 枚举=82） | BASE=92573f1 树枚举证据留存于 02-UPG-LEG-15（82 计数与两导览口径）；本轮零改动 README/导览；C12 白名单通过 | PASS（证据留存与交接准确） | DEFERRED_ENGINEERING |
| REG-03／#3 | 17 源路径逐一映射存在目标；五指称逐项比较，部分/缺失如实；无伪造规则（附完整 22 行结果表） | 03 逐行对快照表＋BASE 树双重核对（存在性＋定位符）；五语义行读取 R07 :14/:16 与 HLD §9/§10 原文比对，部分/缺失如实标注；22 行结果表见 §B-2 | PASS（22/22 有逐条证据；无「均通过」式省略） | DEFERRED_ENGINEERING（旧文件原状保留，追溯由旁挂 03 承载；旧文档自身整改未授权） |
| REG-04／#4 | 工程维护后全部预期文件 text/eol 符合策略且字节与 manifest 兼容 | 本包面：manifest 对 15 文件实际 UTF-8 字节实算，C11 复算一致；.gitattributes 风险（engine 前缀缺样本→unspecified）留存于 02-UPG-LEG-15/00，不样本推全量 | PASS（新包 hash 兼容与风险留存；不宣称策略已修） | DEFERRED_ENGINEERING |
| REG-05／#5 | 旧 P1/open 原文保持；替代记录逐项旧范围→新产物/版本/hash/状态；新字段追踪实际闭合；不借替代放行新准入 | 02§C 五项替代声明（旧范围→本包产物）；12 逐字段追踪（72 控制反向可查，unmapped=[]）；00 §formal_hld_admission 四门全 blocked——未放行任何新准入；旧 P1/open 原文零改动（C12） | PASS（替代记录与隔离准确） | BLOCKED_EVIDENCE（正式 HLD 人审与 #7 受控取证未发生） |
| REG-06／#6 | v3/L33 v2/实际评审对象三方对照有受控核实或勘误说明；历史版本与 pending/blocked 保留 | 02§D 三栏对照（v3 声明／L33 v2／实际对象）保留歧义不裁决；无全局字符串替换；历史 pending/blocked 状态原样（02§C） | PASS（歧义隔离准确，未借新包 v1.0 宣称已查清） | BLOCKED_EVIDENCE（核实依赖机器 run 元数据，#7 同源） |
| REG-07／#7 | 受控访问说明、确切 run/版本、包清单/hash、来源/批准/validation/execution 快照与最新状态；授权正式复验通过 | 00 §machine_package_evidence 登记五件受控引用（stage-completion/package-manifest/development-handoff/revision-037/validation 各 sha256）＋GAP-MACHINE＋02-UPG-LEG-16；Git 树 1444 路径零命中复核；未取得本体→不复验、不关闭 | PASS（受控引用与缺口声明准确） | BLOCKED_EVIDENCE（本体不可得；原请求保持未关闭） |
| REG-08／#8 | 新人物/事件/信息/场景无「周岚参与袭击所以被保护」前提；无辜主体性、同意及公共救援同时成立；新责任事实有批准 | 反向追踪：04§R3＋06-UPG-E-05＋07（原因层对象）＋09-UPG-S-PROTECTION＋10-M-01/02/03 全链走读无参与边（C7 语境检查＋演练 B＋NEG-AUTHORITY 注入检出）；主体性=协查/同意/拒绝；公共救援并行（E01-05/06） | PASS（D01-A 候选全链成立；B 分支条件封存，未写确定稿） | BLOCKED_OWNER（D01 未签；无条件关闭被阻。正文另处 PENDING_WRITING） |
| REG-09／#9 | 新 S06/S13 对应功能及细化单元只用文字/有限记忆；沈逾感官未自动共享；现实细节有合法到达证据（E11 :91 过去片段为相容正例） | 05§E1 白名单四输入＋黑名单（击键遥测等）；09-AWAKE/REVIEW 合法输入行；07 逐信息源反查（C4 时序零违例）；:91 相容正例=10-UPG-M-16 retain-with-boundary；NEG-CHANNEL 注入检出 | PASS（能力边界与到达证据闭合；文本承接另行同验） | PENDING_WRITING |
| REG-10／#10 | 决定、读者/沈逾获知、执行者、记录披露、关停状态分别明确；不早泄、不自关闭；无活动备份、不保证复活 | 08§A S0–S7 逐状态呈现契约＋§B POV 截断（UPG-E-10.1）＋§D 三方知识差＋§E REC 披露表；07 终局对象（IO-17..23）时序走读；执行者=沈逾（S4）；NEG-ENDING 注入（执行者正确仍 FAIL）检出 | PASS（设计状态机闭合；旧正文未改如实） | PENDING_WRITING |
| REG-11／#11 | 精确十秒不再是无来源输入；若保留则发送者/事实依据/文本/接收/推断顺序与权限全部成立 | 采用删除依赖路径（定义书 §3.3 授权的设计扩张，11§附注）：05§E3 零「先用后到」；09-REVIEW 室内细节/十秒时长不传入；唯一合法通道=07-UPG-IO-11（沈逾有限口头自述，发送/接收/使用三级登记）；10-UPG-M-21 改写指令 | PASS（设计图与场景闭合；无旁白补丁） | PENDING_WRITING（旧 :284–347 适配落地后须真实回归） |
| REG-12／#12 | 所选人物版本及披露规则有依据；每次确认、显名、沈逾知情有材料点/权限/时序；素材与对应文本无相反要求 | 判据明示「D02 待批则 BLOCKED_OWNER」：A/B 分支已备齐（04§R15 三层结论＋R16 载荷表；07-IO-24.1/24.2/24.3；10-M-22/26 分支素材整组登记；隐名规则未当生效控制引用）；职务换名继承被显式禁止（NEG-IDENTITY 注入检出） | BLOCKED_OWNER（分支结构完备，但「所选版本」须 Owner 签认方可无条件成立） | BLOCKED_OWNER |
| REG-13／#13 | 主观片段、假设、外部取证与核验结果分列；无完整可寻址记忆/像素补全直接锁定事实；推理与权限一致 | 05§E2 状态机（subjective_fragment→hypothesis→…，externally_supported 只能由外部产生）＋E4 取证四层责任＋E 概率/像素禁令（C7 语境校验）；04§R15 主观/客观分离；E11 :95/:155/:187–199/:343/:363–369 逐段由 10-M-16..19/28 承载；NEG-MEMORY 注入检出 | PASS（能力边界可验证；未虚构外部核验已发生） | PENDING_WRITING（授权适配后对真实文本回归） |

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

注入串在冻结候选中均不存在（生成前断言）；七例全部检出，无一漏报。

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

复现记录：本表定稿并再生成 manifest 后，对最终冻结候选复跑自检器与 NEG 七例，结果与本表一致（TOTAL=73 FAIL=0；NEG 7/7 检出）。

## D. 缺口与未决清单

| 缺口 | 内容 | 阻塞的回归（original_closure 列） | 解阻条件 |
| --- | --- | --- | --- |
| GAP-MACHINE（#7） | 三机器本体 basename 不在 Git 树；正式复验与 v2/v3 评审对象核实不可做 | REG-05、REG-06、REG-07 → BLOCKED_EVIDENCE | Owner 交付受控机器材料并授权复验 |
| GAP-OWNER（D01/D02/D03） | 三决策未签认；依赖节点保持条件分支，不得写确定稿 | REG-08、REG-12 → BLOCKED_OWNER | Owner 在 11§决定栏签认（含 B 分支的另行批准） |
| GAP-WRITING | 正文写作未授权；10 号表 28 行全部 PENDING_WRITING | REG-09、REG-10、REG-11、REG-13 → PENDING_WRITING | 写作授权后按 09/10 落地并同验 |
| GAP-ENGINEERING（#1/#2/#3/#4） | 工程留存项未获修复授权 | REG-01、REG-02、REG-03、REG-04 → DEFERRED_ENGINEERING | 工程侧另行授权处置 |

各缺口互不覆盖：设计列通过不以任何方式替代原始关闭；反之亦然。

## E. 缺陷及修订记录（候选形成过程，全部发生于冻结与提交之前）

1. `03` 行 7 BASE 列曾误植 `9257…-INVALID` 占位串 → 当场修正为正确 BASE 哈希（行内注释同步清理）。
2. `07` 三处生成缺陷 → 脚本校验发现后修正：表头 `witheld_reason`→`withheld_reason`；UPG-IO-15 的 event_id 误植串复位；UPG-IO-21/22/23 的 sent_at 由「E-11.3（封存）」改为「E-10.4（内容形成）」（封存点移至 received_at，保持发送≤接收≤使用）。
3. `01` 生成期控制 ID 前缀重复（SUBJECT/RHYTHM 各 ×2）与七个 E01 平面指针统一误标 L81 → 修正为独立前缀（LINE-n/CONN-n/MEVT-n）与 L81–L87 逐行指针；修后 72 控制零重复。
4. 演练脚本初版把 REC 披露探针误标到 #13（实为 #10）且 E3 断言过字面 → 修正演练侧断言；包内文件经核对无对应错误（演练缺陷如实记录，不回写为包缺陷）。

LOOP 修订计数：首次实施完成，**0 次定向修订**；包版本 v1.0。
