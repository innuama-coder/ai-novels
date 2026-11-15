# duanxian-audit3-impl4-001 · 修正执行记录（ACC-F015–F017 · v3→v4）

- 作业：duanxian-audit3-impl4-001（JOB #2493）；基线 remote-agent/duanxian-audit3-acc3-001@8924e22a。
- 指令唯一来源：`acc3-001-acceptance.md` §A3/08（FAIL，修正指令 ACC-F015/F016/F017）。
- 事实核验基线（BASE）：仓库树 92573f1cca40f37cee04d2beb8708ff33ba603d6；问题定义 024ef15a201a536592162b5f8442cf6a57699a8d；冻结快照 f6cc9ddf44be3ee199c7993e0a37bc56813cb6be8b5e238da35a9f6ffeeffd90。
- 本轮零 GitHub 写操作；线上状态仍以 impl2-001 GET 收据为准；冻结快照/spec/模板/历史证据字节零改动。
- 探针脚本位于 `.kunora/impl4-work/`（gitignore，不提交）：`acc_f015_recompute.py`、`acc_f016_verify.sh`、`ev148-classification.md`、`insert_6a.py`。

---

## ACC-F015 · EV 同来源双入口 ≠ 同值复用

**指令**：区分 EV- 前缀来源的「同来源双入口」（148 组，同值 0）与真同值复用（525 对）；修正 POINTER §6 映射并同步 REPORT/LEDGER 收口描述；525 对零改动（不删不增）。

**独立复算（BASE 一步重算，只读）**：`drilldown_index` 4602 条按 `source_id` 分组——EV- 前缀 148 组、每组恰 2 成员（`/major_events` ↔ `/planned_event_registry`，DI 逐组相邻）；按完整 `value_sha256` 分组——4077 distinct、525 个 size=2 对（CE 321、PROP 159、其余 45 为 demands/requirements 等域）；交叉：148/148 组两侧哈希不同（同值 0），无一 EV 组落入 525 对集合；对照组 CE 321/321、PROP 159/159 两侧哈希相同（真复用）。语境回读：`decision_control_ids` 两侧不同 148/148、`exposure` 不同 1 组、`review_priority`/`stage` 全同。样例 EV-TR-3d275aff39f35d69807d：DI 3683/3684，hash 8090695e80df4f0e…/30b8be16f5dcd986…。

**改动**：
- POINTER §6 L284 段重写：CE/PROP＝真复用镜像（同哈希）；EV＝同来源双入口而非复用（148/148 哈希不同）；v3 并列表述撤回。
- POINTER 新增 §6a：方法、语境摘要、复算脚本（断言 `len(ev)==148`、同值 0、525 对、EV 落入 0、CE 321/PROP 159）、**148 组全列分类表**（source→两侧 DI→指针→完整 64 字符哈希→分类）。
- POINTER §2/§11、REPORT §1.1、LEDGER（§0-4 item4、n=7 行、§3-9）同步区分表述。
- 525 对清单零改动（§8 维持原样）。

**复验**：§6a 内嵌脚本自 BASE 重跑通过，输出 `EV dual-entry=148 same-value=0; genuine pairs=525 (EV 0); CE same=321; PROP same=159`。

---

## ACC-F016 · 四列入口表恢复精确路径/回退根/阶段来源

**指令**：技能入口表恢复七条精确技能路径＋三候选回退根；Q1/P1 真名无 `-designer` 后缀；「模块可导入」改「静态存在」；P1/handoff 与 hld-completion 阶段来源分列（A2 对 hld-completion 零引用）。

**独立核验（BASE）**：`load_stage_runtime`（engine/loader.py L44–48）三候选按序 ①`ENGINE/rel` ②`ENGINE.parent/rel` ③`NOVEL/rel`；七条调用串带 `engine/` 前缀故候选①拼出 `engine/engine/…`（`git cat-file -e` 全部不存在），实际全部命中候选②`ENGINE.parent`＝仓库根；`-designer` 后缀的 reviewer/assembler 路径在三根均不存在；A2 `conception-completion.json` 仅含 `p1_manifest`（P1/package-manifest.json，sha256 bba81d35a089320074eb8677911707052ba99b1265fbf19731c78785a1eef8ce）与 `development_handoff`（P1/development-handoff.json，sha256 d48194db32a43575c96ff2df0c9bccf0f8d95a98f2b7bc7bc601068078c33957）两引用，对 hld-completion.json 零引用（其属 HLD V1 HF1 终结器契约产物）；四个测试构造器调用串命中③根 `duanxian/testing/…`（非①根，初稿笔误已当场更正）。

**改动**：REPORT §6 重写——撤回 v3 四项断言（designer 花括号路径／首根／可导入／统归 A2 manifest）；表格重建为 S1/W1/E1/T1/C1/Q1/P1 七行（精确路径＋调用串行号＋「L44–48 三候选按序：①（拼两次 engine，不存在）→②仓库根（命中）→③`NOVEL/…`」；Q1 `novel-conception-reviewer`、P1 `novel-conception-deliverable-assembler` 真名无后缀）＋harnesses 行（静态存在；导入与依赖闭包可执行性未证）＋3 机读文件行按阶段来源分列＋脚注（该型共 10 文件；designer 路径三根不存在；4 测试构造器命中③根）。同类表述仅 REPORT L124/L125/L128 存在（LEDGER/ISSUES/PROPOSAL 已核无同类）。

**复验**：`acc_f016_verify.sh`（git cat-file -e 逐路径存在性＋grep 调用串行号）通过；A2 JSON 引用清单重读确认仅两项。

---

## ACC-F017 · #20 主候选单一关闭目标＋分层登记

**指令**：主候选单一关闭目标（仅计数口径收敛）＋反例测试；K4/K6 载体＝独立非发布观察；附带项逐项处置对照冻结 #11/#12/#13 关闭条件；JSON 区分主候选/历史发布/独立观察/外部动作待授权。

**独立核验（BASE）**：正文 L191/L195 两次匹配（67%→82%，L363 明写第一次/第二次）vs L464「七次匹配」（同一推理链）；L379/L472 七个认知节点为另一计数对象。载体两组记录均真实在案（meeting-room L17/L20/L28–38＋§3.1–3.4 vs shenyu L82、zhengbozhou L191–199、正文 L302），采用基准未定。附带项证据：第比利斯时间 L157/L335/L375；K6 编号 L302；名片 L502；字符缺损归既有 REG-03。冻结 #11（十秒沉默来源标注）/#12（郑柏舟披露口径）/#13（记忆检索边界）关闭条件均不自动覆盖前三项。

**改动**：
- REPORT §8.1 #20 行 v4 重写（单目标＋反例测试通过＋载体独立观察＋四附带项处置）。
- ISSUES §2.7 `difference_reason` 重写（独立性仅由计数矛盾支撑，载体子集移出）；`publish_gate` 追加 v4 子句；新增五门状态表（6 行）；§5.2 #20 行 v4 重列；**追加 v4 JSON delta（schema 4.0-delta）**：`main_candidate`（单目标＋反例 PASS）、`independent_observations`（OBS-CARRIER-K4K6＋4 附带项逐项 disposition）、`historical_publish`（#20 published_open、线上未动、body_sha256 eea29d09a5e19aaa994ab967e7206b98658da590c514f8920b709470543b5a9f）、`external_actions`（OWNER_PENDING 未执行）、`retracted_v3_claims`（双目标单字段／笼统归并／载体并列独立性理由）。
- PROPOSAL header v4 批注＋#20 v4 批注＋汇总表 #20 行更新。

**复验**：反例测试「只解决计数是否满足主候选目标」＝是（计数修正无需决定 K4/K6 电话或会议室，也不需任何道具/披露决定）；ISSUES 自然语言与 JSON delta 一致性逐字段核对通过；nl/delta/proposal 三处口径一致。

---

## 交付物与版本

| 文件 | 版本 | 承载修正 |
|---|---|---|
| impl3-001-pointer-coverage-table.md | v4 | ACC-F015（§2/§6/§6a 新增/§11） |
| impl-001-report.md | v4 | ACC-F015（§1.1）＋ACC-F016（§6）＋ACC-F017（§8.1/§9/§10/§11） |
| impl-001-reading-ledger.md | v4 | ACC-F015 同步（header/§0-4/§3-9） |
| impl-001-issues.md | v4 | ACC-F017（header/§2.7/§5.2/v4 JSON delta） |
| impl2-001-external-correction-proposal.md | v4 批注 | ACC-F017（header/#20/汇总表） |
| impl4-001-correction-notes.md | 新建 | 本记录 |

机械验收自查（spec argv 原样执行）：ACC-F015/F016/F017/v4 四关键词在 impl-001-report.md 命中；`git diff --name-only 8924e22..HEAD` 全部落于 `outputs/duanxian-audit3/` 白名单 6 路径；秘密模式扫描零命中。
