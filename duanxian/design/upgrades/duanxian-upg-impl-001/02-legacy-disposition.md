# 02 · 旧资产处置与历史隔离（legacy disposition）

- 包：`duanxian-upg-impl-001`（设计适配候选，非正式准入凭证）。
- 规则：旧链资产**仅经本表**进入本包消费；未被本表列为 `retain` 的内容不得直接引用。历史文件原字节零改动；本表只决定「新版设计中如何对待旧内容」。
- 处置值：`retain`（按当前边界保留消费）／`adapt`（改写后以新节点承载）／`retire`（退出新版设计，仅存历史）／`pending`（处置依赖 Owner 决策或证据，条件分支）。
- 行号与 JSON Pointer 绑定 BASE=92573f1。控制 ID 见 `01-control-register.json`；旧段逐行指令见 `10-text-adaptation-map.csv`；路径/语义映射见 `03-source-migration.csv`。

## A. 总原则（对每条旧资产生效）

1. 权威分层：`duanxian/novel-goals.md`＋`duanxian/conception-approved/`（2026-08-17 批准）为当前权威；六月 PRD/LLD/素材/正文与七月 HLD 全部是历史链（UPG-CTRL 见 00 的 authority 节）。
2. 旧链内部的 `pass`、`canonical`、`covered`、`已完成` 字样不迁移为本版通过结论（E01 L71 明示；定义书根因 A）。
3. 路径可达≠内容获准复用（#3 裁决）；语义相容≠编号可直接继承（E15 旧 C 编号，见 UPG-CTRL-NC-05）。
4. 需要新核心事实（新袭击机制、旧责任人替代、新增配角、终局新机制）时一律进 D01–D03 条件分支（`11-owner-decisions.md`），未签认前相关节点保持 `BLOCKED_OWNER` 语义，不得进入无条件 handoff。

## B. 逐资产处置表

| ID | 旧资产（BASE 路径·版本/时间） | 问题段 | 处置 | 原因（绑定控制） | 替代路径／新版节点 | 未决门 |
| --- | --- | --- | --- | --- | --- | --- |
| UPG-LEG-01 | `duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/canonical-world-facts-v3.0.md`（v3.0，2026-07 HLD run） | `:38–44,59–73` 周岚=认证分包商审计员、主动写入维护例外接入袭击因果；周启明=其弟／裂隙网络行动者；纬线利益链；D+58 报复性气象攻击等时间线事实 | **pending（D01）**：参与链整体退出候选；`retire` 部件＝周岚参与袭击的技术机制与全部时间线事实（D+26/D+57/D+58 等）；`retain` 部件＝两条反证限度（周岚「不知道完整规模」`:68`；复杂依恋「不能直白恋爱化」`:73`，只能以回避姓名/照片/记忆中断表现） | 参与链与 UPG-CTRL-ZHOULAN（无辜亲属、独立生活、不得暗示参与袭击）和 UPG-CTRL-E01-05（亲属主体性）直接冲突；「不知道完整规模」是保留周岚知情灰区的历史反证限度，与「无辜且未参与」不矛盾，故保留为刻画边界而非事实 | 新版周岚设计：`04-character-responsibility.md` §周岚；保护原因层：`06-causal-and-event-map.json` 事件层＋`07-information-ledger.csv` 原因层对象；场景：`09-scene-specs.md` UPG-S-PROTECTION/UPG-S-AFTERMATH；替代保护理由=亲属关联风险＋协查/同意/拒绝的主体性，不依赖参与 | D01（推荐 A：不继承参与机制）；若 Owner 选 B，须另行批准责任来源与完整因果，本表相应行升级为 adapt+新批准源 |
| UPG-LEG-02 | 同 run `artifacts/04-character-system.md`（HLD v4 的七月重建） | `:20` HLD-04-04 周岚=`protected_participant`（主动维护例外）；`:21,34` HLD-04-05 特殊认知处置组（韩惟/郑柏舟/顾栖）及 fact trace 承接 | `:20,34` **pending（D01）**随 UPG-LEG-01；`:21` 特殊认知处置组三角色 **retire**（不在当前 17 人批准表 E02 中；启用需 Owner 新批） | 周岚行同上；韩惟/郑柏舟/顾栖无 E02 批准条目，属旧版自设人物（#12：未列名不自动证明非法，但启用必须经批准——不走「机械替换职务」捷径） | 周岚行→`04` §周岚；旧处置组功能（止损审查/项目价值/程序闭合）由已批角色承载：罗景明（权限/保密/复盘）、唐黎（技术核验）、监督与责任室环境（UPG-CTRL-OVERSIGHT）；见 `04` §职责承载表 | D01；若需保留旧角色名，另提 Owner 决策（现无此提案） |
| UPG-LEG-03 | `duanxian/design/runs/prd/2026-07-07-duanxian-prd-workflow/artifacts/03-trunk-scenes.md`（2026-07 PRD，S00–S18＋36 单元） | `:23` PRD-S06 R-07 对当下光线/声音/时间迟疑回应；`:30` PRD-S13「隔离系统里听见了她的沉默」；`:53–54,67–74` 细化单元（S06-U01/U02、S13-U01/U02、S15/S16-U01/U02） | `adapt` | 与 UPG-CTRL-DIALOGUE／UPG-CTRL-11（只有文字与受限记忆，沈逾侧感官不自动传入）冲突（#9）；S15 设局＋读者提前知终止（`:26`）另与 UPG-CTRL-STORY-SUSPENSE 冲突 | 初醒/审查功能由 `09` UPG-S-AWAKE／UPG-S-REVIEW 重建（S06 保留沈逾看到设备的**外部**体验，R-07 只回应收到的文字；S13 沉默由沈逾 POV 表现）；终局单元由 UPG-S-FAREWELL 重建（无设局、无提前披露）；逐行指令见 `10` | 无（#9 设计层可闭合；正文落地=PENDING_WRITING） |
| UPG-LEG-04 | 同 run `artifacts/05-information-flow.md` | `:26–28` S15 读者提前知终止设计/S16 研究员执行/S17 事后知骗；`:40` PRD-INFO-06 private_motive 提前 visible；PRD-INFO-05 complete_cause concealed | `adapt`（信息边界表框架 `retain` 为方法参考；具体行全部重排） | 读者提前披露违反 UPG-CTRL-STORY-SUSPENSE（告别前不展示决定性终止意图）与 UPG-CTRL-NC-03（公平隐瞒）；「研究员被设局执行」与 E01 主线（沈逾执行告别）冲突（#10） | 新版知识时序整体重建于 `07-information-ledger.csv`（reader_reveal 列逐对象控制）＋`08-ending-and-pov.md` 披露表；旧 S15–S17 功能并入 UPG-S-FAREWELL/UPG-S-AFTERMATH | 无（设计层）；D03 只约束是否新增机制（本包未新增） |
| UPG-LEG-05 | `duanxian/design/specs/lld/scenes/2026-06-07-scene-K9.md`（六月 LLD） | `:24–33` K9=自主终结、内部 POV、压力 10/10；`:71–78` POV 服从 HLD v4、真相不越 K5/K8 顺序 | `adapt` | 「自主终结」的**选择自主性**保留（UPG-CTRL-CHAR-AGENCY、UPG-CTRL-R07 自主选择结束当前实例），但「自行执行关闭」违反 UPG-CTRL-CORE（不能自行终止）与 E01 终局（沈逾执行）；内部 POV 直示终止过程违反 UPG-CTRL-STORY-SUSPENSE | K9 功能拆分：决定形成（外部迹象+过程性心理，`08` 状态机 S1–S3）／意愿表达（UPG-S-FAREWELL）／授权与执行（沈逾，`06` UPG-E-11）／技术核验（唐黎，UPG-E-12）／记录披露（`08` 披露表＋`07` 记录对象）；旧 K 编号只作 alias | D03（不新增机制路径下无阻塞） |
| UPG-LEG-06 | `duanxian/writing/characters/2026-06-07-writer-R07.md`（六月写作素材） | `:13–16` LLD/HLD 引用错位（§10.2/10.3/10.4/10.6/10.8）；`:67–91,241–253` 自行启动关闭序列；`:90` 推理结论「确认了身份」；`:325` K8 身份确认；`:338` 不识面孔名字 | 引用错位 `adapt`（经 `03` 五行映射）；自关闭段 `adapt`（同 UPG-LEG-05 路径）；身份确认段 `pending`（D02） | 引用错位=#3；自关闭=#10；「确认身份→用户【她】」的确认深度与 D02 的披露上限绑定（#12） | 映射→`03-source-migration.csv`；自关闭→`10` 行 R07-closure；身份→`04` §身份识别结论分层＋`07` 显名权限对象；素材级写作约束由 `08`/`09` 重述 | D02 |
| UPG-LEG-07 | `duanxian/writing/spaces/2026-06-07-writer-digital-realm.md` | `:56–63` 终结前先关闭其他处理路径/完全沉默被清空；`:123` 技术记录不提前揭示（读者与她一起读到）；`:13–14` 引用错位 | 记录不提前揭示 `retain`（与 UPG-CTRL-STORY-SUSPENSE 同向，升为 `08` 披露表正式规则）；自行关闭路径 `adapt`；引用 `adapt`（`03`） | 「先关闭其他路径」仍是被执行方自关闭叙事（#10），改为请求结束+外部执行后该段整体重构；`:123` 与新版读者时序完全一致 | 披露规则→`08` §记录披露表（对象 UPG-IO-REC-1/2/3）；关闭路径→`10` 行 E10-closure | 无（D03 路径 A 下） |
| UPG-LEG-08 | `duanxian/novel-text/2026-06-07-duanxian-novel.md`（508 行旧正文，草稿） | 全部终局与感知段（`10` 号表逐行列出：`:91,95,155,187–205,278–280,284–347,351–387,409–443,448–476`，另 `:245–271` 击键压力列为接口审查候选） | `adapt`（整体为历史草稿；本包不改正文，只出逐段适配指令；`writing_status` 全部 PENDING_WRITING） | 正文属写作阶段产物（E01 判界：形成可发表叙事文字=写作）；本作业授权仅设计层 | 逐段冲突类型/替代动作/保留/删除/验证预期→`10-text-adaptation-map.csv`；场景级重建→`09` | 写作授权（另议）；D01/D02 影响对应行 |
| UPG-LEG-09 | `duanxian/writing/characters/2026-06-07-writer-betrayer.md`＋`2026-06-07-writer-zhengbozhou.md` | betrayer `:15,40,76–88,102` 不出场/门禁交叉→「内部人员。身份未锁定」/K10 只知有一个内部的人；zhengbozhou `:211` 姓名不向读者披露（最高识别度=项目主管）、`:260` 验证项、`:235` 十秒沉默（郑线） | **pending（D02）**：两分支并存登记（隐名分支/退出支线分支），推荐 A=支线退出、功能由已批角色承载；未签认前不固定任一分支 | 隐名方案（E12/E13）与显名正文（E11 `:365,466`）相反（#12）；D02 未决前任何「确定凶手/删角/换名」都越权 | 两分支知识台账（识别上限×接收者×材料点）→`07`（UPG-IO-ID-* 对象组）＋`04` §身份识别结论分层；`10` 行 E11-187/E11-351/E11-448 按分支给出替代动作 | D02（BLOCKED_OWNER：依赖节点的无条件消费） |
| UPG-LEG-10 | `duanxian/design/specs/lld/characters/2026-06-07-character-betrayer.md` | `:24–29` 显名必须推迟到 LLD 确认的材料点之后 | `retain`（作为**条件分支**的方法规则保留；与 E12 隐名规则并列登记，不合并） | 「材料点后显名」与 E12「永不显名」是旧链内部两种不同方案（#12 根因），不得假装一致；新版若走显名分支则本规则生效，若走退出分支则仅历史 | 分支登记→`04` §身份识别结论分层；`07` 显名权限字段 | D02 |
| UPG-LEG-11 | `duanxian/design/specs/2026-06-06-digital-life-novel-design.md`（六月构想） | `:12` 前序任务记忆被完整注入早已存在的人造数字生命体；`:25–26` 可接收完整人类意识结构化数据（记忆+情感+性格+价值观作为内容层） | `retire`（完整注入/完整意识内容层前提）；保留「以顾衡记忆为起点」的启动事实（由批准源直接承载，不经本文件） | 与 UPG-CTRL-E01-01（记忆为片段、顾衡已亡、新判断属 R-07）＋UPG-CTRL-MEMORY（主观片段、非可检索录像/客观数据库）冲突（#13） | 新版记忆模型→`05-capability-and-evidence.md` §记忆触发与缺口（状态机 subjective_fragment→…）；旧正文对应段→`10` 行 E11-091/095/155 | 无（批准源已覆盖，无事实缺口） |
| UPG-LEG-12 | `duanxian/design/workflow-docs/duanxian-narrative-contract.md`（v1.1，2026-07-21） | `:53–73` POV 分配表；`:107–118` 记忆/回忆/历史信息规则；N1–N6 披露台账 | `retain-with-boundary`（方法层保留；旧 C 编号不直接继承——UPG-CTRL-NC-05） | 与批准控制相容（E01 §四.2 引为历史链相容方法）；但 E01 L97 明示不能宣称已与当前 P1 绑定 | POV 截断点重映射→`08` §POV 退出点（旧 C5 功能→新版事件 UPG-E-10 意图形成时点）；记忆规则→`05` §3；披露台账方法→`07` reader_reveal | 无 |
| UPG-LEG-13 | 七月 HLD run 三件：`…/artifacts/12-hld-integrity-report.md`、`final-hld-package.md`、`manifest.md` | integrity `:25,57` HLD-TRACE-CLOSURE P1/open；`:32` 语义过/形式追踪败；`:33` 人审 v2.0；`:34` LLD blocked；package `:20–24` fail/pending_required/blocked_revision_required；manifest `:11–15` pending_hld_human_review＋canonical v3.0 唯一事实源 | `retire`（作为准入门）＋**显式替代声明**（见 §C）；三件作为历史证据 `retain`（只读） | #5：旧 open 不可擦改、不可改名继承；替代路线由本包重建追踪；#6：版本歧义保留不裁决 | 替代链→§C＋`12-traceability-and-handoff.json`（control→设计字段→场景→检验 ID 逐项）＋`03`（来源映射）；正式准入状态→`00` formal_hld_admission（blocked_by_evidence_and_pending_gates） | #7 机器本体取证；正式 HLD 人审（另议） |
| UPG-LEG-14 | `duanxian/design/specs/2026-06-06-hld-digital-life-novel.md`（六月 HLD v4） | §9.1–9.3（`:312–339`）风格/语言/禁用；`:343` §10=HLD→LLD 交付包 | `adapt`（作为**语义锚点比较对象**进入 `03` 五行映射；风格章本身不升为当前控制） | #3：R07 素材引用 §10.2/10.3/10.4/10.6/10.8 需逐项与 §9.1–9.3 实际内容比较，不得伪造 §9.4/§9.6/§9.8 | 逐项比较结论→`03-source-migration.csv` 行 18–22；风格控制新版由 `08`（表达规则）＋`09`（场景禁止项）承接 | 无 |
| UPG-LEG-15 | 工程线四条：`duanxian/conception-production/run.py`＋三测试（#1）、`README.md`/`engine/README.md` 计数（#2）、`.gitattributes`（#4）、#6 取证 | `run.py:14,41–47,54,69,77,85,93,126,133`；tests `:12–13,23–24`；`README.md:5`、`engine/README.md:9`；`.gitattributes:1–23` | **engineering_deferred**（本包不修复、只登记依赖与隔离；见 `13` REG-01/02/04/06 行 DEFERRED_ENGINEERING） | 设计作业无工程修复授权（定义书 §1.2/1.3/1.4/1.7 裁决）；禁止顺手修引擎 | 依赖登记→`12` §阻塞与暂停条件；证据留档→`13` | 工程责任人另行处置 |
| UPG-LEG-16 | `engine/harnesses/novel-conception-autonomous/docs/final-delivery-contract.md`（E17） | `:17–24,48–58,64–91` 同版包/来源链/正式验证/作者权 | `retain`（作为机器验收方法论参考；不执行、不冒用其 validator 名义） | 本包不是机器本体复验（#7 缺口）；方法参照可保留 | 引用→`00` §machine_package_evidence；正式复验要求→`13` REG-07 | #7 |

## C. #5 替代声明（HLD-TRACE-CLOSURE P1/open 的显式替代记录）

1. **旧门原文保持**：`12-hld-integrity-report.md:25`（artifact01 逐字段来源绑定=P1/open）与 `:57`（摘要式追踪未逐字段闭合的自述）原样保留，不擦改、不改名、不复制其任何 `pass` 子项。
2. **消费范围重定义**：2026-07-13 HLD run 全部产物在本包中的身份=历史证据（用于定位旧冲突与映射来源），不再作为当前设计的准入凭据；其 `pending_hld_human_review`／`blocked_revision_required` 状态继续有效。
3. **替代链**：本包以 `01`（控制→Pointer/hash 逐字投影）＋`03`（17 路径＋5 语义映射）＋`12`（control→设计字段→场景→检验 ID 的逐字段追踪）＋`manifest.json`（逐文件字节 hash）重建字段级追踪。替代范围=本包 16 文件；不回溯修复旧 run 内部追踪。
4. **新门状态**：设计层替代记录成立≠正式 HLD 人审通过≠`lld_ready`。正式 HLD/LLD 准入仍按 `00` §formal_hld_admission 的四个门执行（#7 机器复验、#5 本声明、#6 歧义、D01–D03 签认）。
5. **回退保护**：若本包被验收否决，旧 open 状态不受影响；不存在「以新包失败为由改写旧状态」的路径。

## D. #6 版本歧义保留（v2/v3 混用，不裁决）

| 栏 | 内容 | 证据 |
| --- | --- | --- |
| manifest 声明的待审对象 | canonical-world-facts **v3.0** | `manifest.md:12–15` |
| 人审说明原文 | **v2.0** is newly presented after material world reconstruction | `12-hld-integrity-report.md:33` |
| 真实评审对象 | **未从这些记录证实**（是否实际审错版本未知） | 定义书 §1.7；本作业未获历史运行责任人取证 |
| 禁用动作 | 全局替换字符串／删除 v2／把 pending 改 pass／以本包任何标签宣称旧评审对象已查清 | 定义书 §1.7 裁决 |
| 完整关闭剩余条件 | 历史运行责任人提供可核验的真实评审对象，或受控说明明确不可证边界并完成责任确认（与 #5 关闭互不替代） | 同上 |

## E. 防回流检查（本表自检）

- 周岚参与链：本包 `04/06/07/09/10` 中不存在「周岚参与/维护例外/周启明/纬线/裂隙」作为新版事实；仅 `02/10` 中作为 retire/pending 的历史指称出现（NEG-AUTHORITY 检查点，`13`）。
- 旧角色机械置换：郑柏舟→罗景明的职务换名路径被显式禁止（`04` §身份识别；NEG-IDENTITY 检查点）。
- 历史正文：`duanxian/novel-text/` 零改动；`10` 号表 writing_status 全部 PENDING_WRITING。
- 旧 `pass/canonical/covered`：本包不引用任何旧 run 通过状态作为依据；canonical 指称只出现在 §C/D 的历史引述中。
