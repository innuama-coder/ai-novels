# duanxian-audit3-impl-001 · 新 ISSUE 提交登记 v2（impl2-001 修正版）

- 版本：v2，2026-11-15，作业 duanxian-audit3-impl2-001（JOB #2394）按 acc-001 验收记录 §7/ACC-F009＋ACC-F007 修正。v1 登记内容原样保留于本文件（历史 hash、授权与回读记录零改动）；v2 只新增字段、收据与重归类结论，不补造任何历史请求日志。
- 作业（v1 原文）：JOB #2382（duanxian-audit3-impl-001，R3 审视实施）
- 审计基线 BASE：`92573f1cca40f37cee04d2beb8708ff33ba603d6`；定义书 @ `024ef15a201a536592162b5f8442cf6a57699a8d`
- 输入快照：`.kunora/inputs/open-issues-snapshot-20261114b.md`（SHA-256 `f6cc9ddf44be3ee199c7993e0a37bc56813cb6be8b5e238da35a9f6ffeeffd90`）
- 提交规程：定义书 §5.1（POST 仅 title+body；201 判成功；逐条 GET 回读核对标题/标记/正文 SHA-256；标记格式 `<!-- duanxian-audit3-impl-001:DX3-Fnnn:base=<BASE> -->`）
- v1 提交时点实时核验（原文保留）：`GET /repos/innuama-coder/ai-novels/issues?state=all` 分页全量＝13 条、与冻结快照一致、无 PR、无第三方新增。
- v2 线上复核（impl2-001，公开无认证 GET，2026-11-15）：全量 22 条、无 PR；#14–#22 全部 `state=open`，`created_at` 与验收附录 B 一致，正文 SHA-256 与 v1 提交体逐一相同——**线上原文未动**。本轮零评论/零关闭/零编辑/零新建（见 §2 各条 `retrieved_body_sha256` 与文末 v2 JSON `impl2_recheck`）。
- 证据缺失声明（ACC-F009 要求如实说明）：v1 交付未留存逐条 POST 响应原始日志，本登记不补造；九条发布成功的事实依据＝线上 live 状态＋v1 逐条 GET 回读哈希（`body_sha256_sent`＝`body_sha256_readback`）＋acc-001 附录 B 独立回读收据＋impl2-001 复核 GET，四方一致。

## 1. 本次创建（v1 表原样保留；created_at 等全字段见 §2 与 v2 JSON）

| 编号 | ISSUE | 标题 | 链接 | 回读 |
|---|---|---|---|---|
| DX3-F001 | #14 | [断线审视] 多层设计产物的文档路径与引用在重构后失配（既有三条 ISSUE 范围外的路径漂移族） | https://github.com/innuama-coder/ai-novels/issues/14 | OK（SHA-256 一致） |
| DX3-F002 | #15 | [断线审视] 审阅简报 brief.html 版本链引用全失效、处于审阅真空并含已废止内容 | https://github.com/innuama-coder/ai-novels/issues/15 | OK |
| DX3-F003 | #16 | [断线审视] 主体定义 v1.1 残留旧终局口径而构思审计全 passed 未捕获 | https://github.com/innuama-coder/ai-novels/issues/16 | OK |
| DX3-F004 | #17 | [断线审视] HLD-04 与 HLD-07 对处置组是否掌握行动层情报的表述相反 | https://github.com/innuama-coder/ai-novels/issues/17 | OK |
| DX3-F005 | #18 | [断线审视] PRD 终包对 HLD 入口门状态自述矛盾（L34 与 L281 相反） | https://github.com/innuama-coder/ai-novels/issues/18 | OK |
| DX3-F006 | #19 | [断线审视] 历史层启动与归责口径同批准层「沈逾非启动者」存在未声明冲突族（G02） | https://github.com/innuama-coder/ai-novels/issues/19 | OK |
| DX3-F007 | #20 | [断线审视] 六月写作线素材与正文对同一事件的事实互斥未收敛（K1 传输/人数/面孔/载体/地点/匹配次数） | https://github.com/innuama-coder/ai-novels/issues/20 | OK |
| DX3-F008 | #21 | [断线审视] 批准报告控制条目残留早期迭代计数（「十个环境」vs 实际 12、「六个样章片段」vs 实际 3） | https://github.com/innuama-coder/ai-novels/issues/21 | OK |
| DX3-F009 | #22 | [断线审视] 构思工程脚本路径失配扩展至样片驱动器等三处（#1 同根因、其关闭范围之外） | https://github.com/innuama-coder/ai-novels/issues/22 | OK |

回读明细（正文 SHA-256，sent＝提交体，readback＝GET 回读体）与逐条结果见文末 JSON。9/9 成功、0 失败；每条含六要素（标记/BASE/编号/责任阶段/严重度、可证伪命题、应然实然证据、与 13 条差异、建议与关闭条件、采纳边界）。
**v2 批注**：上表为 v1 事实记录（发布动作确实发生且回读一致）。v1 报告「9 条五门全过/零重复」的总声明已按 ACC-F007 撤回——#14/#22 重归类 out_of_scope/existing，#15/#16/#17/#19/#20 命题收窄，#18/#21 保留确证核心。逐门状态见 §2，四维差异表见 §5.2；线上处置建议（均 OWNER_PENDING）见 `impl2-001-external-correction-proposal.md`。

## 2. 候选全字段登记 v2（定义 §5.1 要求字段；ACC-F009 产物）

五门（定义书 L107）：①范围门（属 DX-G01–09 构思/设计命题）②证据门（应然实然有 BASE 原文证据含版本/上下文/反证）③查重门（与 13 条＋发布前实时全状态语义比较）④目标门（单一修订目标/责任阶段/独立验收条件）⑤边界门（只提设计改进，不改故事）。

### 2.1 DX3-F001（#14）
- finding_id：DX3-F001
- dedup_disposition：`reclassified_out_of_scope_existing`（v1 submit → v2 按 ACC-F007/§3.7 重归类）
- closest_existing：#1（构思 CLI 路径族）、#3（素材路径迁移）、#4（.gitattributes 前缀）
- difference_reason（v2）：自承「文档迁移工程整理」，责任阶段与关闭条件为全树路径工程整理；旧条范围排除后未证明任何独立构思/设计控制受影响——**与既有条无机制差异成立**
- publish_gate：v1 判五门全过 → v2 撤回：门①不成立（定义 §4.3/S05 停止工程缺陷扩展）、门③不成立（与 #1/#3/#4 同机制）
- marker：`<!-- duanxian-audit3-impl-001:DX3-F001:base=92573f1cca40f37cee04d2beb8708ff33ba603d6 -->`
- body_sha256（sent＝readback＝线上现行）：`5fb154303e9e1d576e746c1cf2bdf0f836d4caad749a01b4fe18bb73f0cb2d28`
- publish_status：`published_open`＋v2 重归类 out_of_scope/existing；线上处置建议＝Owner 允许时关闭并说明（OWNER_PENDING，未执行）
- number：14；url：https://github.com/innuama-coder/ai-novels/issues/14；created_at：`2026-11-14T12:52:13Z`（验收附录 B；impl2 GET 同）；get_verified：true（v1 回读＋验收附录 B＋impl2-001 GET 三方一致）；retrieved_body_sha256（impl2-001）：`5fb154303e9e1d576e746c1cf2bdf0f836d4caad749a01b4fe18bb73f0cb2d28`

### 2.2 DX3-F002（#15）
- finding_id：DX3-F002
- dedup_disposition：`published_narrowed`（收窄保留；acc-001 §3.2）
- closest_existing：#6（版本指称混用——对象不同：brief.html 审阅简报 vs canonical 规格）、#3（引用失效——载体不同：冻结快照内文档 vs 线上审阅简报）
- difference_reason：审阅简报版本链引用与审阅状态可见性无既有条覆盖；#6/#3 机制邻接但对象与控制不同
- publish_gate：v1 判五门全过 → v2：门②部分不成立（「全部失配」全称失败：I3 core-character v1.0 相符、I2 世界契约件不在库不可对照；周岚婚姻＝对象混淆；三个月 vs D+58＝非同一事件）；收窄命题「部分版本引用待对齐且 awaiting_author_review 状态需保持可见」仍过门
- marker：`<!-- duanxian-audit3-impl-001:DX3-F002:base=92573f1cca40f37cee04d2beb8708ff33ba603d6 -->`
- body_sha256：`7581445b5ab13913ec59aa2859915cbad7f9de3a5dc5caa336a50de4787073cc`
- publish_status：`published_open`；线上原文含被撤回断言，编辑建议 OWNER_PENDING（GET 保存新旧 hash 后改写为窄观察，或不足独立立项则关闭）
- number：15；url：https://github.com/innuama-coder/ai-novels/issues/15；created_at：`2026-11-14T12:52:18Z`；get_verified：true；retrieved_body_sha256（impl2-001）：`7581445b5ab13913ec59aa2859915cbad7f9de3a5dc5caa336a50de4787073cc`

### 2.3 DX3-F003（#16）
- finding_id：DX3-F003
- dedup_disposition：`published_narrowed`
- closest_existing：#10（终局披露族——控制不同：主体定义版本残留 vs 叙事披露顺序）
- difference_reason：subject-definition v1.1 残留旧终局口径无既有条覆盖；#10 对象为叙事顺序非版本残留
- publish_gate：v1 判五门全过 → v2：门②部分不成立（「三处旧终局直接违反第一部不知情」为误判：L34 创伤≠已知受骗、L41 明指第二部、L61 时间线 delegated；causal 版本定位改正为 v1.1 非 v2.0）；版本事实（v1.1）与残留观察保留
- marker：`<!-- duanxian-audit3-impl-001:DX3-F003:base=92573f1cca40f37cee04d2beb8708ff33ba603d6 -->`
- body_sha256：`c43c926d355ea5a4c1ce9b088cec9b3a14f4c66684baa1a0124ae7c772291300`
- publish_status：`published_open`；撤回违规结论的编辑建议 OWNER_PENDING；不另立「纠错 Issue」
- number：16；url：https://github.com/innuama-coder/ai-novels/issues/16；created_at：`2026-11-14T12:52:22Z`；get_verified：true；retrieved_body_sha256（impl2-001）：`c43c926d355ea5a4c1ce9b088cec9b3a14f4c66684baa1a0124ae7c772291300`

### 2.4 DX3-F004（#17）
- finding_id：DX3-F004
- dedup_disposition：`published_reanchored_insufficient_evidence`（现行强命题证据不足；设计对齐问题保留待证）
- closest_existing：#5（HLD 追踪门——控制不同：权限/知情映射 vs 事件-状态绑定）
- difference_reason：HLD-04 权限列与 HLD-07 知情时点的映射问题无既有条覆盖；#5 为 trace 完整性
- publish_gate：v1 判五门全过 → v2：门②不成立（「两者不可能同时为真」缺同一时点/同一信息粒度桥接；源列是 Known by 非 visible_to）；重锚定后窄命题「权限/实际知情/时序映射待澄清」过门，与 #5 不同的设计裁决须在补桥接后证明
- marker：`<!-- duanxian-audit3-impl-001:DX3-F004:base=92573f1cca40f37cee04d2beb8708ff33ba603d6 -->`
- body_sha256：`ddae703bfc11bf45f5631a21290430a4d9efc8507830b9c2e97e7eb6cd5e4e93`
- publish_status：`published_open`；收窄编辑建议 OWNER_PENDING（visible_to→Known by、删「不可能同时为真」）
- number：17；url：https://github.com/innuama-coder/ai-novels/issues/17；created_at：`2026-11-14T12:52:27Z`；get_verified：true；retrieved_body_sha256（impl2-001）：`ddae703bfc11bf45f5631a21290430a4d9efc8507830b9c2e97e7eb6cd5e4e93`
- v2 锚点（重锚定依据）：HLD-04＝`duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/artifacts/04-character-system.md` L15（Information permission 列）L21（「危机解除后……掌握行动层；原因层须复核申请」）；HLD-07＝同目录 `artifacts/07-time-information-system.md` L15（Known by 列）L20（HLD-07-04 行动层 D+57；HLD-07-05 完整原因层 Hidden from 处置组＋读者）

### 2.5 DX3-F005（#18）
- finding_id：DX3-F005
- dedup_disposition：`published_confirmed_core_cause_marked_inference`（核心确证保留；成因标推断）
- closest_existing：#6（状态自述族——对象不同：PRD 终包门状态 vs canonical 标签）
- difference_reason：PRD 终包 L34「入口仍需等待人类评审」vs L281「人类 PRD 评审已确认…pass_to_hld」前后状态未标过程/终态，无既有条覆盖
- publish_gate：v1 判五门全过 → v2：核心成立、低严重度合理、过门维持；成因（07-10 gate-report pending → 07-13 confirmed 的确认时间窗）为旁证推断非直证；不能据此断言今天 HLD 未获准进入
- marker：`<!-- duanxian-audit3-impl-001:DX3-F005:base=92573f1cca40f37cee04d2beb8708ff33ba603d6 -->`
- body_sha256：`34c9ec64c3f1aaa8d1cce96566caa4f857d5c400649826b2b415699fee6ea9b4`
- publish_status：`published_open`；核心无需因验收失败而关闭；历史终包状态说明的实施守授权边界
- number：18；url：https://github.com/innuama-coder/ai-novels/issues/18；created_at：`2026-11-14T12:52:32Z`；get_verified：true；retrieved_body_sha256（impl2-001）：`34c9ec64c3f1aaa8d1cce96566caa4f857d5c400649826b2b415699fee6ea9b4`

### 2.6 DX3-F006（#19）
- finding_id：DX3-F006
- dedup_disposition：`published_narrowed`
- closest_existing：#8（参与链族——对象不同：沈逾启动归责 vs 周岚维护例外）
- difference_reason：六月线濒死/生前转移与批准「死亡后加载」的适配映射无既有条覆盖
- publish_gate：v1 判五门全过 → v2：门②部分不成立（「研究员参与执行即违规」被反例否定——批准禁「决策者/启动者」允「执行者」；「没有任何口径迁移声明」被否定——`duanxian/README.md` L22–23 历史链隔离＋`duanxian/novel-goals.md` L67–71 专列历史隔离）；窄子集「特定残留的逐条适配映射是否足够」保留过门
- marker：`<!-- duanxian-audit3-impl-001:DX3-F006:base=92573f1cca40f37cee04d2beb8708ff33ba603d6 -->`
- body_sha256：`8521063d9fa73ad6e338cfbcf3749da1de54dfc0dab69bc77ad5e304a88cf5d0`
- publish_status：`published_open`；删除两项被反例否定断言的编辑建议 OWNER_PENDING
- number：19；url：https://github.com/innuama-coder/ai-novels/issues/19；created_at：`2026-11-14T12:52:37Z`；get_verified：true；retrieved_body_sha256（impl2-001）：`8521063d9fa73ad6e338cfbcf3749da1de54dfc0dab69bc77ad5e304a88cf5d0`
- v2 窄子集证据：LLD K2（`duanxian/design/specs/lld/scenes/2026-06-07-scene-K2.md` L26）、`design-scenes-draft.md` L15–22、PRD L38/L120/L190

### 2.7 DX3-F007（#20）
- finding_id：DX3-F007
- dedup_disposition：`published_narrowed`
- closest_existing：#11（十秒沉默——信息先用后到族）、#12（郑柏舟显名——载体对齐）、#13（记忆可检索——机制邻接）
- difference_reason：正文与素材对同一事件的计数矛盾（两次 vs 七次）及载体对齐子集无既有条直接覆盖；#11/#12/#13 为子项比较对象
- publish_gate：v1 判五门全过 → v2：门②部分不成立（人数、面孔同一性、「未写即未发生」、仓库/地点等互斥未证明——acc-001 §3.5/ACC-F006）；计数确证保留：正文 L191/L195 两次匹配（67%→82%）vs L464「七次匹配」（L363 两次、L379 七节点）；「七」污染源＝R07 §2.2 表/片段 C 第七次回放（成因推断）
- marker：`<!-- duanxian-audit3-impl-001:DX3-F007:base=92573f1cca40f37cee04d2beb8708ff33ba603d6 -->`
- body_sha256：`eea29d09a5e19aaa994ab967e7206b98658da590c514f8920b709470543b5a9f`
- publish_status：`published_open`；撤回未证互斥、保留单一对齐目标的编辑建议 OWNER_PENDING；多机制若不能形成单一目标则关闭，有效证据记入报告，不批量拆发
- number：20；url：https://github.com/innuama-coder/ai-novels/issues/20；created_at：`2026-11-14T12:52:42Z`；get_verified：true；retrieved_body_sha256（impl2-001）：`eea29d09a5e19aaa994ab967e7206b98658da590c514f8920b709470543b5a9f`

### 2.8 DX3-F008（#21）
- finding_id：DX3-F008
- dedup_disposition：`published_confirmed_core_cause_marked_inference`
- closest_existing：#2（计数核对族——对象不同：A3 控制条目文案 vs README 技能数）
- difference_reason：A3 `/decision_controls/1/statement`「十个环境」vs `/world/environments` 实列 12；`/decision_controls/7/statement`「六个样章片段」vs `/fragments` 实列 3——批准包内部计数矛盾无既有条覆盖
- publish_gate：v1 判五门全过 → v2：两处计数独立复算成立、过门维持；成因「早期迭代计数残留」为推断（h1_plan L893–901 六 briefs 选二、h1_fragments L51–198 六→三死数据块为旁证，生成因果无库内直证）；计数通过≠体验控制通过；现行片段映射改正为 **03/04/06 三项**（v1「两深场景 04/06」少计 03）
- marker：`<!-- duanxian-audit3-impl-001:DX3-F008:base=92573f1cca40f37cee04d2beb8708ff33ba603d6 -->`
- body_sha256：`c10b62c7d1933001565ee9c6676770dd2eacd9b89f04cf29d720e829a34e773b`
- publish_status：`published_open`；如需编辑＝明确「计数不符已证，迭代成因是推测；体验控制是否满足不由计数核对证明」；A3 批准包勘误需另授权，不改原字节
- number：21；url：https://github.com/innuama-coder/ai-novels/issues/21；created_at：`2026-11-14T12:52:47Z`；get_verified：true；retrieved_body_sha256（impl2-001）：`c10b62c7d1933001565ee9c6676770dd2eacd9b89f04cf29d720e829a34e773b`

### 2.9 DX3-F009（#22）
- finding_id：DX3-F009
- dedup_disposition：`reclassified_out_of_scope_existing`（v1 submit → v2 按 ACC-F007/§3.7 重归类）
- closest_existing：#1（自承同根因：构思 CLI 路径族）
- difference_reason（v2）：自承「#1 同根因」；新载体（样片驱动器等三处）不自动形成新控制/新修订目标；静态引用失效不能概括为所有脚本均不可导入（无运行验证）——**与 #1 无机制差异成立**
- publish_gate：v1 判五门全过 → v2 撤回：门①不成立（§4.3/S05）、门③不成立（#1 同族）
- marker：`<!-- duanxian-audit3-impl-001:DX3-F009:base=92573f1cca40f37cee04d2beb8708ff33ba603d6 -->`
- body_sha256：`186d0bd68319530e46757729e7feaaac661d2b988a6284129f510435add6457f`
- publish_status：`published_open`＋v2 重归类 out_of_scope/existing；线上处置建议＝Owner 允许时关闭并说明（OWNER_PENDING，未执行）；工程修复须另授权冻结任务，本轮禁止执行加载器修复/生产测试
- number：22；url：https://github.com/innuama-coder/ai-novels/issues/22；created_at：`2026-11-14T12:52:51Z`；get_verified：true；retrieved_body_sha256（impl2-001）：`186d0bd68319530e46757729e7feaaac661d2b988a6284129f510435add6457f`

## 3. 既有 13 条引用（v1 表保留＋v2 批注；零评论/零关闭/零编辑维持至 impl2-001）

| 既有 | 主题 | R3 处置（v1 原文；详见 impl-001-report.md §5） |
|---|---|---|
| #1 (C-I01) | run.py 七路径＋三测试入口 | 复核属实并精确化（L41-48/L47 失败点/f7ac2db 半改）；不重复提交；范围外同族立 DX3-F009 |
| #2 (C-I02) | 81 vs 82 技能计数 | 实测 engine/skills=82，与 ISSUE 声明一致；无新证据 |
| #3 (C-I03) | 17 素材 LLD 迁移＋R07 章节引用 | 属实；全树文字命中本不在其关闭范围，新实例归 DX3-F001 |
| #4 (C-I04) | .gitattributes engine/ 前缀 | 属实；机制独立，无新载体 |
| #5 (C-I05) | HLD-TRACE-CLOSURE P1 | 补证（06 绑定错位/10 缺行/11 handoff 失衡/01 原子复用） |
| #6 (C-I06) | v2.0/v3.0 标签混用 | 补证（gate-report:9；canonical 六项实质差） |
| #7 (C-I07) | 三个机器包基名缺失 | 佐证（conception-runs 不入库；驱动器代际差异） |
| #8 (C2-I01) | 周岚维护例外参与链 | 补证（proposal 04:21/PRD FREEZE-12/subject:42-43/brief:282/design-task-package L93,97） |
| #9 (C2-I02) | R-07 当前视听 | 补证（PRD S15-16、design:90、tech:233、digital-realm:91、正文:245/255/271、shenyu:27、声音印随） |
| #10 (C2-I03) | 终局自行关闭＋提前披露 | 补证（proposal 04:25,58、PRD 05:26-28+INFO-06、LLD K9 族、design-scenes-draft） |
| #11 (C2-I04) | 十秒沉默来源 | 补证（正文:367 安全通信记录同族） |
| #12 (C2-I05) | 郑柏舟显名 | 补证（betrayer:44-47 记录区省略 vs 正文:365 点名） |
| #13 (C2-I06) | 完整可检索记忆 | 补证（PRD S11-12、proposal 04:23/09:20/12:20、LLD K8、PRD:38,98、视网膜重建） |

**v2 批注（ACC-F007）**：#1 行「范围外同族立 DX3-F009」与 #3 行「新实例归 DX3-F001」两句为 v1 扩发结论，已撤回——F001/F009 重归 out_of_scope/existing（§2.1/§2.9），既有条处置（不重复提交/补证）不变。#8–#13 的应然均以批准层为当前控制、历史内容只是适配反侧（acc-001 §5）；旧 HLD 的 pass_to_hld 与 pending_hld_human_review 保留不同阶段意义，六条内容 Issue 未被本轮评论、编辑或关闭。

## 4. REG-01..08／REJ-01..02（v2 修订；均未发布）

登记不提交八项维持（REG-01 OPEN-01~03 映射缺表、REG-02 qianxu 文件名歧义、REG-03 style-reference 防护缺口＋字符损坏、REG-04 V2 报告 L1613-1646 表格截断、REG-05 A2/A0 revision-037/038 时序、REG-06 48 小时 vs 三个月张力（可相容）、REG-07 素材-正文覆盖缺口＝正常未完成创作、REG-08 PRD 09 风险检查零检出＋00↔09 断链）；publish_gate＝未过门①/④（流程或工程观察，非本轮故事控制命题），publish_status＝`not_published_register_only`，marker/body_sha256＝不适用。

**REJ-01 v2 拆分判定（ACC-F004；v1「亲验后判兼容」整体结论撤回）**：

| 子项 | v2 判定 | 依据 |
|---|---|---|
| PRD FREEZE-05（「学生时代暗恋」） | 与批准层相容，维持不立案 | N05：单侧暗恋相容；程予安为在世妻子而非周岚新增身世 |
| PRD FREEZE-10 L20（「结尾必须呈现研究员事后理解骗局」） | 与 N4「第一部不确认受骗」**需显式历史适配**；与 #10/#16 语义比较后再定候选资格，本轮不发布 | acc-001 §3.3/N08：强要求 vs 开放项，REJ-01 v1 漏读此行 |

REJ-02（proposal 12-ending「封死未来重载」）维持拒绝：L24「系列钩子：不推荐」为建议级（N08 相容）。

## 5.2 四维差异表（ACC-F007 产物；覆盖全部 22 条 all-state）

四维＝对象（管什么）／控制（依哪层控制判）／机制（问题如何发生）／关闭条件（怎样算修好）。候选 #14/#22 与既有 #1/#3/#4 同机制、无新控制，即重归类依据；其余候选给出与最近既有条的对象/控制差。

| 条目 | 对象 | 控制 | 机制 | 关闭条件 |
|---|---|---|---|---|
| 既有 #1 | run.py 运行时路径＋测试入口 | 构思 CLI 可运行性（工程） | 重构后半改（f7ac2db） | 路径修复并过测试 |
| 既有 #2 | README 技能计数声明 | 文档计数准确 | 目录实数 82 vs 声明 81 | 计数勘误 |
| 既有 #3 | 17 份素材 LLD 路径＋R07 引用 | 素材路径有效（工程） | .gitattributes 迁移 | 明示的 17＋5 件修复 |
| 既有 #4 | .gitattributes engine/ 前缀 | 忽略规则机制 | 前缀缺失 | 规则修复 |
| 既有 #5 | HLD-TRACE-CLOSURE P1 追踪门 | 事件-状态绑定可追踪 | 绑定错位/缺行 | trace 补行＋人评关闭 |
| 既有 #6 | v2.0/v3.0 标签指称 | 评审版本指称准确 | 标签混用 | 版本指称澄清 |
| 既有 #7 | 三个机器交付文件 | 交付可复现（工程） | 未留存（conception-runs 不入库为既定策略） | 留存策略声明 |
| 既有 #8 | 周岚维护例外参与链 | 周岚参与边界（批准层封闭） | 历史维护例外链残留 | 参与链对齐批准层 |
| 既有 #9 | R-07 当前视听 | 当前无感官契约（批准层） | 视听残留进载体 | 载体对齐 |
| 既有 #10 | 终局自行关闭＋提前披露 | 终局顺序（批准层封闭） | 披露顺序残留 | 顺序对齐 |
| 既有 #11 | 十秒沉默文字来源 | 信息时序先用后到 | 来源未标 | 来源标注对齐 |
| 既有 #12 | 郑柏舟显名 | 显名禁令（betrayer §7） | 记录区省略 vs 正文点名 | 披露口径对齐 |
| 既有 #13 | 完整可检索记忆/像素重建 | 记忆检索边界（ENV-MEMORY 封闭） | 重建表述残留 | 检索边界对齐 |
| 候选 #15 | brief.html 版本链引用＋审阅状态呈现 | 审阅可见性（awaiting_author_review 须保持可见） | 版本引用与留存件不一致（I0/I1/I4/I5 四项；I3 相符；I2 不在库） | brief 版本引用对齐＋状态可见；GET 存新旧 hash 后编辑或关闭 |
| 候选 #16 | subject-definition v1.1 旧终局残留＋causal 版本定位（实为 v1.1） | 第一部不知情契约（N4） | 历史版本残留未治理；构思审计未捕获（创伤≠已知受骗、L41 第二部、L61 delegated） | 主体定义终局口径治理；撤回违规结论 |
| 候选 #17 | HLD-04 权限列↔HLD-07 知情时点映射 | 处置组行动层/原因层权限分级（Information permission vs Known by） | 同一时点/同一粒度桥接未建立（D+57 行动层 vs 危机解除后原因层复核） | 补齐映射表则保留设计对齐问题，否则关闭 |
| 候选 #18 | PRD 终包 L34/L281 门状态自述 | PRD→HLD 入口门状态记录 | 终包前后行未标过程/终态（07-10–07-13 确认时间窗为旁证） | 历史终包状态说明澄清（勘误需授权） |
| 候选 #19 | 六月线濒死/生前转移 vs 批准死亡后加载 | 死亡后加载终局＋沈逾执行者非启动者（G02） | 历史层-批准层适配映射缺失（总隔离声明在场：README L22-23/novel-goals L67-71） | 逐条适配映射声明；总隔离足够则关闭；不改写故事 |
| 候选 #20 | 正文与素材对同一事件的表述 | 匹配次数一致性＋载体对齐（单次/两次计数契约） | 素材迭代残留进入正文（两次 vs 七次；「七」污染源 R07 §2.2/片段 C） | 单一对齐目标确立；多机制不成单一目标则关闭并记证据 |
| 候选 #21 | A3 decision_controls 计数文案 | 环境/片段体验控制条目 statement | 早期迭代计数残留（推断；h1_plan 六选二/h1_fragments 六→三死数据为旁证） | 控制条目文案与实列对齐（A3 勘误另授权，不改原字节）；计数≠体验控制 |
| 候选 #14（重归类） | 全树文档路径/引用（工程整理） | **无独立故事控制** | 与 #1/#3/#4 同机制：路径迁移后引用失配 | 全树路径工程整理（超出本轮；另授权任务）——本轮关闭建议 OWNER_PENDING |
| 候选 #22（重归类） | 构思工程脚本路径（样片驱动器等） | **无独立故事控制** | 与 #1 同根因路径失配；静态引用失效≠运行失败 | 工程修复另授权冻结任务——本轮关闭建议 OWNER_PENDING |

## 机器可读登记

### v1 JSON（历史原样保留，未改动）

```json
{
  "schema_version": "1.0",
  "job_ref": "duanxian-audit3-impl-001",
  "base_commit": "92573f1cca40f37cee04d2beb8708ff33ba603d6",
  "definition_commit": "024ef15a201a536592162b5f8442cf6a57699a8d",
  "snapshot_sha256": "f6cc9ddf44be3ee199c7993e0a37bc56813cb6be8b5e238da35a9f6ffeeffd90",
  "existing_references": [
    {"iid": "DEDUP-01", "issue": 1, "disposition": "recheck_confirmed_precised"},
    {"iid": "DEDUP-02", "issue": 2, "disposition": "recheck_confirmed"},
    {"iid": "DEDUP-03", "issue": 3, "disposition": "recheck_confirmed_scope_respected"},
    {"iid": "DEDUP-04", "issue": 4, "disposition": "recheck_confirmed"},
    {"iid": "DEDUP-05", "issue": 5, "disposition": "evidence_added"},
    {"iid": "DEDUP-06", "issue": 6, "disposition": "evidence_added"},
    {"iid": "DEDUP-07", "issue": 7, "disposition": "corroborated"},
    {"iid": "DEDUP-08", "issue": 8, "disposition": "evidence_added"},
    {"iid": "DEDUP-09", "issue": 9, "disposition": "evidence_added"},
    {"iid": "DEDUP-10", "issue": 10, "disposition": "evidence_added"},
    {"iid": "DEDUP-11", "issue": 11, "disposition": "evidence_added"},
    {"iid": "DEDUP-12", "issue": 12, "disposition": "evidence_added"},
    {"iid": "DEDUP-13", "issue": 13, "disposition": "evidence_added"}
  ],
  "candidates": [
    {"id": "DX3-F001", "verdict": "submit", "issue": 14},
    {"id": "DX3-F002", "verdict": "submit", "issue": 15},
    {"id": "DX3-F003", "verdict": "submit", "issue": 16},
    {"id": "DX3-F004", "verdict": "submit", "issue": 17},
    {"id": "DX3-F005", "verdict": "submit", "issue": 18},
    {"id": "DX3-F006", "verdict": "submit", "issue": 19},
    {"id": "DX3-F007", "verdict": "submit", "issue": 20},
    {"id": "DX3-F008", "verdict": "submit", "issue": 21},
    {"id": "DX3-F009", "verdict": "submit", "issue": 22},
    {"id": "REG-01", "verdict": "register_only", "subject": "OPEN-01~03 映射缺表（intake L21 有正文响应）"},
    {"id": "REG-02", "verdict": "register_only", "subject": "writer-qianxu 文件名歧义（#3 迁移表已缓解）"},
    {"id": "REG-03", "verdict": "register_only", "subject": "style-reference 模仿防护声明缺口＋字符损坏"},
    {"id": "REG-04", "verdict": "register_only", "subject": "V2 报告 L1613-1646 表格截断"},
    {"id": "REG-05", "verdict": "register_only", "subject": "A2/A0 revision-037/038 时序呈现"},
    {"id": "REG-06", "verdict": "register_only", "subject": "48 小时 vs 三个月进入时序张力（可相容）"},
    {"id": "REG-07", "verdict": "register_only", "subject": "素材-正文覆盖缺口＝正常未完成创作"},
    {"id": "REG-08", "verdict": "register_only", "subject": "PRD 09 风险检查零检出＋00↔09 断链（流程观察）"},
    {"id": "REJ-01", "verdict": "rejected_after_recheck", "subject": "PRD FREEZE-05/10 与 G05/G08 冲突（亲验后判兼容）"},
    {"id": "REJ-02", "verdict": "rejected_after_recheck", "subject": "proposal 12-ending 封死未来重载（实为建议级）"}
  ],
  "created": [
    {"iid": "DX3-F001", "number": 14, "url": "https://github.com/innuama-coder/ai-novels/issues/14", "readback_ok": true, "body_sha256_sent": "5fb154303e9e1d576e746c1cf2bdf0f836d4caad749a01b4fe18bb73f0cb2d28", "body_sha256_readback": "5fb154303e9e1d576e746c1cf2bdf0f836d4caad749a01b4fe18bb73f0cb2d28"},
    {"iid": "DX3-F002", "number": 15, "url": "https://github.com/innuama-coder/ai-novels/issues/15", "readback_ok": true, "body_sha256_sent": "7581445b5ab13913ec59aa2859915cbad7f9de3a5dc5caa336a50de4787073cc", "body_sha256_readback": "7581445b5ab13913ec59aa2859915cbad7f9de3a5dc5caa336a50de4787073cc"},
    {"iid": "DX3-F003", "number": 16, "url": "https://github.com/innuama-coder/ai-novels/issues/16", "readback_ok": true, "body_sha256_sent": "c43c926d355ea5a4c1ce9b088cec9b3a14f4c66684baa1a0124ae7c772291300", "body_sha256_readback": "c43c926d355ea5a4c1ce9b088cec9b3a14f4c66684baa1a0124ae7c772291300"},
    {"iid": "DX3-F004", "number": 17, "url": "https://github.com/innuama-coder/ai-novels/issues/17", "readback_ok": true, "body_sha256_sent": "ddae703bfc11bf45f5631a21290430a4d9efc8507830b9c2e97e7eb6cd5e4e93", "body_sha256_readback": "ddae703bfc11bf45f5631a21290430a4d9efc8507830b9c2e97e7eb6cd5e4e93"},
    {"iid": "DX3-F005", "number": 18, "url": "https://github.com/innuama-coder/ai-novels/issues/18", "readback_ok": true, "body_sha256_sent": "34c9ec64c3f1aaa8d1cce96566caa4f857d5c400649826b2b415699fee6ea9b4", "body_sha256_readback": "34c9ec64c3f1aaa8d1cce96566caa4f857d5c400649826b2b415699fee6ea9b4"},
    {"iid": "DX3-F006", "number": 19, "url": "https://github.com/innuama-coder/ai-novels/issues/19", "readback_ok": true, "body_sha256_sent": "8521063d9fa73ad6e338cfbcf3749da1de54dfc0dab69bc77ad5e304a88cf5d0", "body_sha256_readback": "8521063d9fa73ad6e338cfbcf3749da1de54dfc0dab69bc77ad5e304a88cf5d0"},
    {"iid": "DX3-F007", "number": 20, "url": "https://github.com/innuama-coder/ai-novels/issues/20", "readback_ok": true, "body_sha256_sent": "eea29d09a5e19aaa994ab967e7206b98658da590c514f8920b709470543b5a9f", "body_sha256_readback": "eea29d09a5e19aaa994ab967e7206b98658da590c514f8920b709470543b5a9f"},
    {"iid": "DX3-F008", "number": 21, "url": "https://github.com/innuama-coder/ai-novels/issues/21", "readback_ok": true, "body_sha256_sent": "c10b62c7d1933001565ee9c6676770dd2eacd9b89f04cf29d720e829a34e773b", "body_sha256_readback": "c10b62c7d1933001565ee9c6676770dd2eacd9b89f04cf29d720e829a34e773b"},
    {"iid": "DX3-F009", "number": 22, "url": "https://github.com/innuama-coder/ai-novels/issues/22", "readback_ok": true, "body_sha256_sent": "186d0bd68319530e46757729e7feaaac661d2b988a6284129f510435add6457f", "body_sha256_readback": "186d0bd68319530e46757729e7feaaac661d2b988a6284129f510435add6457f"}
  ],
  "failures": []
}
```

### v2 JSON（schema 2.0；全字段登记，ACC-F009 产物；纠错后仍保留上方 v1 hash 与授权记录）

```json
{
  "schema_version": "2.0",
  "job_ref": "duanxian-audit3-impl-001",
  "revised_by_job": "duanxian-audit3-impl2-001",
  "revision_source": "acc-001 §7 ACC-F007/ACC-F009",
  "base_commit": "92573f1cca40f37cee04d2beb8708ff33ba603d6",
  "definition_commit": "024ef15a201a536592162b5f8442cf6a57699a8d",
  "snapshot_sha256": "f6cc9ddf44be3ee199c7993e0a37bc56813cb6be8b5e238da35a9f6ffeeffd90",
  "evidence_gap_disclosure": "v1 未留存逐条 POST 原始日志；成功事实由 live 状态＋v1 回读 hash＋acc-001 附录 B＋impl2 GET 四方一致支撑，不补造历史日志",
  "existing_references": [
    {"iid": "DEDUP-01", "issue": 1, "disposition": "recheck_confirmed_precised", "v2_note": "v1『同族立 F009』撤回；F009 重归 out_of_scope/existing"},
    {"iid": "DEDUP-02", "issue": 2, "disposition": "recheck_confirmed"},
    {"iid": "DEDUP-03", "issue": 3, "disposition": "recheck_confirmed_scope_respected", "v2_note": "v1『新实例归 F001』撤回；F001 重归 out_of_scope/existing"},
    {"iid": "DEDUP-04", "issue": 4, "disposition": "recheck_confirmed"},
    {"iid": "DEDUP-05", "issue": 5, "disposition": "evidence_added"},
    {"iid": "DEDUP-06", "issue": 6, "disposition": "evidence_added"},
    {"iid": "DEDUP-07", "issue": 7, "disposition": "corroborated"},
    {"iid": "DEDUP-08", "issue": 8, "disposition": "evidence_added"},
    {"iid": "DEDUP-09", "issue": 9, "disposition": "evidence_added"},
    {"iid": "DEDUP-10", "issue": 10, "disposition": "evidence_added", "v2_note": "FREEZE-10 适配子问题回归本族比较（REJ-01 拆分）"},
    {"iid": "DEDUP-11", "issue": 11, "disposition": "evidence_added"},
    {"iid": "DEDUP-12", "issue": 12, "disposition": "evidence_added"},
    {"iid": "DEDUP-13", "issue": 13, "disposition": "evidence_added"}
  ],
  "candidates": [
    {"finding_id": "DX3-F001", "dedup_disposition": "reclassified_out_of_scope_existing", "closest_existing": [1, 3, 4], "difference_reason": "自承文档迁移工程整理，无独立故事控制，与既有同机制", "publish_gate": "v1 五门全过→撤回；门①范围门不成立（§4.3/S05），门③与 #1/#3/#4 机制重复", "marker": "<!-- duanxian-audit3-impl-001:DX3-F001:base=92573f1cca40f37cee04d2beb8708ff33ba603d6 -->", "body_sha256": "5fb154303e9e1d576e746c1cf2bdf0f836d4caad749a01b4fe18bb73f0cb2d28", "publish_status": "published_open; reclassified out_of_scope/existing; owner close recommendation OWNER_PENDING", "number": 14, "url": "https://github.com/innuama-coder/ai-novels/issues/14", "created_at": "2026-11-14T12:52:13Z", "get_verified": true, "retrieved_body_sha256": "5fb154303e9e1d576e746c1cf2bdf0f836d4caad749a01b4fe18bb73f0cb2d28"},
    {"finding_id": "DX3-F002", "dedup_disposition": "published_narrowed", "closest_existing": [6, 3], "difference_reason": "审阅简报版本链引用与审阅状态可见性无既有条覆盖；#6/#3 机制邻接但对象不同", "publish_gate": "v1 五门全过→门②部分不成立（全称失配/对象混淆/非同一事件互斥撤回）；窄命题过门", "marker": "<!-- duanxian-audit3-impl-001:DX3-F002:base=92573f1cca40f37cee04d2beb8708ff33ba603d6 -->", "body_sha256": "7581445b5ab13913ec59aa2859915cbad7f9de3a5dc5caa336a50de4787073cc", "publish_status": "published_open; narrowed; edit proposal OWNER_PENDING", "number": 15, "url": "https://github.com/innuama-coder/ai-novels/issues/15", "created_at": "2026-11-14T12:52:18Z", "get_verified": true, "retrieved_body_sha256": "7581445b5ab13913ec59aa2859915cbad7f9de3a5dc5caa336a50de4787073cc"},
    {"finding_id": "DX3-F003", "dedup_disposition": "published_narrowed", "closest_existing": [10], "difference_reason": "主体定义版本残留无既有条覆盖；#10 为叙事顺序", "publish_gate": "v1 五门全过→门②部分不成立（三处直接违反为误判；causal 定位改 v1.1）；版本事实保留", "marker": "<!-- duanxian-audit3-impl-001:DX3-F003:base=92573f1cca40f37cee04d2beb8708ff33ba603d6 -->", "body_sha256": "c43c926d355ea5a4c1ce9b088cec9b3a14f4c66684baa1a0124ae7c772291300", "publish_status": "published_open; narrowed; edit proposal OWNER_PENDING", "number": 16, "url": "https://github.com/innuama-coder/ai-novels/issues/16", "created_at": "2026-11-14T12:52:22Z", "get_verified": true, "retrieved_body_sha256": "c43c926d355ea5a4c1ce9b088cec9b3a14f4c66684baa1a0124ae7c772291300"},
    {"finding_id": "DX3-F004", "dedup_disposition": "published_reanchored_insufficient_evidence", "closest_existing": [5], "difference_reason": "权限/知情映射与 #5 trace 完整性控制不同", "publish_gate": "v1 五门全过→门②不成立（『不可能同时为真』缺同时点/同粒度桥接）；重锚定窄命题过门待证", "marker": "<!-- duanxian-audit3-impl-001:DX3-F004:base=92573f1cca40f37cee04d2beb8708ff33ba603d6 -->", "body_sha256": "ddae703bfc11bf45f5631a21290430a4d9efc8507830b9c2e97e7eb6cd5e4e93", "publish_status": "published_open; reanchored (HLD-04 L15/L21 vs HLD-07 L15/L20); edit proposal OWNER_PENDING", "number": 17, "url": "https://github.com/innuama-coder/ai-novels/issues/17", "created_at": "2026-11-14T12:52:27Z", "get_verified": true, "retrieved_body_sha256": "ddae703bfc11bf45f5631a21290430a4d9efc8507830b9c2e97e7eb6cd5e4e93"},
    {"finding_id": "DX3-F005", "dedup_disposition": "published_confirmed_core_cause_marked_inference", "closest_existing": [6], "difference_reason": "PRD 终包门状态自述无既有条覆盖", "publish_gate": "核心成立过门维持；成因（07-10→07-13 确认时间窗）为旁证推断", "marker": "<!-- duanxian-audit3-impl-001:DX3-F005:base=92573f1cca40f37cee04d2beb8708ff33ba603d6 -->", "body_sha256": "34c9ec64c3f1aaa8d1cce96566caa4f857d5c400649826b2b415699fee6ea9b4", "publish_status": "published_open; core confirmed; no forced closure", "number": 18, "url": "https://github.com/innuama-coder/ai-novels/issues/18", "created_at": "2026-11-14T12:52:32Z", "get_verified": true, "retrieved_body_sha256": "34c9ec64c3f1aaa8d1cce96566caa4f857d5c400649826b2b415699fee6ea9b4"},
    {"finding_id": "DX3-F006", "dedup_disposition": "published_narrowed", "closest_existing": [8], "difference_reason": "沈逾启动归责适配映射与 #8 周岚参与链对象不同", "publish_gate": "v1 五门全过→门②部分不成立（执行≠违规；隔离声明在场）；窄子集（K2:26/design-scenes L15-22/PRD L38,120,190）保留", "marker": "<!-- duanxian-audit3-impl-001:DX3-F006:base=92573f1cca40f37cee04d2beb8708ff33ba603d6 -->", "body_sha256": "8521063d9fa73ad6e338cfbcf3749da1de54dfc0dab69bc77ad5e304a88cf5d0", "publish_status": "published_open; narrowed; edit proposal OWNER_PENDING", "number": 19, "url": "https://github.com/innuama-coder/ai-novels/issues/19", "created_at": "2026-11-14T12:52:37Z", "get_verified": true, "retrieved_body_sha256": "8521063d9fa73ad6e338cfbcf3749da1de54dfc0dab69bc77ad5e304a88cf5d0"},
    {"finding_id": "DX3-F007", "dedup_disposition": "published_narrowed", "closest_existing": [11, 12, 13], "difference_reason": "正文计数矛盾（L191/L195 两次 vs L464 七次）无既有条直接覆盖；#11/#12/#13 为子项比较", "publish_gate": "v1 五门全过→门②部分不成立（人数/面孔/未写即未发生/仓库地点互斥未证）；计数确证保留", "marker": "<!-- duanxian-audit3-impl-001:DX3-F007:base=92573f1cca40f37cee04d2beb8708ff33ba603d6 -->", "body_sha256": "eea29d09a5e19aaa994ab967e7206b98658da590c514f8920b709470543b5a9f", "publish_status": "published_open; narrowed to counting + carrier alignment subset; edit proposal OWNER_PENDING", "number": 20, "url": "https://github.com/innuama-coder/ai-novels/issues/20", "created_at": "2026-11-14T12:52:42Z", "get_verified": true, "retrieved_body_sha256": "eea29d09a5e19aaa994ab967e7206b98658da590c514f8920b709470543b5a9f"},
    {"finding_id": "DX3-F008", "dedup_disposition": "published_confirmed_core_cause_marked_inference", "closest_existing": [2], "difference_reason": "A3 控制条目计数矛盾（十 vs 12、六 vs 3）无既有条覆盖", "publish_gate": "两处计数独立复算成立过门维持；迭代残留成因＝推断；现行片段映射改正 03/04/06；计数通过≠体验控制通过", "marker": "<!-- duanxian-audit3-impl-001:DX3-F008:base=92573f1cca40f37cee04d2beb8708ff33ba603d6 -->", "body_sha256": "c10b62c7d1933001565ee9c6676770dd2eacd9b89f04cf29d720e829a34e773b", "publish_status": "published_open; core confirmed; A3 erratum requires separate authorization", "number": 21, "url": "https://github.com/innuama-coder/ai-novels/issues/21", "created_at": "2026-11-14T12:52:47Z", "get_verified": true, "retrieved_body_sha256": "c10b62c7d1933001565ee9c6676770dd2eacd9b89f04cf29d720e829a34e773b"},
    {"finding_id": "DX3-F009", "dedup_disposition": "reclassified_out_of_scope_existing", "closest_existing": [1], "difference_reason": "自承 #1 同根因；新载体不形成新控制；静态引用失效≠运行验证失败", "publish_gate": "v1 五门全过→撤回；门①不成立，门③与 #1 同族", "marker": "<!-- duanxian-audit3-impl-001:DX3-F009:base=92573f1cca40f37cee04d2beb8708ff33ba603d6 -->", "body_sha256": "186d0bd68319530e46757729e7feaaac661d2b988a6284129f510435add6457f", "publish_status": "published_open; reclassified out_of_scope/existing; owner close recommendation OWNER_PENDING", "number": 22, "url": "https://github.com/innuama-coder/ai-novels/issues/22", "created_at": "2026-11-14T12:52:51Z", "get_verified": true, "retrieved_body_sha256": "186d0bd68319530e46757729e7feaaac661d2b988a6284129f510435add6457f"},
    {"finding_id": "REG-01", "dedup_disposition": "register_only", "closest_existing": [], "difference_reason": "流程观察非故事控制", "publish_gate": "门①/④未过", "marker": null, "body_sha256": null, "publish_status": "not_published_register_only"},
    {"finding_id": "REG-02", "dedup_disposition": "register_only", "closest_existing": [3], "difference_reason": "#3 迁移表已缓解", "publish_gate": "门①/④未过", "marker": null, "body_sha256": null, "publish_status": "not_published_register_only"},
    {"finding_id": "REG-03", "dedup_disposition": "register_only", "closest_existing": [], "difference_reason": "工程/规范观察", "publish_gate": "门①/④未过", "marker": null, "body_sha256": null, "publish_status": "not_published_register_only"},
    {"finding_id": "REG-04", "dedup_disposition": "register_only", "closest_existing": [7], "difference_reason": "机器交付留存族；表格截断为工程观察", "publish_gate": "门①/④未过", "marker": null, "body_sha256": null, "publish_status": "not_published_register_only"},
    {"finding_id": "REG-05", "dedup_disposition": "register_only", "closest_existing": [6], "difference_reason": "版本指称族；时序呈现观察", "publish_gate": "门①/④未过", "marker": null, "body_sha256": null, "publish_status": "not_published_register_only"},
    {"finding_id": "REG-06", "dedup_disposition": "register_only", "closest_existing": [10], "difference_reason": "可相容时序张力", "publish_gate": "门②未过（相容）", "marker": null, "body_sha256": null, "publish_status": "not_published_register_only"},
    {"finding_id": "REG-07", "dedup_disposition": "register_only", "closest_existing": [], "difference_reason": "正常未完成创作非缺陷", "publish_gate": "门①未过", "marker": null, "body_sha256": null, "publish_status": "not_published_register_only"},
    {"finding_id": "REG-08", "dedup_disposition": "register_only", "closest_existing": [5], "difference_reason": "门追踪族流程观察", "publish_gate": "门①/④未过", "marker": null, "body_sha256": null, "publish_status": "not_published_register_only"},
    {"finding_id": "REJ-01", "dedup_disposition": "rejected_split_v2", "closest_existing": [10, 16], "difference_reason": "v2 拆分：FREEZE-05 相容维持不立案；FREEZE-10 L20 强要求与 N4 第一部不确认受骗需显式历史适配，与 #10/#16 比较后再定资格", "publish_gate": "v1 整体拒绝→v2 拆分；FREEZE-10 子项本轮不发布", "marker": null, "body_sha256": null, "publish_status": "not_published; FREEZE-10 sub-item pending comparison"},
    {"finding_id": "REJ-02", "dedup_disposition": "rejected_after_recheck", "closest_existing": [10], "difference_reason": "『系列钩子：不推荐』为建议级（N08 相容）", "publish_gate": "维持拒绝", "marker": null, "body_sha256": null, "publish_status": "not_published"}
  ],
  "created": [
    {"iid": "DX3-F001", "finding_id": "DX3-F001", "number": 14, "url": "https://github.com/innuama-coder/ai-novels/issues/14", "created_at": "2026-11-14T12:52:13Z", "created_at_source": "acc-001 附录 B；impl2 GET 一致", "get_verified": true, "body_sha256_sent": "5fb154303e9e1d576e746c1cf2bdf0f836d4caad749a01b4fe18bb73f0cb2d28", "body_sha256_readback": "5fb154303e9e1d576e746c1cf2bdf0f836d4caad749a01b4fe18bb73f0cb2d28", "retrieved_body_sha256": "5fb154303e9e1d576e746c1cf2bdf0f836d4caad749a01b4fe18bb73f0cb2d28"},
    {"iid": "DX3-F002", "finding_id": "DX3-F002", "number": 15, "url": "https://github.com/innuama-coder/ai-novels/issues/15", "created_at": "2026-11-14T12:52:18Z", "created_at_source": "acc-001 附录 B；impl2 GET 一致", "get_verified": true, "body_sha256_sent": "7581445b5ab13913ec59aa2859915cbad7f9de3a5dc5caa336a50de4787073cc", "body_sha256_readback": "7581445b5ab13913ec59aa2859915cbad7f9de3a5dc5caa336a50de4787073cc", "retrieved_body_sha256": "7581445b5ab13913ec59aa2859915cbad7f9de3a5dc5caa336a50de4787073cc"},
    {"iid": "DX3-F003", "finding_id": "DX3-F003", "number": 16, "url": "https://github.com/innuama-coder/ai-novels/issues/16", "created_at": "2026-11-14T12:52:22Z", "created_at_source": "acc-001 附录 B；impl2 GET 一致", "get_verified": true, "body_sha256_sent": "c43c926d355ea5a4c1ce9b088cec9b3a14f4c66684baa1a0124ae7c772291300", "body_sha256_readback": "c43c926d355ea5a4c1ce9b088cec9b3a14f4c66684baa1a0124ae7c772291300", "retrieved_body_sha256": "c43c926d355ea5a4c1ce9b088cec9b3a14f4c66684baa1a0124ae7c772291300"},
    {"iid": "DX3-F004", "finding_id": "DX3-F004", "number": 17, "url": "https://github.com/innuama-coder/ai-novels/issues/17", "created_at": "2026-11-14T12:52:27Z", "created_at_source": "acc-001 附录 B；impl2 GET 一致", "get_verified": true, "body_sha256_sent": "ddae703bfc11bf45f5631a21290430a4d9efc8507830b9c2e97e7eb6cd5e4e93", "body_sha256_readback": "ddae703bfc11bf45f5631a21290430a4d9efc8507830b9c2e97e7eb6cd5e4e93", "retrieved_body_sha256": "ddae703bfc11bf45f5631a21290430a4d9efc8507830b9c2e97e7eb6cd5e4e93"},
    {"iid": "DX3-F005", "finding_id": "DX3-F005", "number": 18, "url": "https://github.com/innuama-coder/ai-novels/issues/18", "created_at": "2026-11-14T12:52:32Z", "created_at_source": "acc-001 附录 B；impl2 GET 一致", "get_verified": true, "body_sha256_sent": "34c9ec64c3f1aaa8d1cce96566caa4f857d5c400649826b2b415699fee6ea9b4", "body_sha256_readback": "34c9ec64c3f1aaa8d1cce96566caa4f857d5c400649826b2b415699fee6ea9b4", "retrieved_body_sha256": "34c9ec64c3f1aaa8d1cce96566caa4f857d5c400649826b2b415699fee6ea9b4"},
    {"iid": "DX3-F006", "finding_id": "DX3-F006", "number": 19, "url": "https://github.com/innuama-coder/ai-novels/issues/19", "created_at": "2026-11-14T12:52:37Z", "created_at_source": "acc-001 附录 B；impl2 GET 一致", "get_verified": true, "body_sha256_sent": "8521063d9fa73ad6e338cfbcf3749da1de54dfc0dab69bc77ad5e304a88cf5d0", "body_sha256_readback": "8521063d9fa73ad6e338cfbcf3749da1de54dfc0dab69bc77ad5e304a88cf5d0", "retrieved_body_sha256": "8521063d9fa73ad6e338cfbcf3749da1de54dfc0dab69bc77ad5e304a88cf5d0"},
    {"iid": "DX3-F007", "finding_id": "DX3-F007", "number": 20, "url": "https://github.com/innuama-coder/ai-novels/issues/20", "created_at": "2026-11-14T12:52:42Z", "created_at_source": "acc-001 附录 B；impl2 GET 一致", "get_verified": true, "body_sha256_sent": "eea29d09a5e19aaa994ab967e7206b98658da590c514f8920b709470543b5a9f", "body_sha256_readback": "eea29d09a5e19aaa994ab967e7206b98658da590c514f8920b709470543b5a9f", "retrieved_body_sha256": "eea29d09a5e19aaa994ab967e7206b98658da590c514f8920b709470543b5a9f"},
    {"iid": "DX3-F008", "finding_id": "DX3-F008", "number": 21, "url": "https://github.com/innuama-coder/ai-novels/issues/21", "created_at": "2026-11-14T12:52:47Z", "created_at_source": "acc-001 附录 B；impl2 GET 一致", "get_verified": true, "body_sha256_sent": "c10b62c7d1933001565ee9c6676770dd2eacd9b89f04cf29d720e829a34e773b", "body_sha256_readback": "c10b62c7d1933001565ee9c6676770dd2eacd9b89f04cf29d720e829a34e773b", "retrieved_body_sha256": "c10b62c7d1933001565ee9c6676770dd2eacd9b89f04cf29d720e829a34e773b"},
    {"iid": "DX3-F009", "finding_id": "DX3-F009", "number": 22, "url": "https://github.com/innuama-coder/ai-novels/issues/22", "created_at": "2026-11-14T12:52:51Z", "created_at_source": "acc-001 附录 B；impl2 GET 一致", "get_verified": true, "body_sha256_sent": "186d0bd68319530e46757729e7feaaac661d2b988a6284129f510435add6457f", "body_sha256_readback": "186d0bd68319530e46757729e7feaaac661d2b988a6284129f510435add6457f", "retrieved_body_sha256": "186d0bd68319530e46757729e7feaaac661d2b988a6284129f510435add6457f"}
  ],
  "failures": [],
  "impl2_recheck": {
    "date": "2026-11-15",
    "method": "unauthenticated GET /repos/innuama-coder/ai-novels/issues?state=all&per_page=100&page=1",
    "result": "22 items, 0 PR; #14-#22 all open; created_at matches acc-001 Appendix B; body SHA-256 identical to v1 sent hashes (line originals unchanged)",
    "writes_this_loop": "none (zero comments/closures/edits/creations by impl2-001)"
  }
}
```

注：v1 `body_sha256_sent`/`body_sha256_readback` 为提交体与 GET 回读体的 SHA-256，九条两两一致（readback_ok 全 true）；v2 `retrieved_body_sha256` 为 impl2-001 公开无认证 GET 复核值，与 v1 哈希逐条相同＝线上原文未动。本轮未获任何 ISSUE 编辑/关闭/评论授权，全部线上处置建议（#14/#22 关闭说明、#15/#16/#17/#19/#20 收窄编辑、#21 口径澄清）状态 OWNER_PENDING，汇总见 `impl2-001-external-correction-proposal.md`。
