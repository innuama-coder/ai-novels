# 《断线》R3 审视实施报告 v4（duanxian-audit3-impl-001 → impl2-001 → impl3-001 → impl4-001 修正版）

- 作业：JOB #2382 · duanxian-audit3-impl-001（三步协议第二步：审视实施）；**本 v2 由修正作业 JOB #2394 · duanxian-audit3-impl2-001 依据独立验收 `acc-001-acceptance.md` §7 修正单 ACC-F001–F010 改写**；**本 v3 由修正作业 JOB #2471 · duanxian-audit3-impl3-001 依据独立验收 `acc2-001-acceptance.md` §A2/07 修正单 ACC-F011–F014 续改**；**本 v4 由修正作业 JOB #2493 · duanxian-audit3-impl4-001 依据独立验收 `acc3-001-acceptance.md` §A3/08 修正单 ACC-F015–F017 续改**。
- 定义书：`outputs/duanxian-audit3/def-001-definition.md`（@ 024ef15a，唯一工作指令源）。
- 审计基线 BASE：`92573f1cca40f37cee04d2beb8708ff33ba603d6`；本作业基线 156ffc48（＝acc2-001 交付提交）。
- 判决历史（保留不抹除）：acc-001 对 v1 报告质量线／ISSUE 质量线／总体均判 **FAIL**，返回第二步 LOOP；v2 为该 LOOP 的修正交付。acc2-001 对 v2 复验仍判 **FAIL** 并出具修正单 ACC-F011–F014（ACC-F011 为阻断项）；本 v3 为第二轮 LOOP 的修正交付。acc3-001 对 v3 复验仍判 **FAIL**（ACC-F011/F012/F013 三项残余＝ACC-F015–F017；ACC-F014 判 PASS）并出具修正单 ACC-F015–F017；本 v4 为第三轮 LOOP 的修正交付，**待第四步独立复验（acc4），不自宣布 PASS**。
- 判断目标：DX-G01..G09（定义书第二节冻结口径）。两条判断轴：与目标一致性、实现程度。

---

## 1. 范围与版本基线

### 1.1 阅读集（v2 重述；全读账见 `impl-001-reading-ledger.md`）

- 全读证据账：**逐件可回读全读账 v2**（`outputs/duanxian-audit3/impl-001-reading-ledger.md`，155 条）——R=127（`duanxian/` 除 `conception-production/`、`testing/` 外全树）＋定义 N 集 8 件（G1–G7＋根 README；G7＝`duanxian/novel-goals.md` 与 R 重合，账内记 R，N 标记其余 7 件非 duanxian 路径）→ **R∪N=134**；E=21（工程候选集）；合计 **155 件逐件登记** BASE blob OID／SHA-256／字节／阅读区间或 Pointer 覆盖／摘要／目标映射／支持-反证-未读。
- 阅读时间与诚实声明：v1 无逐件账，acc-001 R02 判「提交证据不能证明全读」。本 v2 的 155 件逐件自读全部发生于 impl2-001 期间（2026-11-14/15）——**补读重建，不溯及 v1 历史，不伪造历史阅读时间**；不以验收方字节清单或任何他人清单替代自读（全读账 §0）。
- E 集 21 件逐件选择与闭合理由见全读账 §2；未闭合项 9 条见全读账 §3（A3 P1 原值仅哈希、机器链字节级不可复算、两机器链关系未裁决等）。
- 批准包深读：A3 `human-review-report.json`（约 2.84 MB 单行 JSON）按顶层域分块——内容域 3792 行全文、三索引阵列**逐 Pointer 语义覆盖**（v3 新增 `impl3-001-pointer-coverage-table.md`，ACC-F011：RL 4602/4602＝18 语义组合全读；DI 4602/4602 库内六字段全量核验＋91 (阶段×域) 组语义直读；SC 3924/3924＝64 源族直读、引用 4626 次全解析零断引用；同值复用 525 对全列——**v4（ACC-F015）：EV 同来源双入口 148 组＝同值 0、非复用，与 525 真复用对按两种分组分开判定，逐组全列见 POINTER §6a**；P1 值体 4602 条未读＝#7 维持，不声称补出）；A5 HTML 18 分块全覆盖（可见文本＋嵌入数据）。
- 实时远端核验：v1 于 2026-11-14 GET 全量 22 条与冻结快照一致（§10）；impl2-001 未做任何 GitHub 写操作，#14–#22 当前状态以无认证 GET 收据为准（issues v2 §5.1）。

### 1.2 版本谱系（v2 修正：A1/A2 名称对调、因果 v1.1、writing 17 件、「六月线」定名）

| 层 | 载体 | 时点 | 状态 |
|---|---|---|---|
| ① 批准层（**当前权威**） | `duanxian/conception-approved/`：A0 README、**A1 author-decision.json**、**A2 conception-completion.json**、A3 human-review-report.json、A4 报告 md、A5 报告 html；run `duanxian-conception-v2-20260811-18` | 2026-08 | 作者批准，现行口径（v1 曾将 A1/A2 名称对调，acc-001 R03 指正） |
| ② 工作流文档层 | `duanxian/design/workflow-docs/` 11 件：意图卡 v0.2、主体定义 v1.1、**因果故事线 v1.1**（L7；L25 废止 v1.0 旧口径）、叙述契约 v1.1、core-character v1.0 等；brief.html 为 `awaiting_author_review`（novel-goals L97） | 2026-07-17..21 | 作者逐件确认（brief.html 待审） |
| ③ 七月设计链 | `design/runs/`（07-05 intake/proposal→07-06/07 PRD→07-10/13 HLD） | 2026-07 | HLD 阻塞于人审；PRD 终包门状态自相矛盾（#18 核心确证保留） |
| ④ **六月遗产线** | `design/specs/lld/`（人物/场景/空间件）、`duanxian/writing/`（**17 件**）、`duanxian/novel-text/2026-06-07-duanxian-novel.md`、`design-scenes-draft.md` | 2026-06-06/07 | 旧写作线，已被上层替代但保留（v1 曾误计 18 件、误称「四月线」，均已改正） |
| 机器链（**两条，关系库内未裁决**） | (a) conception-production V2 链：run.py＋testing 构建器（B0→S1→W1→E1→T1→C1→Q1→P1→H1；默认 RUN 20260802-04，env 可切 20260803-04/20260811-18）；(b) hld-run-08 HLD V1 链：build_run08_hi1_000230/237/238（RUN 目录不在库） | 2026-08 后 | 现行字节为批准后修订；仅静态阅读，不可复算（§6） |

一致性判定以①为应然基准；②③④为历史层，其与①的偏差按「历史实现 vs 当前批准口径」分轴记录，不因历史层偏差否定批准层。**机器链内部两链在顾衡生死上互斥（§6），v1「下游 HLD 层同样一致」的说法撤回。**

---

## 2. 目标基准（DX-G01..G09 摘要）

G01 新主体（R-07≠顾衡复生，无预装情感）；G02 启动条件与责任分离（沈逾无项目启动决策权、可为知情执行者）；G03 无当前感官、纯文字接口；G04 记忆＝主观线索，现实团队阻断袭击，自述可验证≠已验证；G05 周岚为受保护无辜亲属（≠妻子程予安）、程予安知情同意边界；G06 行动层/原因层分离，崩溃根因在处境；G07 危机先由现实团队阻断、R-07 选择、沈逾执行告别、无活动备份；G08 终止意图不提前直示、法律身份/未来重载/长期互信保持开放、后果不被抹除；G09 来源与授权链可追溯。

---

## 3. 一致性轴结论（v2：对象级 12 字段矩阵，ACC-F002 补全）

矩阵字段＝定义 §4.1 全 12 项：`goal_id、object_id、version_class、baseline_source、actual_source、support、counterevidence、consistency、implementation_level、limitation、existing_issue、candidate_id`。路径行号绑定 BASE；全读账 n= 为逐件账行号。version_class：①批准／②工作流／③七月链／④六月线／机器(a)conception／机器(b)hld-run-08。

| goal_id | object_id | version_class | baseline_source | actual_source | support | counterevidence | consistency | implementation_level | limitation | existing_issue | candidate_id |
|---|---|---|---|---|---|---|---|---|---|---|---|
| G01 | R-07 主体设定 | ①＋机器(a) | A3 characters/core-0（R-07 卡） | 同 baseline；c1_builder R-07 forbidden | c1 L54「不得写成顾衡复生或预装恋爱程序」；h1_fragments 片段04「我在」；w1 SL-R07-MAIN（n=151） | 无 | 一致 | 规范已定义＋当前批准呈现可证＋机器静态内容级一致 | A3 P1 原值仅哈希（#7） | — | — |
| G01 | 六月线前序人物件 | ④ | G01 新主体口径 | LLD 人物 7 件＋qianxu（n=72-79、116） | —（历史层不承担当前义务） | qianxu＝陆远/灰鸟线；程予安/周岚/纪菱/郑柏舟无对应 LLD 件 | 部分一致（历史断裂） | 历史实现 | 已被上层替代；v1 曾误称「四月线」 | #3（迁移表） | — |
| G02 | 沈逾角色边界 | ①＋机器(a) | A3 core_characters/1 must_not_imply＋MOD-WORLD-SYSTEMS must_hold | 同 baseline；c1 L65、w1 L53、h1_plan L339 | A3「不得把她写成启动项目的决策者。」＋「沈逾是知情接受任务的执行者，不是项目启动者」——**禁决策/启动、允执行** | 无 | 一致 | 规范已定义＋当前批准呈现可证＋机器静态内容级一致 | — | — | — |
| G02 | 历史启动/执行口径 | ③④ | 同上 | proposal 04:17、LLD K2:26、shenyu 24/26-27、design-scenes L15-22 | proposal 为「组织决定＋研究员执行」（决策/执行分离）；README L22-23 已有新旧线隔离声明 | 六月线濒死/生前转移 vs 批准「死亡后加载」＝历史时间差异，适配映射未建立 | 部分一致（历史适配缺口） | 历史实现 | #19 收窄至本子集 | — | #19（收窄） |
| G03 | R-07 接口边界 | ①＋机器(a) | A3 ENV-DIALOGUE、A5 closing-note | w1 L72/L174 逐字、e1 ENV-TEXT-DIALOGUE-ISOLATION | 「无视觉、听觉、肢体与现实感知」；隔离室模板 | 无 | 一致 | 规范已定义＋当前批准呈现可证＋机器静态内容级一致 | — | — | — |
| G03 | 六月线正文接口越界 | ④ | 同上 | 正文 L245/255/271（n=110） | — | R-07 读击键间隔/眼球位置/按键压力 | 明确冲突（对④自身） | 历史实现 | 归既有族 | #9 | — |
| G04 | 记忆边界 | ①＋机器(a) | A3 ENV-MEMORY、周岚卡 must_not_imply | 同 baseline；w1 L68/L82 | 「只作为主观片段而非录像」；可打断片段 | 无 | 一致 | 规范已定义＋当前批准呈现可证＋机器静态内容级一致 | — | — | — |
| G04 | 历史复核链缺口 | ③ | 同上 | PRD S11-12、proposal 04:23/09:20/12:20、LLD K8 | — | 记忆情报直接化解危机；无复核链 | 部分一致 | 历史实现 | 归既有族 | #13 | — |
| G05 | 周岚卡（儿时守护者） | ①＋机器(a) | A3 周岚卡 must_not_imply「不得把她写成顾衡恋人。」 | c1 L87/L101、w1 L101、h1_plan L649 | 「周岚是儿时守护者」多层在场；受保护亲属边界 | 无（v1「brief:282 妻子细节被撤回口径」系**对象混淆**，撤回） | 一致 | 规范已定义＋当前批准呈现可证 | 正文零出场＝未完成创作，不判缺陷 | #8 | — |
| G05 | 程予安卡（在世妻子） | ①＋机器(a) | A3 程予安卡生活背景 | c1 L98、A4 L416/L444 | 「恋爱五年、结婚两年」「顾衡仍在世的妻子」——与 brief:282 妻子信息一致（同属周岚条目内嵌） | 无 | 一致 | 规范已定义＋当前批准呈现可证 | 同上 | #8 | — |
| G06 | 行动/原因分离与根因 | ①＋机器(a) | A3 MOD-WORLD-ACTIVITY、t1 R07-MAIN | t1 L287、w1 L148、c1 L65、e1 联合指挥 L63-69 | 危机压力只加重已发生崩溃（根因在处境）；三缺一不能下发行动 | 无 | 一致 | 规范已定义＋当前批准呈现可证＋机器静态内容级一致 | — | — | — |
| G06 | 历史根因外移 | ③ | 同上 | proposal 04:25 | — | 数字生命体设局诱导 | 部分一致 | 历史实现 | 归 #10 族语义比较 | #10 | — |
| G07 | 危机-选择-执行-备份链 | ①＋机器(a) | A4 md＋A3 world/boundaries＋ENV-CORE | t1 L287、q1 L269-277、w1 L212、h1_fragments 06、run_v2 L777 | **A4 md 多处直接表述**：L271「当前也没有活动备份」、L283「封存材料不是活动备份」、L327「关闭当前实例且无活动备份」、L510「确认关停不可逆、无活动备份」；brief.html:166 另有 | 无（v1「md 仅 brief 一处明写」**撤回**，acc-001 §3.1 指正） | 一致（md 直接覆盖充分） | 规范已定义＋当前批准呈现可证＋机器静态内容级一致 | — | — | — |
| G07 | 六月线 K9 自行终止 | ④ | 同上 | scene-K9 族、design-scenes | — | 自行终止＋她返回 | 明确冲突（历史层） | 历史实现 | 归 #10 族 | #10 | — |
| G08 | 开放边界与不提前直示 | ①＋机器(a) | A3、N4 L82、A5 brief6 forbidden | w1 L201/L205、t1 L299-306、run_v2 L530（intentionally_open）、h1_plan L969 | 重载仅未决承诺；告别前只写可观察迹象 | 无 | 一致 | 规范已定义＋当前批准呈现可证＋机器静态内容级一致 | — | — | — |
| G08 | subject-definition 残留口径 | ② | N4 第一部不知情 | subject L34/L41/L61 | L41＝第二部线索；L61＝delegated 开放时间项——**均不证明第一部已确认受骗**（v1「三处直接冲突」撤回） | 残留「被利用创伤/何时意识到受骗」旧表述 | 部分一致（残留待治理） | 历史实现 | #16 收窄后保留 v1.1 版本事实 | — | #16（收窄） |
| G08 | FREEZE-10 历史适配 | ③ | N4 | PRD 06-freeze L20 | FREEZE-05（单侧暗恋）与批准相容，维持不立案 | FREEZE-10 L20 首列「结尾必须呈现研究员事后理解骗局」vs N4「不得让沈逾在第一部确认受骗」——**需显式历史适配，非「兼容」**（v1 REJ-01 判定修正、拆分） | 部分一致 | 历史实现 | 待与 #10/#16 语义比较后再定候选 | #10、#16 | 待证（不发布） |
| G09 | A1/A2/A3 哈希链 | ① | A1 author-decision、A2 completion | run_id/schema/p1 三处一致＋A2 三包哈希＋PRD manifest 11/11（acc-001 R05 独立复算认可） | 局部 hash 绑定收据成立 | 无 | 一致 | 当前批准呈现可证 | 绑定≠全链复验 | — | — |
| G09 | 机器链字节复算边界 | 工程 | — | run_v2/run.py 静态阅读＋`git ls-tree -rz` BASE 全树核对（v3，ACC-F012，四列表见 §6） | 局部 hash 绑定收据成立（§6 结构层） | **v3 纠正（ACC-F012）**：engine/ 源码在库（BASE 计 1290 路径，含 10 件 `engine/skills/*/run_v2.py` 与 `engine/harnesses/novel-conception-autonomous/runtime/production_orchestrator.py`）；不在库者为运行目录 `duanxian/conception-runs/`（0 路径）、`engine/projects/` migration 输入（0 路径）与三机器包（#7）；A3 `h1_session_id=H1-IMPLEMENTATION-…` 前缀≠库内入口 `run_duanxian_conception_v2.py` 生成格式 `H1-DUANXIAN-<run_id>`（L128）——**仅证格式不一致，不能推出执行入口不在库**；实际执行的脚本版本绑定未证 | 无法判定（字节级） | 证据不足（字节级） | 静态源码只证写法＋解析根/运行绑定逐项见表（§6） | #7 | — |
| G09 | brief 版本链引用 | ② | G09 可追溯 | brief L314：I0 v0.3/I1 v1.2/I2 v1.0/I3 v1.0/I4 v1.0/I5 v1.0 | **I3 core-character v1.0 相符**（v1「全部不符」撤回，acc-001 §3.2 指正）；brief 状态 awaiting_author_review（novel-goals L97） | I0/I1/I4/I5 四项与库内 v0.2/v1.1/v1.1/v1.1 不符；I2《世界运行契约》不在库不可对照 | 部分一致（部分失配） | 历史实现 | 「不在任何审阅清单」全称撤回 | — | #15（收窄） |

**一致性轴总裁决（v2）**：批准层（①）与机器链 (a) 内嵌故事数据在 DX-G01..G09 上零冲突（本轮逐件补读后维持，证据见全读账）；机器链 (b) hld-run-08 与批准链在顾衡生死上互斥（§6，未闭合不裁决）；偏差集中于历史层（②③④），构成新证实发现者见 §8（收窄后），其余为既有 13 条 ISSUE 覆盖族（§5）。**v1 的「机器链已复验（内容级）」标签全面撤回**（ACC-F002）：本轮仅持有局部 hash 绑定收据＋静态源码内容级阅读。

---

## 4. 实现程度轴结论（v2：撤回「机器链已复验」）

分级仍用定义枚举，但按定义 §4.1「本轮不运行生产 validator，不得无证写机器链已复验」执行：

| goal | 实现程度（v2） | 说明 |
|---|---|---|
| G01 | 规范已定义＋当前批准呈现可证＋机器链(a)静态内容级一致 | A3/A5 全链在场；c1_builder 同口径 forbidden（静态阅读） |
| G02 | 同上 | 批准层禁决策/启动、允执行；机器层双落在场；历史层差异归 #19 收窄子集 |
| G03 | 同上 | w1 limits 逐字＋e1 模板＋三段样片正文；正文层旧违例归 #9 族 |
| G04 | 规范已定义＋当前批准呈现可证＋机器链(a)静态内容级一致；md 复核链为历史实现 | ENV-MEMORY 在场；PRD 复核链缺口归 #13 族 |
| G05 | 规范已定义＋当前批准呈现可证；正文层未完成（不判缺陷） | 周岚/程予安两卡对象级拆分后边界清晰（§3）；生活线素材零正文实现＝正常创作进程 |
| G06 | 规范已定义＋当前批准呈现可证＋机器链(a)静态内容级一致 | t1 节拍完整落实顺序与根因 |
| G07 | 规范已定义＋当前批准呈现可证＋机器链(a)静态内容级一致 | **md 直接覆盖充分**（A4 四处直写，§3）；v1「md 侧显式覆盖部分」撤回 |
| G08 | 规范已定义＋当前批准呈现可证＋机器链(a)静态内容级一致 | 三问开放＋N4 在场；②层残留归 #16 收窄；FREEZE-10 需历史适配（§8.2） |
| G09 | 批准层结构可证（局部 hash 绑定）；机器链**证据不足（字节级不可复算）**；②文档引用网络部分一致 | **v3 纠正（ACC-F012）**：engine/ 源码在库（1290 路径）；缺的是运行目录 `duanxian/conception-runs/`、`engine/projects/` migration 输入与三机器包（#7）；h1_session_id 前缀差异仅证格式不一致（§6 四列表）；brief 部分失配归 #15 收窄 |

**实现程度轴总裁决（v2）**：九项目标在批准层均为「规范已定义＋当前批准呈现可证」；机器链 (a) 达到**静态源码内容级阅读一致**（非复验）；未完成项集中于 G05 生活线正文（正常进程）与 G09 字节级复算（库内证据边界，#7）。

---

## 5. DEDUP-01..13 逐条处置（v2 修正两处归并结论）

| DEDUP | 既有 ISSUE | 复核结论 | 处置（v2） |
|---|---|---|---|
| DEDUP-01 | #1 构思 CLI 七条运行时路径＋三测试入口 | 属实且精确化（run.py 双前缀；成因 f7ac2db 半改） | 不重复提交；**v1「扩展载体立 DX3-F009」撤回**——F009 重归 out_of_scope/existing（ACC-F007） |
| DEDUP-02 | #2 README 81 技能计数 vs 实际 82 | 复核实测现存 82 目录 | 不重复提交 |
| DEDUP-03 | #3 17 份写作素材 LLD 路径迁移＋R07 章节引用 | 属实；关闭范围明确 17＋5 件 | 不重复提交；**v1「范围外新实例归 DX3-F001」撤回**——F001 重归 out_of_scope/existing（ACC-F007）；**v3（ACC-F014）重做机制/关闭行**：机制＝旧根文本引用迁移（17 件各 3 处 backtick LLD 文本引用→`duanxian/design/specs/lld/` 新根，17 目标全存在）＋R07 素材内容指称章节错位（writer-R07 L14 引 §10.2/10.3/10.4/10.6/10.8、L16 引 §10.2，而 2026-06-06-hld v4.0 风格章为 §9、§10 为 HLD→LLD 交付包）；关闭＝17 项逐条可定位＋R07 五处指称按内容对照（给准确定位/注明历史版本依赖或待核，不补造）；**非 .gitattributes 迁移**（v2 机制行系只换对象外推） |
| DEDUP-04 | #4 .gitattributes 缺 engine/ 前缀 | 属实 | 不重复提交；**v3（ACC-F014）重做机制/关闭行**：机制＝HLD 工件字节稳定属性规则路径前缀失配（L1–2 声明 byte-exact manifest，L3–23 规则均缺 `engine/` 前缀；实测 3 件真文件 text/eol 全 unspecified）；关闭＝按实际树调整规则覆盖并在**全预期集**复查 text/eol（非 3 件抽样）；**非忽略规则问题**（v2 机制行系只换载体外推） |
| DEDUP-05 | #5 HLD-TRACE-CLOSURE P1 open | 补证（事件-状态绑定错位等） | 不重复提交；补证供关闭时处理 |
| DEDUP-06 | #6 v2.0/v3.0 标签混用 | canonical 六项实质差，非纯标签 | 不重复提交 |
| DEDUP-07 | #7 三个机器交付文件未留存 | 佐证：conception-runs 不入库为既定策略 | 不重复提交；§6 复算边界同源；**v3（ACC-F014）重做机制/关闭行**：机制＝受控同版取证链缺失（性质＝证据补充请求，非已证生产失败或留存策略违例——政策 A0 README L3 与 .gitignore L11-18 已明示运行账本不入 Git；A2 指针 `/run_id=duanxian-conception-v2-20260811-18`、`/development_handoff/path=P1/development-handoff.json` sha256 d48194db…、`/p1_manifest path=P1/package-manifest.json` sha256 bba81d35…）；关闭＝可审计访问说明＋确切 run/版本＋包清单及 hash＋回溯 manifest/完成记录/作者决定/正式 validation/execution/实现快照/来源链＋受控环境 validator 重放（basename 存在或两项 hash 一致均不足以证全链可用）；**非留存策略声明问题**（v2 机制行系只换对象外推） |
| DEDUP-08 | #8 周岚维护例外参与链 | 补证（上游同族）；批准层周岚卡已封闭 | 不重复提交 |
| DEDUP-09 | #9 R-07 当前视听 | 大量补证（PRD/正文/LLD） | 不重复提交 |
| DEDUP-10 | #10 终局自行关闭＋提前披露 | 补证；批准层顺序封闭 | 不重复提交；FREEZE-10 适配问题回归本族比较（§8.2） |
| DEDUP-11 | #11 十秒沉默文字来源 | 补证（正文信息先用后到族） | 不重复提交；#20 工程残留子项与本案比较（§8） |
| DEDUP-12 | #12 郑柏舟显名 | 补证（betrayer 记录区省略 vs 正文点名） | 不重复提交；#20 载体对齐子集与本案比较（§8） |
| DEDUP-13 | #13 完整可检索记忆/像素重建 | 补证；批准层 ENV-MEMORY 封闭 | 不重复提交 |

十三条处置完毕：零重复提交、零评论/关闭/编辑（线上只读状态保持至 impl3-001）。**全部 22 条 all-state 的对象/控制/机制/关闭条件四维差异表见 `impl-001-issues.md` v2 §5.2（ACC-F007 产物）。** v3（ACC-F014）复核该 22 条表：「只换对象/载体即新机制」式外推共发现 4 处——issues v2 §5.2 的 #3 行（误写 .gitattributes 迁移）、#4 行（误写忽略规则）、#7 行（误写留存策略声明）三处机制/关闭条件概括，及本报告 §5 DEDUP-03/04/07 行沿用的同一概括，均已按上方重做行修正并传导至 issues v3 §5.2 批注；其余 19 条复核未发现同类外推。

---

## 6. G09 机器链复算边界（v2 修正：撤回复验标签＋两链矛盾登记）

- 结构层（局部绑定，保留）：A1↔A2↔A3 的 run_id、schema_version、P1 哈希三处一致；A2 三包哈希齐备；PRD manifest 11/11 匹配。acc-001 R05 独立复算认可这些**局部绑定**。
- 内容层（静态阅读，降级表述）：testing 21 件内嵌故事数据经 impl2-001 逐件全文静态阅读，conception 链 (a) 与批准口径未见冲突；**但 v1「机器链已复验（内容级）」撤回**——静态源码只证明写法，不证明任何 run 已按当前字节执行。
- 字节层（不可复算，v3 修正引擎可得性表述，ACC-F012）：v2「conception-runs/ 全部 run root 与 engine/ 不在库」**前半句成立、后半句错误**——engine/ 源码树在库（BASE `git ls-tree -rz` 计 1290 路径，含 10 件 `engine/skills/*/run_v2.py` 与 harnesses runtime）；真正不在库者为运行目录 `duanxian/conception-runs/`（0 路径）与 `engine/projects/`（0 路径，migration-finalization.json 输入缺失）。A3 run `20260811-18` 的 `h1_session_id` 前缀 `H1-IMPLEMENTATION-`≠库内 `duanxian/testing/run_duanxian_conception_v2.py` 生成格式 `H1-DUANXIAN-<run_id>`（L128）——该差异**仅证两处格式不一致，不能推出实际执行入口不在库**；入口在库而实际执行的脚本版本绑定未证（#7 边界维持）。
- **引擎/入口可得性四列证据表（v3 新增，ACC-F012；v4 按 ACC-F016 重做七入口行、harnesses 行与三机器包行）**——证据＝BASE `92573f1c` `git ls-tree -rz` 全树枚举＋逐候选路径 `git cat-file -e` 核验＋入口脚本 `duanxian/testing/run_duanxian_conception_v2.py` 静态逐行追读（ENGINE/RUN_ROOT/MIGRATION 定义 L16–35、importlib 导入 L37–44、`load_stage_runtime` 三候选根 L43–55、七技能调用 L80–123）。**v3 表四处失真表述（经 acc3 §A3/03 反例证实）撤回**：①统一 `-designer` 后缀的花括号路径（构造 Q1/P1 两个不存在的技能名）；②「三根回退首根（ENGINE）」（调用串自带 `engine/` 前缀，首候选＝`ENGINE/engine/skills/…` 拼重根不存在，实际命中**第二候选** `ENGINE.parent`＝仓库根）；③「模块可导入」（静态核验未证导入）；④三机器文件统归「A2 manifest 哈希引用」（A2 对 hld-completion.json 零引用）。v4 表列＝仓库路径／解析根·阶段来源（脚本依据）／实际存在／运行绑定：

| 仓库路径（BASE） | 解析根（脚本依据） | 实际存在 | 运行绑定 |
|---|---|---|---|
| `engine/` 全树 | run 脚本 L16–19 `ENGINE=parents[2]/engine`＋sys.path.insert | **在库**（1290 路径） | 静态解析根成立；实际执行版本未证 |
| S1 `engine/skills/novel-storyline-architecture-designer/scripts/run_v2.py`（调用串 L80–83） | L44–48 三候选按序：① `ENGINE/engine/skills/…`（拼两次 engine，**不存在**）→ ② **`ENGINE.parent`＝仓库根（命中）** → ③ `NOVEL/…`（备而未用） | **在库**（②命中，`git cat-file -e` 逐候选验证） | 静态解析成立；实际执行版本未证 |
| W1 `engine/skills/novel-world-model-designer/scripts/run_v2.py`（L84–87） | 同上三候选序（②命中） | **在库** | 同上 |
| E1 `engine/skills/novel-environment-system-designer/scripts/run_v2.py`（L92–95） | 同上（②命中） | **在库** | 同上 |
| T1 `engine/skills/novel-event-timeline-designer/scripts/run_v2.py`（L100–103） | 同上（②命中） | **在库** | 同上 |
| C1 `engine/skills/novel-character-system-designer/scripts/run_v2.py`（L108–111） | 同上（②命中） | **在库** | 同上 |
| Q1 `engine/skills/novel-conception-reviewer/scripts/run_v2.py`（L116–119；**真名无 `-designer` 后缀**） | 同上（②命中） | **在库** | 同上 |
| P1 `engine/skills/novel-conception-deliverable-assembler/scripts/run_v2.py`（L120–123；**真名无 `-designer` 后缀**） | 同上（②命中） | **在库** | 同上 |
| `engine/harnesses/novel-conception-autonomous/runtime/__init__.py`、`runtime/production_orchestrator.py` | L37–44 importlib 导入（`harnesses.novel-conception-autonomous.runtime[.production_orchestrator]`，sys.path 已插 ENGINE） | **在库**（源文件与导入路径存在） | **源文件/导入路径静态存在；模块导入与依赖闭包可执行性未证（未运行 import）**；实际执行版本未证 |
| `duanxian/conception-runs/<run_id>/` | L24–27 RUN_ROOT＝NOVEL/conception-runs/RUN_ID（默认 20260802-04） | **不在库**（0 路径） | 运行产物目录缺失（#7） |
| `engine/projects/duanxian/compatibility-migrations/b0-compat-01/final/migration-finalization.json` | L29–35 MIGRATION 常量 | **不在库**（engine/projects/ 0 路径） | migration 输入缺失 |
| `novel-conception-package.json`（P1 机器包本体） | 阶段来源＝**P1 机器包**（engine 构思 V2 契约命名：`final-delivery-contract.md` 等）；A2 证据＝`p1_manifest` 指针（`P1/package-manifest.json` sha256 `bba81d35…`）＝**manifest 间接引用，非包本体哈希** | **不在库**（BASE 1444 路径 basename 零命中） | 未留存（#7 维持） |
| `development-handoff.json`（P1→开发移交） | 阶段来源＝**P1 交付物**；A2 证据＝`development_handoff` 指针（`P1/development-handoff.json` sha256 `d48194db…`）＝**直接哈希引用** | **不在库**（同上） | 未留存（#7 维持） |
| `hld-completion.json`（HLD 链终验件） | 阶段来源＝**HLD 自主工作流 V1 的 HF1 finalizer 契约产物**（`hld-skill-contract-catalog-v1.md` L223/L1261–1268、`hld-autonomous-workflow-v1-design.md` L89/L681/L903）；**A2 `conception-completion.json` 对其零引用**（顶层键无任何 hld-completion 字段/字符串）——其缺失是**独立 HLD 阶段证据边界，非构思完成记录必含项**（冻结 #7 明示，不由此推断新版 HLD 未运行） | **不在库**（同上） | 未留存；阶段证据边界单列 |
| `runtime/production_orchestrator.py`（acc2 引用的裸路径） | —（acc2 §A2 所引） | **不在库**（仓库根无此文件） | acc2 引用路径不精确；实件位于上行 engine/harnesses/…/runtime/ 下且在库 |
| `duanxian/testing/run_duanxian_conception_v2.py` | 入口脚本本体 | **在库** | 本表证据源（静态追读完成） |

注（v4，ACC-F016）：`engine/skills/*/run_v2.py` 该型共 10 件在库，上表 7 个被引用件全部命中（②根）；v3 花括号＋统一 `-designer` 后缀写出的 `engine/skills/novel-conception-reviewer-designer/scripts/run_v2.py` 与 `engine/skills/novel-conception-deliverable-assembler-designer/scripts/run_v2.py` 两路径经三候选根逐一 `git cat-file -e` 验证**均不存在**（acc3 反例成立）；另有四件测试构建器调用串（`testing/duanxian_w1_model.py`、`testing/duanxian_e1_builder.py`、`testing/duanxian_t1_builder.py`、`testing/duanxian_c1_builder.py`，L88–115）不带 `engine/` 前缀、①②根不存在而**③根 `NOVEL/testing/…`（＝`duanxian/testing/…`）命中**，不在本表七技能之列。
- **两机器链矛盾（v2 新登记，未闭合）**：链 (a) conception-production 设定顾衡牺牲/死亡且「不得把顾衡写成仍存活的行动者」（w1 L34/L44/L459、run_v2 L193）；链 (b) hld-run-08（HI1 三变体 000230/237/238）设定顾衡「昏迷垂危且未脑死亡」的在世患者（n=140 L108/294/413、n=141 L536）。两链互斥，库内无先后/替代关系裁决文件——**v1 §6「下游 HLD 层 build_run08 三件同样一致」撤回**；登记于全读账 §3-3，本轮不裁决、不发布新候选（超出修正单范围）。
- 工程可用性（静态）：run.py 七路径双前缀（#1）等布局问题保持 #1/#3/#4 范围归并，本轮不扩发（ACC-F007）。

---

## 7. 限制与待决（v2 修订）

1. **G05 断言强度（修订）**：周岚「无辜」正面表述集中于批准层；brief:282 属周岚条目内嵌妻子信息，对象级已拆分（§3 G05 两行）——v1 对象混淆撤回。
2. ~~G07 md 覆盖~~ **撤回**（acc-001 §3.1）：A4 md 四处直接表述「无活动备份」（L271/283/327/510），覆盖充分，不再列为限制。
3. 48 小时 vs 三个月（zhengbozhou:183 vs security-hall:59-61）：可相容为两次进入，登记为张力。
4. OPEN-01~03 映射：proposal 正文有响应，不构成链断裂。
5. qianxu 文件名歧义：#3 迁移表已缓解。
6. style-reference：G7 历史层观察（条目化技法映射＋无文风防护声明＋字符损坏）。
7. V2 报告表格截断、A2/A0 revision 时序：呈现层观察。
8. 素材-正文覆盖缺口：正常未完成创作。
9. PRD 09 风险检查零检出：历史流程观察，并入 #18 背景。
10. **（新增）LLD 模板件覆盖口径**：scenes/spaces 17 件以「母本全文＋字节级 diff 收据」达成覆盖（全读账 §0-5/§3-8）；如验收不认可等效，该 17 件降级表述。**v3（ACC-F011）**：可回读收据已补——diff 收据 17 条重生成并登记于全读账 §5（difflib unified diff、n=0、收据 sha256 与账内一致），复现映射＝收据头部命令逐字可重放。

---

## 8. 新证实发现（v2：逐条按 ACC-F003–F008 修正命题、证据与状态）

### 8.1 九条已发布候选的 v2 修正状态（线上原文未动；纠错建议见外部纠错提案）

| ID（#） | v2 命题（修正后） | v2 状态与修正 |
|---|---|---|
| DX3-F001（#14） | 文档路径/引用失配族（#1/#3/#4 范围外的工程整理项） | **重归类 out_of_scope/existing**（ACC-F007）：自承文档迁移扩展，无新故事控制；v1「五门全过」撤回；线上处置建议＝关闭并说明（OWNER_PENDING） |
| DX3-F002（#15） | brief **部分**版本引用与留存件不一致（I0/I1/I4/I5 四项不符；I3 相符；I2 不在库不可对照），状态 awaiting_author_review 需保持可见 | **收窄**（acc-001 §3.2）：撤回「全部失配」「周岚婚姻细节（对象混淆）」「三个月 vs D+58 互斥（非同一事件）」「不在任何审阅清单（全称）」 |
| DX3-F003（#16） | causal-storyline 为 **v1.1**（版本定位修正）；subject 残留旧终局表述待治理 | **收窄**：撤回「三处旧终局直接违反第一部不知情」——L34 创伤≠已知受骗、L41 明指第二部、L61 时间 delegated；保留版本事实与残留观察 |
| DX3-F004（#17） | HLD 处置组权限与 D+57 实际知情的映射待澄清 | **重锚定**：HLD-04（`artifacts/04-character-system.md` L15 Information permission 列；L21「危机解除后……掌握行动层；原因层须复核申请」）vs HLD-07（`artifacts/07-time-information-system.md` L15 Known by 列；L20 HLD-07-04 行动层 D+57、HLD-07-05 完整原因层 Hidden from 处置组＋读者）；**删除「不可能同时为真」**；判定 insufficient_evidence（同一时点/粒度映射未建立）；**v3（ACC-F013）**：#17 维持「未过门②」——强命题（权限矛盾）已被反证、窄命题（HLD-04 与 HLD-07 同一时点/粒度映射桥接缺失）为已证观察；单一可验关闭目标＝补齐该映射桥接；未过门维持至桥接补齐，不自动拆发 |
| DX3-F005（#18） | PRD 终包门状态自述矛盾（final L34 vs L281）——核心确证保留 | 保留；**成因标推断**（07-10 gate-report 人评 pending → 07-13 confirmed，确认时间窗 07-10–07-13 为旁证，非直证） |
| DX3-F006（#19） | 六月线濒死/生前转移（LLD K2:26、design-scenes-draft L15-22、PRD L38/L120/L190）相对批准「死亡后加载」的**历史适配映射**未建立 | **收窄**：撤回「研究员参与执行即违规」（批准禁决策允执行）与「没有任何口径迁移声明」（README L22-23 隔离在场）；保留窄子集；**v3（ACC-F013）**：隔离充分性判断＝总隔离声明（README L22-23＋novel-goals L67-71）对**层级误用**风险充分、对**事实级再利用**风险不充分（清单化素材仍可被消费、具体事实可被直接采用）；窄命题「事实级逐条适配映射缺失」保留，单一可验关闭目标＝Owner 对清单化残留素材逐条适配声明 |
| DX3-F007（#20） | 正文计数矛盾确证：L191/L195 两次匹配（67%→82%）vs L464「七次匹配」（L363 明写第一次/第二次；L379/L472 七个认知节点为另一计数对象）——**v4 起为 #20 主候选的唯一命题**；载体与其余子项不再并入主候选命题或其关闭条件 | **收窄**（acc-001 §3.5/ACC-F006）：撤回人数、面孔同一性、「未写即未发生」、仓库/地点等未证互斥（v4 维持不恢复）；**v3（ACC-F013）逐子项**：传输/人数/面孔/地点＝撤回；匹配次数＝确证保留；**v4（ACC-F017）主候选单一化＋附带项分类闭合**：主候选**单一**可验关闭目标＝正文计数口径收敛（同一推理链匹配次数统一；**只此一个**——反例测试成立：只解决计数即完全满足主候选目标，不需任何载体/道具/披露决定，计数修正也无需决定 K4/K6 电话或会议室）；K4/K6 载体＝**独立不发布观察**（不再是 #20 关闭目标或独立性理由；证据限度＝meeting-room L17/L20/L28–38＋§3.1–3.4 会议室 vs writer-shenyu L82/writer-zhengbozhou L191–199 电话·面对面/正文 L302 回指 K6 电话，采用基准未定，其自身潜在关闭方向＝采用基准声明）；附带项**逐项处置**（撤回 v3「剥离归 #11/#12/#13」笼统归并）：①第比利斯时间标注（正文 L157/L335/L375）＝register_only（#11 十秒沉默来源标注/#12 郑柏舟披露口径/#13 记忆检索边界的关闭条件均不覆盖）；②K6 编号进入正文（L302）＝register_only（同上不覆盖）；③L502 名片无素材来源＝待证（机制**邻接** #11「来源未标」族，但 #11 关闭条件不覆盖本项，不以邻接冒充已有覆盖）；④素材字符缺损＝existing REG-03（register_only 已登记）。候选/子项五门状态表见 issues v4 §2.7；自然语言/§5.2/JSON delta 三方同步 |
| DX3-F008（#21） | A3 控制条目计数残留：decision_controls/1「十个环境」vs 实列 12；decision_controls/7「六个样章片段」vs 实列 3 | 保留计数确证；**成因标推断**（早期迭代计数残留为推测——h1_plan 侧 statement 已改「两个深场景」、h1_fragments 存在六→三死数据块，生成因果无库内直证）；**现行映射修正为 03/04/06 三片段**（v1「两深场景 04/06」系少计 03）；计数通过≠体验控制通过 |
| DX3-F009（#22） | #1 同族工程脚本路径失配扩展 | **重归类 out_of_scope/existing**（ACC-F007）：静态引用失效≠运行验证失败；v1「五门全过」撤回；线上处置建议＝关闭并说明（OWNER_PENDING） |

### 8.2 登记不提交（v2 修订）

OPEN-01~03 映射缺表、qianxu 文件名歧义、style-reference 防护缺口、V2 表格截断、rev 时序、48 小时张力、素材覆盖缺口、PRD 风险检查零检出——维持不提交。**REJ-01 修正（ACC-F004）**：拆分判定——FREEZE-05 与批准相容（维持不立案）；FREEZE-10 L20 首列「结尾必须呈现研究员事后理解骗局」与 N4「第一部不确认受骗」**需显式历史适配**，与 #10/#16 语义比较后再定候选资格，本轮不发布。

### 8.3 撤销例（v1 保留＋v2 批注）

- 「FREEZE-05/FREEZE-10 与 G05/G08 正面冲突」：v1 判「兼容」——**v2 修正**：FREEZE-05 相容成立；FREEZE-10「兼容」判定不成立，改按 §8.2 需历史适配（同列首列限定不得省略）。
- 「proposal 12-ending 封死未来重载」：L24 为建议级，维持不立案。

---

## 9. 偏离说明

1. 定义书 §3.5 三份交付文件名按 spec.yaml 白名单归并为本报告＋issues 登记两件（v1 即此，保留）。
2. v1 阅读分工（12 只读代理＋主会话亲读）为定义允许的执行方式细化，但**其阅读证据不足以证明逐件全读**（acc-001 R02）——impl2-001 已以 155 件逐件自读全读账补齐（ACC-F001）。
3. 提交署名按作业宪法冻结命令逐字执行，无附加署名行。
4. **（impl2-001 新增）**：本 v2 仅改 `impl-001-report.md`、`impl-001-issues.md` 两件白名单文件，新增 `impl-001-reading-ledger.md`、`impl2-001-external-correction-proposal.md` 两件白名单文件；线上 ISSUE 零写操作（纠错建议全部 OWNER_PENDING，未执行）。
5. **（impl3-001 新增）**：本 v3 仅改上述四件白名单文件并新增 `impl3-001-pointer-coverage-table.md`（共 5 件，spec 白名单内）；隔离探针与中间产物全部置于 gitignore 的 `.kunora/impl3-work/`，不入库；线上 ISSUE 零写操作维持。
6. **（impl4-001 新增）**：本 v4 仅改五件白名单既有文件（本报告＋issues＋ledger＋proposal＋pointer）并新增 `impl4-001-correction-notes.md`（共 6 件，spec 白名单内）；隔离探针与中间产物全部置于 gitignore 的 `.kunora/impl4-work/`，不入库；线上 ISSUE 零写操作维持（ACC-F015–F017 均不涉任何线上编辑，外部建议仍 OWNER_PENDING）。

---

## 10. 发布账（v1 历史保留＋impl2-001 状态）

- v1 发布（历史，保留）：DX3-F001..F009 九条于 2026-11-14 创建（#14–#22），当时 201 成功并 GET 回读核对；既有 13 条零评论/关闭/编辑。**acc-001 判定其后**：#14/#22 未过范围与去重门，#15/#16/#19/#20 关键命题部分不能成立，#17 缺时点/权限区分——修正以本 v2 §8 与 issues v2 §5.1 登记为准，**线上原文一字未动**。
- impl2-001：**零 GitHub 写操作**；#14–#22 的建议纠错动作逐条写入 `impl2-001-external-correction-proposal.md`（OWNER_PENDING）；fresh 无认证 GET 收据（created_at、body SHA-256）登记于 issues v2 §5.1（ACC-F009）。
- 推送：remote-agent/duanxian-audit3-impl2-001 单提交，仅含四件白名单交付物，无 force。
- impl3-001：**零 GitHub 写操作**；推送 remote-agent/duanxian-audit3-impl3-001 单提交，仅含五件白名单交付物（四改一增），无 force；#14–#22 线上处置建议仍全部 OWNER_PENDING（见 `impl2-001-external-correction-proposal.md` v3 批注）。
- impl4-001：**零 GitHub 写操作**；推送 remote-agent/duanxian-audit3-impl4-001 单提交，仅含六件白名单交付物（五改一增），无 force；#14–#22 线上处置建议仍全部 OWNER_PENDING（见 `impl2-001-external-correction-proposal.md` v4 批注）。

## 11. 结语（v4）

本轮 impl3-001 按 acc2 §A2/07 修正单 ACC-F011–F014 完成第二轮修正交付：**(1)** **ACC-F011（阻断项）闭合**——新增 `impl3-001-pointer-coverage-table.md`：A3 三索引逐 Pointer 语义覆盖，RL 4602/4602＝18 语义组合全读（未读＝无），DI 4602/4602 库内六字段全量核验＋91 (阶段×域) 组语义直读（未读＝P1 值体 4602 条，#7 维持、不声称补出），SC 3924/3924＝64 源族直读（引用 4626 次全解析零断引用，42 个 MOD-/FRAG- 全部解析为 A3 内容域双词表），同值复用 525 对（7 域型）全列＋非等价语境核验；内嵌复算脚本＝可回读收据；v2「distinct 值全读」表述撤回，总表与 §1.1/本节声明同文。**(2)** **ACC-F012**——引擎/入口可得性四列证据表（仓库路径/解析根/实际存在/运行绑定）：engine/ 源码 1290 路径在库、七技能 run_v2.py 与 harnesses runtime 在库；真正缺失＝运行目录 conception-runs/、engine/projects/ migration 输入、三机器包（#7 维持）；h1 前缀差异降格为「格式不一致」单一含义；§3/§4/§6 与矩阵同步纠正。**(3)** **ACC-F013**——#17 维持未过门②（映射桥接缺失＝已证观察，关闭＝桥接补齐）；#19 明确隔离充分性双层判断（层级误用充分/事实级再利用不充分），窄命题保留；#20 逐子项处置（传输/人数/面孔/地点撤回；匹配次数确证保留，关闭目标＝正文计数口径收敛；K4/K6 载体待证保留为独立子项；工程/道具/披露剥离归 #11/#12/#13），自然语言与 JSON 同步。**(4)** **ACC-F014**——四维去重表 #3/#4/#7 机制/关闭行重做（旧根文本引用迁移＋R07 章节错位／text-eol 规则前缀失配／受控同版取证链缺失），22 条表复核仅此 4 处同类外推，已传导至 issues v3。线上 ISSUE 仍零写操作（OWNER_PENDING）。**acc-001 与 acc2 的 FAIL 判定历史保留**；本 v3 待第三步独立复验（acc3），不自宣布 PASS。

本轮 impl4-001 按 acc3 §A3/08 修正单 ACC-F015–F017 完成第三轮修正交付（v3→**v4**）：**(1) ACC-F015 闭合**——POINTER §6「CE 321、PROP 159、EV 148×2 并列＝§8 复用对在 SC 侧镜像」的误归类**撤回**：EV 148 组＝**同来源双入口、同值 0、非 §8 复用**（按 source_id 分组与按完整 value_sha256 分组分开判定；POINTER §6a 148 组逐组全列——两侧同 T1/同优先级、148/148 组 decision_control_ids 不同、域恒为 /major_events↔/planned_event_registry）；CE 321/321、PROP 159/159 两侧同哈希＝真复用镜像维持；**525 真复用对零改动不凑数**；§1.1/全读账覆盖闭合描述同步；SC 双入口＝来源展示关联、值身份复用＝完整哈希相同，二者均不证 P1 值体已读。**(2) ACC-F016 闭合**——§6 四列表重做：七技能入口**逐项精确路径＋三候选根实际命中**（调用串自带 engine/ 前缀→①`ENGINE/engine/…` 拼重不存在→**②`ENGINE.parent`＝仓库根命中**；Q1＝novel-conception-reviewer、P1＝novel-conception-deliverable-assembler，**真名无 -designer 后缀**，带后缀两路径三根逐一验证均不存在）；「模块可导入」降为「源文件/导入路径静态存在，导入与依赖闭包可执行性未证」；三机器文件**阶段来源拆分**（P1 包↔A2 `p1_manifest` manifest 间接引用；handoff↔A2 `development_handoff` 直接哈希引用；hld-completion↔HLD V1 HF1 契约产物且 **A2 零引用**＝独立 HLD 阶段证据边界，非构思完成记录必含项）；已修正结论（engine 1290 件在库、缺运行目录/migration/机器包、前缀差异不证入口缺失）保留。**(3) ACC-F017 闭合**——#20 主候选**单一目标**（唯一关闭目标＝正文计数口径收敛；反例测试成立：只解决计数即满足主候选，与载体/道具/披露决定无关）；K4/K6 载体改列**独立不发布观察**（非 #20 关闭目标、非独立性理由，证据限度与不发布理由单列）；附带项**逐项处置**（第比利斯时间 register_only／K6 编号进正文 register_only／L502 名片待证（邻接 #11 但关闭条件不覆盖）／字符缺损 existing REG-03），「剥离归 #11/#12/#13」笼统归并撤回；自然语言/§5.2/v4 JSON delta 三方同步，可区分主候选/历史发布/独立观察/外部待授权。计数确证不丢失，传输/人数/面孔/地点撤回不恢复。线上 ISSUE 仍零写操作（OWNER_PENDING）。**acc-001/acc2/acc3 的 FAIL 判定历史保留**；本 v4 待第四步独立复验（acc4），不自宣布 PASS。
