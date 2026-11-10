# 仓库项目目标总结

> 审查基线：冻结提交 `839df007e36461b3d5f1dd78e33310aa79a3d2b6`。本文把“当前生产契约”“历史兼容资产”“目标设计但未完成实现”分开陈述；路径均为仓内相对路径。

## 1. 项目定位与核心目标

这是一个**小说创作工作流与 Agent 工程仓库**，不是单纯的小说正文库，也不是一个提示词集合。它要把人类作者的创意，经访谈、构思、宏观/详细设计、写作和评审，转化为可审校手稿；核心约束是每次生成都必须有明确输入、唯一职责、可消费产物、状态、版本和审查证据（`docs/ai-novel-workflow/README.md`）。

它主要解决四类问题：AI 擅自补全作者未决选择；下游静默改写上游故事事实；长链生成中版本混用、遗漏和无法追溯；把“文本生成了”误当成“创作验收完成”。因此，目标用户既包括需要作方向、价值和最终批准的作者/编辑，也包括实现技能、运行时和校验器的 Agent 工程开发者。其价值不是代替作者裁决，而是让机器做受控展开、作者保留批准权，并让任何场景都能回查设计依据（`docs/ai-novel-workflow/conception-phase.md`、`docs/ai-novel-workflow/development-phase.md`）。

《断线》是贯穿仓库的样例项目：早期材料讨论数字生命、记忆转移、四幕八锚点与人物双弧（`docs/plan-prd-research.md`、`docs/anchor-scenes-draft.md`），后续则成为契约和全链运行的真实案例。仓库最终目标应理解为“以《断线》验证一套可复用的小说生产系统”，而不是只完成这一部小说。

## 2. 整体流水线

### 2.1 当前主链：构思到 HLD，再到开发

1. **作者访谈与批准**：I0–I5 依次使用 `novel-intent-facilitator`、`novel-subject-designer`、`novel-world-interviewer`、`novel-character-interviewer`、`novel-causality-architect`、`novel-narrative-contract-designer`，形成意图卡、主体、世界契约、角色、因果故事线和叙述契约；`novel-interview-integrity-auditor` 与 `novel-interview-brief-generator` 完成 V1 审计和 V2 简报。`novel-interview-b0-migrator` 只处理旧批准链的兼容迁移。`harnesses/novel-conception-interview/` 持有顺序、逐轮证据、completion 和批准门，支持多运行时适配。
2. **自主构思 V2**：B0 冻结作者控制基线，随后 S1→W1→E1→T1→C1 分别由 `novel-storyline-architecture-designer`、`novel-world-model-designer`、`novel-environment-system-designer`、`novel-event-timeline-designer`、`novel-character-system-designer` 产出故事线、世界、环境、事件和角色 canonical JSON。Q1 `novel-conception-reviewer` 独立审查，P1 `novel-conception-deliverable-assembler` 无损封包。公共 schema 在 `docs/ai-novel-workflow/contracts/autonomous-v2/`。
3. **人审与开发准入**：H1 由 `novel-conception-human-review-assembler`、`novel-conception-fragment-writer`、`novel-conception-review-html-generator` 生成十分钟报告、非权威样片和离线 HTML；`novel-conception-presentation-fidelity-reviewer` 独立检查呈现忠实度。外部作者决定为 approved 后才生成 `conception-completion.json` 和 `development-handoff.json`（`harnesses/novel-conception-autonomous/docs/final-delivery-contract.md`）。构思 1.0.0 已冻结（`docs/ai-novel-workflow/release-notes-1.0.0.md`）。
4. **HLD 自主链**：`novel-development-baseline-preparer` 先把批准构思无损转成开发基线。HB0 `novel-hld-baseline-admitter` 准入，HA1/HS1/HC1/HI1/HR1/HK1 分别由 `novel-hld-narrative-architect`、`novel-hld-storyline-choreographer`、`novel-hld-character-arc-placer`、`novel-hld-information-architect`、`novel-hld-rhythm-continuity-architect`、`novel-hld-key-scene-function-planner` 完成结构、故事线、人物弧、信息、节奏连续性和关键场景功能。随后是 HQ1 `novel-hld-semantic-reviewer`、HP1 `novel-hld-package-assembler`、HQ2 `novel-hld-lld-readiness-evaluator`，HH1 的 `novel-hld-review-report-assembler`、`novel-hld-presentation-fidelity-reviewer`、`novel-hld-html-renderer`，最后由 HF1 `novel-hld-finalizer` 消费作者决定并授予 `lld_ready`（`docs/ai-novel-workflow/hld-autonomous-workflow-v1-design.md`）。
5. **LLD、写作与评审**：目标边界是 HLD 管“既有内容怎样组成小说”，LLD 管“场景具体如何发生”，Writing 产出正文。`docs/ai-novel-workflow/development-phase.md` 进一步定义 D0–D7：准入、场景计划、初稿、硬检查、语义重写、连续性、汇编和定稿。当前新 HLD 只交接到 `lld-handoff.json`；后续完整 LLD/checking/acceptance 生产链尚不能据此认定为已完成。

### 2.2 早期提案—PRD—HLD—LLD 资产与校验器

早期主链是 `idea → intake → proposal → PRD → HLD → LLD → writing → checking → acceptance`（`docs/superpowers/specs/2026-07-05-novel-creation-workflow-design.md`）。全部 81 个 `novel-*` 技能入口已按阶段核对，除上述当前链外，其余归类如下：

- **Intake/Proposal**：`novel-intake-workflow`、`novel-intake-boundary-ledger-builder`、`novel-reader-promise-designer`、`novel-core-concept-designer`、`novel-storyline-designer`、`novel-storyline-quality-evaluator`、`novel-final-promise-concept-consistency-checker`、`novel-macro-structure-designer`、`novel-core-character-framer`、`novel-world-premise-framer`、`novel-ending-direction-designer`、`novel-proposal-integrator`、`novel-proposal-risk-checker`、`novel-proposal-workflow`。
- **PRD**：`novel-prd-workflow`、`novel-part-scope-selector`、`novel-part-goal-definer`、`novel-trunk-scene-designer`、`novel-scene-conflict-value-designer`、`novel-scene-information-flow-designer`、`novel-prd-freeze-boundary-writer`、`novel-hld-expansion-requirement-writer`、`novel-prd-integrator`、`novel-prd-causality-checker`。
- **旧 HLD 十二产物链**：`novel-hld-workflow` 调度 `novel-world-entity-inventory-builder`、`novel-prd-support-matrix-builder`、`novel-world-rule-designer`、`novel-character-system-designer`、`novel-environment-system-designer`、`novel-event-system-designer`、`novel-time-information-system-designer`、`novel-thread-system-designer`、`novel-style-pov-system-designer`、`novel-hld-inventory-reconciler`、`novel-hld-integrator`、`novel-hld-integrity-checker`。其中角色/环境两个技能入口已被自主构思 V2 深化并跨链复用；`novel-hld-writer` 仅作历史说明。
- **LLD/写作**：`novel-thread-designer` 是早期线结构辅助；`novel-lld-writer`、`novel-character-designer`、`novel-space-designer`、`novel-scene-designer` 负责详细设计，`novel-character-writer`、`novel-space-writer`、`novel-scene-writer` 负责写作素材和场景正文。
- **退役/只读**：`novel-prd-writer` 不得生成新 PRD；`novel-development-map-designer` 只能诊断历史 D1 包，不得进入 V2。

根目录五个校验器分工明确：`validate_proposal_contract.py` 检查 proposal 契约、技能、DAG、声明追溯和 verdict 同步；`validate_prd_contract.py` 检查 PRD 九技能、场景事实、冻结边界、信息边界与 HLD 准入；`validate_hld_contract.py` 检查旧 HLD 十二产物、Source Map、风险收敛和 LLD 准入，并可校验指定产物目录；`validate_hld_release.py` 以 `--artifact-dir`、`--final-package`、`--upstream` 做只读发布预检；`validate_design_tasks.py` 检查 HLD 设计任务对 PRD 的覆盖。自主 V2 和新 HLD 不依赖这五个脚本代替自身门禁，而有各自 harness validators、schema 和运行时测试。

## 3. 顶层目录职责

| 目录 | 一句话职责 |
|---|---|
| `.git/` | 保存版本、分支和远端元数据，不是业务产物。 |
| `.kunora/` | 保存本次冻结 review 的 `spec.yaml`、`PROMPT.md` 等任务输入，不属于小说生产规范。 |
| `.superpowers/` | 保存 brainstorm 的 KUNORA HTML 设计稿和本地服务状态，与小说主链关系弱。 |
| `docs/` | 保存工作流权威规范、JSON Schema、历史设计、运行包、方法研究和旧正文。 |
| `harnesses/` | 实现访谈、构思自主 V2、新 HLD 三个编排核心及其运行时、校验和 eval。 |
| `projects/` | 保存《断线》项目元数据、生产 CLI 与作者批准的精简交付物。 |
| `skills/` | 保存 81 个按单一职责划分的 `novel-*` 技能及其脚本、契约和参考资料。 |
| `scripts/` | 保存 proposal/PRD/旧 HLD/发布/设计任务五个契约校验入口。 |
| `tasks/` | 保存 HLD 设计规划、TASK-001–005 fixtures 与验收任务状态。 |
| `testing/` | 保存自主 V2 schema runtime、E2E/单元回归和《断线》各阶段构建器。 |
| `tests/` | 保存五个根级校验器的契约测试。 |
| `outputs/` | 当前只有 KUNORA 登录、工作台等 SVG/PNG 视觉产物，不是小说 canonical 交付区。 |

## 4. 当前进展

`git log --oneline -40` 实际返回 20 个提交，主线清楚分为：2026-06 初始数字生命小说及写作资产；2026-07-05 intake/proposal/PRD/HLD 边界和 harness 重构；2026-07-17 `develop` 汇总；2026-08-17 完成《断线》批准构思；2026-08-19 连续完善新 HLD 的基线准入、章节设计、人审可读性与定义血缘。当前本地 `main` 与工作分支 `remote-agent/ai-novels-review-001` 均起于冻结提交；另有远端 `origin/dev/duanxian-conception-approved`，其 tip 与 main 不同，本报告不把它推断为当前主链。

完成度应分层判断：

- **构思已闭环**：`projects/duanxian/deliverables/conception-approved/README.md` 记录 run `duanxian-conception-v2-20260811-18` 于 2026-08-17 获作者批准，`development status=ready`；`author-decision.json` 与 `conception-completion.json` 给出对应绑定。
- **旧链已有业务稿但未全放行**：2026-07-07 PRD manifest 已确认人类评审并允许 HLD；2026-07-13 旧 HLD v3.0 的 01–12 产物已生成，但 manifest 仍为 `pending_hld_human_review`，不能直接称为 LLD-ready。
- **新 HLD 尚未发布**：`harnesses/novel-hld-autonomous/manifest.yaml` 为 `0.1.0 / implementation-candidate`，仅支持 Codex，`agentic_qualification: not-run`。`harnesses/novel-hld-autonomous/docs/release-checklist.md` 明确结构项已完成，而 42 个 bounded-skill Fresh Agent 案例、五个全链案例、《断线》完整 HLD 人审和作者决定仍未完成。
- **测试资产广但不能代替发布验收**：静态检索 `tests/` 五个测试文件有 352 个 test 函数定义，覆盖五个校验器正负例；`testing/` 八个测试文件有 303 个，覆盖 V2 schema、拓扑、运行时、E2E、C1、旧 D1 和新 HLD 技能包标准。`testing/run_duanxian_conception_v2.py` 是长链驱动，`duanxian_{w1,e1,t1,c1}_*` 等构建器提供故事语义，`duanxian_q1_*` 与 `duanxian_h1_*` 提供隔离审查和人审载荷；这些测试构建器不是生产调度器。

## 5. 关键设计决策

1. **内容权威与呈现分离**：canonical JSON 是下游内容输入，Markdown/HTML 只供阅读；P1/H1、HP1/HH1 必须绑定同一结论层，样片不得升级为设定权威。
2. **Schema 与语义双层验收**：JSON Schema 管封闭结构，确定性 validator 另管哈希、集合相等、跨文件引用、拓扑、包 profile 和 owner。`testing/autonomous_v2_schema_runtime.py` 只执行回归所需 Draft 2020-12 子集，遇到不支持关键字会失败；契约索引明确要求生产使用完整 Draft 2020-12 validator，不能把该测试 runtime 当成完整生产验证器。
3. **唯一 owner 与定向回退**：每个字段只有一个生产者，发现问题返回最早责任阶段并失效下游，而不是由 integrator、harness 或 reviewer 偷修。稳定 ID、路径和 SHA-256 共同绑定对象，集合必须精确相等，不能用数量或总分掩盖缺口。
4. **持久化自主工作流**：`harnesses/novel-conception-autonomous/runtime/production_orchestrator.py` 只管理顺序和事务，不创作内容；它签发唯一 work order，维护 append-only run-state、commit-intent 和 H1 workspace，支持崩溃恢复且拒绝覆盖 partial/stale/tampered 包。Q1 的 semantic/handoff、HQ2 的 consumer/fidelity、H1/HH1 的呈现审查均要求任务隔离。
5. **人类批准是外部硬门**：`approved / revise / rejected` 必须绑定当前机器包、报告和 HTML；聊天中的“看起来可以”不能生成 completion。机器检查与文学语义评审互补，作者仍裁决主题、重大变更和发布。
6. **测试形态分层**：`tests/` 偏根级契约同步与负例，`testing/` 偏运行时和全链，harness `evals/` 另有密封 fixture、P/N/B/R 场景和独立语义评分；声明式 fixture 不等于 Fresh Agent 执行证据（`harnesses/novel-hld-autonomous/docs/evaluation-contract.md`）。

## 6. 风险与注意事项

- **多套权威并存是最大使用风险**：旧 proposal/PRD/HLD、构思 V2、新 HLD 不能随意拼接。必须以各文件的权威迁移声明为准；退役 skill、D1/R1、旧 Markdown/HTML 和聊天记录不能冒充当前输入。同名角色/环境技能跨链复用时，也要按实际 work order 判断阶段。
- **不要把历史状态当成当前状态**：早期 proposal manifest 曾等待确认，后续 PRD 已有确认副本；旧 LLD blocked manifest 已被标为误解任务的错误记录。阅读状态必须结合日期、manifest 和最终 completion，而不能只挑一个文件。
- **新 HLD 与后续链路仍有明确未完成项**：新 HLD 的 Fresh Agent eval 和真实《断线》全链未验收；新 LLD 应以 `lld-handoff.json` 重新设计。旧正文和 `novel-scene-writer` 的存在，不证明当前 V2→HLD→LLD→写作→验收已端到端贯通。
- **可移植性有硬编码点**：`scripts/validate_design_tasks.py` 含 `/Users/royzuo/...` schema 路径，`testing/duanxian_h1_html.py` 含 Windows extended-length 路径，`tasks/design/design-planning.json` 也记录本机路径。新 HLD 当前只支持 Codex，其他 runtime 需独立 adapter/eval。
- **基线契约回归并非全绿**：本次 `python3 -m pytest tests -q` 因当前环境缺少 `jsonschema` 在收集 `test_validate_design_tasks.py` 时中止；排除该文件后为 307 passed、10 failed。十个失败均在 `test_validate_hld_contract.py`，指向 `novel-character-system-designer` 与 `novel-environment-system-designer` 已改成 V2 中文契约，旧 HLD 校验仍要求 `## Responsibility`、`## Output Artifact` 等旧英文结构。这实证了跨链复用同名技能的契约漂移风险；本任务未修改这些既有文件。
- **复杂度与维护成本较高**：生产 orchestrator、HLD validator、E2E 文件体量很大，E1/T1 2.4 又要求精确实现身份和契约升级。修改 schema、runtime、renderer 或 skill 都可能使旧 completion 失效，不能只改版本字符串或复用旧包。
- **机器门禁不等于文学质量保证**：大量结构测试能防漂移、漏引用和越权，却不能单独证明故事好看；仍须独立语义 reviewer 与作者评审。另因 `outputs/`、`.superpowers/` 含非小说视觉资产，且仓库没有根 README，Owner 应把 `docs/ai-novel-workflow/README.md` 作为业务入口，避免误判目录用途。
