# 《断线》构思与设计适配包 · duanxian-upg-impl-001

## 这是什么

- 三步协议第二步（实施）的交付：在作者 2026-08-17 批准的构思基准上，对人物、能力、因果、信息、终局、场景与旧素材/正文适配的**版本化设计适配包**。
- 严格按《升级定义书》（`outputs/duanxian-upgrade/duanxian-upg-def-001-definition.md`，definition_commit=4ce28e8a）§5 步骤 0–10 执行产生。

## 这不是什么（先读）

1. **不是**正式 HLD/LLD 准入凭证，**不是** `lld-handoff.json`，**不是**任何 stage completion——正式 HLD 生产若获授权须从重验通过的 canonical 机器基线进入（#7 门未过，本包不冒充）。
2. **不是**重新批准构思；作者批准权不受本包影响（D01–D03 均 `owner_pending`，见 `11-owner-decisions.md`）。
3. **不是**正文：旧正文零改动；`10-text-adaptation-map.csv` 全部 `writing_status=PENDING_WRITING`。
4. **不宣称**任何 GitHub ISSUE 已关闭；不宣称「所有 ISSUE 已解决」。处置权在 Owner。

## 状态

| 面 | 状态 |
| --- | --- |
| 包状态 | candidate_for_independent_acceptance（候选，交第三步 duanxian-upg-acc-001 独立验收） |
| 设计层 | 16 文件齐备（本 README＋15）；自检见 `13-regression-results.md` |
| 正式 HLD 准入 | blocked_by_evidence_and_pending_gates（#7 机器本体取证；#5 替代记录已立但正式人审另议；#6 歧义保留；D01–D03 待签） |
| 正文 | 未授权（PENDING_WRITING） |
| 工程（#1/#2/#4/#6） | DEFERRED_ENGINEERING（另行授权处置） |

## 唯一消费入口与阅读顺序

**下游只从本包消费设计，不得到旧目录自行拼材料**（旧 run `pass/canonical/covered` 字样一律不得引用）：

1. `README.md`（本文件）→ 2. `00-baseline-and-authority.json`（基线/权威/缺口）→ 3. `01-control-register.json`（批准控制原子登记）→ 4. `02-legacy-disposition.md`＋`03-source-migration.csv`（旧资产唯一入口）→ 5. `11-owner-decisions.md`（条件分支）→ 6. `04`/`05`（人物/能力证据）→ 7. `06`/`07`（因果/信息）→ 8. `08`（终局/POV）→ 9. `09`/`10`（场景/逐段适配）→ 10. `12-traceability-and-handoff.json`（追踪与交接）→ 11. `13-regression-results.md`＋`manifest.json`（验证锚）。

## 当前批准引用（Authority）

- `duanxian/novel-goals.md`（sha256 5ebbce4f…f297）＋`duanxian/conception-approved/`（author-decision.json=4f5a070d…；conception-completion.json=4eabd4af…；human-review-report.json=f3d848f1…）：作者 2026-08-17 批准，scope=conception，run=duanxian-conception-v2-20260811-18，status=ready。逐项 hash 与机器包受控引用见 `00`。

## 历史禁用说明（摘）

- 七月 HLD run（含 canonical-world-facts-v3.0）＝历史证据，仅经 `02` 处置表进入；其 `pending_hld_human_review`/`blocked_revision_required`/P1-open 状态原样有效（`02` §C/D）。
- 六月 PRD/LLD/写作素材/正文＝历史链；17 个旧路径引用与 5 个旧章节指称的映射见 `03`（路径可达≠内容获准复用）。
- 周岚参与链（维护例外/周启明/纬线链/D+58）pending D01，A 候选下整体退出；郑柏舟支线 pending D02，A 候选下退出且**禁止**换名为罗景明；完整记忆/像素重建/自行关停/会议室十秒依赖＝已撤出新版设计（详见 `02`/`10`）。

## 验证锚

- 文件级：`manifest.json`（逐文件 bytes/sha256，对实际 UTF-8 字节实算；manifest 自身不自哈希）。
- 内容级：`13-regression-results.md`（REG-01..13 双列＋NEG 七例＋22 行迁移表＋消费演练；实施者自检，第三步独立重做）。

## 版本

- v1.0（首次实施候选；LOOP 预算=首次＋最多两次定向修订）。修订即递增包版本并使旧 manifest/回归结果失效。
