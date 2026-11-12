# 《断线》审视任务：工作项B定义书

作业：`duanxian-audit-rdef-001`。本文定义如何审视实现一致性与实现程度，不代写实施报告，不提交 ISSUE。内容证据固定为 `main@92573f1cca40f37cee04d2beb8708ff33ba603d6`（下称 BASE），不随远端 main 移动更新。执行边界来自本作业 `.kunora/spec.yaml`、`.kunora/PROMPT.md` 与 Owner 启动要求。

目标口径沿用已获 Owner 确认的两份输入：

| 输入 | 不可变版本与路径 | 本次核验 |
| --- | --- | --- |
| 工作项A定义书 | `99e18a0d2f3c8d4d8f069a3150622f8f68a55912:outputs/duanxian-audit/gdef-001-def.md` | 只读 fetch 指定提交，核对完整 commit SHA，读取全文。 |
| 目标总结候选 | `a6935ddcdf6716cf96bfdc6804e0cde29471bb5c:outputs/duanxian-audit/goals-summary.md`；来源分支 `remote-agent/duanxian-audit-gimpl-001` | 只读 fetch 指定提交，核对完整 commit SHA；原始文件 SHA-256 为 `ac7f045a92af07c23b0b7a15a59421de25756f60883d4a3c9adc75b47e90155e`，与冻结值一致。 |

以上文件是任务定义及目标理解基准，不是新增故事事实来源。故事与实现断言仍须回到 BASE 的原始文件。`duanxian/novel-goals.md` 文首的 `9baefb33cb999f1e92f318fe6ac22f0d1fe4d752` 是该文材料整理基线，不是本次审视的新内容基线。

## 一、工作项B六要素

| 要素 | 定义 | 可核查的完成条件 |
| --- | --- | --- |
| 目标 | 完整、仔细阅读冻结 main 的文档与代码，判断其与项目目标的一致性及实现程度，形成真实、自洽的报告。 | 六问逐项回答“目标是什么、实现证据是什么、差距是什么、能判断到哪一步”；小说项目状态与引擎能力分别说明。 |
| 工作方法 | 固定版本→建立全量文件清单→按权威层次全文阅读→沿规范、实现、测试和实际留存产物追证→分级→复核反证。 | 阅读覆盖可核对；每项结论有具体路径及行/字段；不以目录存在、关键字命中或测试名称替代内容阅读。 |
| 边界 | 对 BASE 仓库内容只读；B-实施唯一新增审视报告；B-验收独立复核；C 才负责 ISSUE 整理提交。 | 不修源码、旧文档、依赖或配置，不续写小说、不代作者批准，不运行生成流水线，不在 B 创建 ISSUE。 |
| 约束 | 固定来源、Owner 模型分工、五种口径、证据强度、字数和唯一交付路径；保留全部不可变约束原文。 | 无未经授权的事实、来源、模型替换或执行扩权；缺证与冲突如实披露。 |
| 交付物 | B-定义交付本文；B-实施交付 `outputs/duanxian-audit/implementation-review-report.md`；B-验收通过编排渠道交结论和修正指令。 | 报告 UTF-8 中文，6000–12000 中文字，含固定章节、ISSUE 候选清单；候选文件与提交/哈希绑定，唯一新增文件。 |
| 验收标准与方法 | 机械、覆盖、结构、证据、口径、一致性、越界七类门全部通过。 | 按第六节逐项 PASS，不能用篇幅、总分或实施自评抵销硬门；独立验收失败返回实施追加修正提交。 |

### 1.1 Owner 冻结的不可变约束（原文）

- 实施作业交付物唯一路径＝`outputs/duanxian-audit/implementation-review-report.md`，唯一新增文件。
- 报告必须以 main@92573f1cca40f37cee04d2beb8708ff33ba603d6 冻结内容为唯一依据；实现程度结论必须附路径级证据。
- 报告 6000–12000 中文字；中文、真实自洽、五种口径标注（【当前权威口径】【历史/旧链口径】【未完成项】【流程规范】【推断】）沿用目标文档体系。
- 实施与验收作业的执行器/模型分配＝Owner 冻结（实施→kimi-code/k3.1-pro；验收→codex/gpt-6-astra high）。
- 审视任务全程不得修改仓库既有文件；B 报告不代替工作项C 的 ISSUE（ISSUE 由 C 实施作业提交）。
- 报告须包含明确的「ISSUE 候选清单」节：列出值得立 ISSUE 的不一致/缺口（每条含问题、证据路径、建议方向），供 C-定义作业消费；但不预造 ISSUE。

### 1.2 权威与执行权限

执行权限由各作业自己的冻结契约决定，小说流程中的“自主”不授权审视 Agent 修改源码或代填批准。内容依据分四层：流程总则及适用契约说明应然要求；目标文档和已确认 A 总结说明目标口径；批准构思留存证据说明目前能证明的故事与状态；历史稿说明演变与旧链。遇到不同层内容不一致，先判定适用阶段和版本，不能以文件日期、`pass` 字样或自己的偏好取代权威判断。

`engine/harnesses/novel-conception-autonomous/docs/final-delivery-contract.md` 第 2–3 节规定 P1 为最终机器内容权威，H1 是忠实呈现。可以从留存批准报告理解故事，不能因 P1 未入库就把 Markdown 提升为机器入口；也不能据缺失运行文件宣布既有作者批准无效。未取得正式链时，写“冻结 Git 留存不足以复验该条件”。

本定义作业不安装依赖、不执行仓库测试或构建，只做只读盘点、内容核对和文稿自检；未产生新的流水线实测结论。后续实施及验收默认同样采用静态只读审视；若自身契约另行明确授权测试，须按 5.5 的隔离与记录规则执行，不能从本定义书获得额外许可。ACK、初始化报告属于编排控制证据，不进入业务提交。

## 二、审视对象文档地图

### 2.1 冻结树总量、范围与复现

清单由 BASE 的 `git ls-tree -rz --name-only` 取得，按 NUL 分隔以正确处理中文路径。共 1444 个跟踪文件：`duanxian/` 148、`engine/` 1290，其余 6。文件数是目录盘点，不是已读证明或测试通过数。

其余 6 个文件为 `README.md`、`.gitattributes`、`.gitignore`、`.serena/.gitignore`、`.serena/project.yml`、`.zcode/plans/plan-sess_316609e2-5263-4909-a27a-c47b17476339.md`。它们用于解释仓库入口、忽略范围和工程历史；工具配置不能取得故事权威。`engine/` 的 1290 个文件包括顶层 README、docs 83、skills 669、harnesses 404、scripts 5、tests 6、testing 10、tasks 112。

只读清单复现命令：

```bash
git ls-tree -rz --name-only 92573f1cca40f37cee04d2beb8708ff33ba603d6
# 阅读单个文件时使用下面形式，路径从清单取得：
# git show 92573f1cca40f37cee04d2beb8708ff33ba603d6:<仓库相对路径>
```

报告须记录每层文件总数、全文已读数、非文本/重复投影数、未读数及原因。文档和源码的全量阅读是 B 的工作要求；后文“抽样”是对全文阅读之后的取证、交叉核对与验收，不允许用少数样本代表“已完整读仓库”。多行长文分段读到末尾；单行大 JSON 按字段展开，覆盖全部独有语义字段；同源重复投影可记录同源关系与差异核对。压缩包等二进制只读目录、manifest 和内容哈希，必要时在内存中读取文本成员，不运行、不解包覆盖工作树。未读项影响结论时不得宣称完整完成。

### 2.2 分层地图与必查证据

| 层次 | 精确入口与目录范围 | 在审视中的作用与重点取证规则 |
| --- | --- | --- |
| 目标 | `duanxian/novel-goals.md`；`README.md`；`duanxian/README.md` | 全读六章与 S01–S23，逐问建立目标→产物→结论映射。逐条回查权威原文，不能只转述 A 总结。 |
| 批准构思 | `duanxian/conception-approved/`，6 个文件：README、author-decision.json、conception-completion.json、human-review-report.md/.json/.html | 全读批准记录及故事正文；检查 JSON 的 run、completion 引用、source_coverage、reduction_ledger、decision_controls 等，核对 HTML/Markdown 投影。故事高风险边界全查，不能从“三个试读场景”增加设定。 |
| 宪法/流程 | `engine/docs/ai-novel-workflow/README.md`；同目录 `conception-autonomous-workflow-v2.md`、`hld-autonomous-workflow-v1-design.md`、`hld-skill-contract-catalog-v1.md`、`development-phase.md`；`engine/harnesses/novel-conception-autonomous/docs/final-delivery-contract.md` | 建立构思、正式开发基线、HLD、LLD、写作、作者门及变更回退关系。规范是否存在与实现是否满足分别判断。源码字段冲突须回查 catalog/schema，不从自然语言猜字段等价。 |
| 其他工程规范 | `engine/docs/ai-novel-workflow/contracts/autonomous-v2/`、`engine/docs/design/`、`engine/docs/superpowers/`、`engine/docs/plan-prd-research.md` | 识别当前契约真源、设计稿、发布说明与历史计划；全文读独有文本与 schema，追踪规范到实现、测试及发行状态。仓库内参考文献只作为留存引文，不访问外部资料。 |
| 旧 SPEC | `duanxian/design/specs/` 共 36：根层 10，`lld/characters/` 7、`lld/scenes/` 10、`lld/spaces/` 9 | 根层为六月 digital-life 八篇及七月 intake/proposal 两篇；读版本与批准边界，逐个核对会进入当前结论的事实。旧 K1–K10、四段式和人物名单不自动迁移为新版结构。 |
| 旧运行链 | `duanxian/design/runs/` 共 49：`proposal/` 15、`prd/` 13、`hld/` 20、`lld/` 1 | 全读 manifest/gate、风险报告及产物；按运行 ID 分组，不混成一条新版批准链。HLD 20 包含两个七月运行目录，不能全部说成 7 月 13 日单轮。 |
| 构思过程与任务 | `duanxian/design/workflow-docs/` 11；`duanxian/design/design-tasks/` 2；`duanxian/design/reference/` 1 | 对照意图、叙述契约、发展图、覆盖矩阵及任务状态；过程 HTML 的版本可能与 Markdown 不同。风格参考只能说明历史意图，不能新增模仿要求。 |
| 写作产物 | `duanxian/writing/` 17（characters 7、scenes 1、spaces 9）；`duanxian/novel-text/2026-06-07-duanxian-novel.md`；`duanxian/design-scenes-draft.md` | 全读正文和素材；重点取证启动/记忆、关系形成、现实阻断、告别与尾声。不存在某段则记录缺失，不补故事；将草稿偏差与当前正式产物违约区分。 |
| 项目代码 | `duanxian/conception-production/run.py` 与同目录 `tests/` 3；`duanxian/testing/` 17；`duanxian/project-display-metadata.json` | 核对入口、stage 拓扑、双根寻址、run/attempt 隔离、作者与评审身份、构建器的适用 run 和标题来源；测试存量另见 2.3。 |
| 引擎代码 | `engine/skills/`、`engine/harnesses/`、`engine/scripts/`、`engine/tests/`、`engine/testing/` | 以契约→入口→运行时→输出/门禁→负例测试追调用闭包；按 2.3–2.5 清单覆盖，不只统计脚本。 |
| 工程任务与发布资产 | `engine/tasks/design/` 22、`engine/tasks/development/` 90；各 harness 的 dist/releases/tools/adapters 等实际子树 | 判断是小说生产能力、开发任务样例还是分发工具；不把 greeting-cli fixtures 的完成状态当《断线》完成。发布包与当前源码分别标版本，二进制不作为未读源码的替代。 |

旧链的固定重点文件：

- `duanxian/design/specs/2026-07-05-duanxian-intake.md`、`duanxian/design/specs/2026-07-05-duanxian-proposal.md`：边界及旧人审门。
- `duanxian/design/runs/hld/2026-07-10-duanxian-hld-workflow/manifest.md`、同目录 `gate-report.md`；`duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/manifest.md`、同目录 `gate-report.md`：不得只取入口 pass 而漏掉人审未放行。
- `duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/artifacts/final-hld-package.md`、同运行 `canonical-world-facts-v2.0.md` 和 `canonical-world-facts-v3.0.md`：版本隔离与来源关系。
- `duanxian/design/runs/lld/2026-07-08-duanxian-lld-workflow-blocked/manifest.md`：开头已标 superseded，并说明曾误解详细设计任务；不能摘下文旧 blocked 表格冒充当前 LLD 裁定。
- `duanxian/design/workflow-docs/duanxian-intent-card.md`、`duanxian-narrative-contract.md`、`duanxian-development-map.md`、`duanxian-coverage-matrix.md`、`duanxian-map-check.md`（后四项均在同一 workflow-docs 目录）：查读者未定、C5/M01–M10 等旧编号及过程覆盖范围。

### 2.3 构建器、校验器及测试存量

以下均为 BASE 中真实存在的文件或目录；数量是以文件名 `test_*.py` 计的测试文件数，不是 pytest 用例数，不证明运行通过。

**项目 CLI 与测试**：`duanxian/conception-production/run.py`；`duanxian/conception-production/tests/test_attempt_selection_cli.py`、`test_line_sequence_review_cli.py`、`test_topology_review_cli.py`（后两项与第一项同目录）。重点读 attempt 选择、候选 SHA、独立评审、API 兼容及入口寻址。实例：run.py 第 14、41–54 行把 ROOT 与模块相对路径组合；测试第 12–13 行仍组合 `projects/duanxian`。B 必须逐段核对这些表达式在冻结布局下解析到何处，报告静态观察和影响条件；本定义没有运行 CLI 或据此宣称测试已失败。

**项目 testing 的完整 17 文件清单**（每项前缀均为 `duanxian/testing/`）：

| 分组 | 文件 |
| --- | --- |
| run08 构建 | `build_run08_hi1_000230.py`、`build_run08_hi1_000237.py`、`build_run08_hi1_000238.py` |
| 世界/环境/事件/角色 | `duanxian_w1_model.py`、`duanxian_e1_builder.py`、`duanxian_t1_builder.py`、`duanxian_c1_builder.py` |
| Q1 | `duanxian_q1_semantic.py`、`duanxian_q1_handoff.py` |
| H1 | `duanxian_h1_plan.py`、`duanxian_h1_fragments.py`、`duanxian_h1_assemble.py`、`duanxian_h1_html.py` |
| 驱动与编辑呈现 | `run_duanxian_conception_v2.py`、`generate_duanxian_editorial_review.py` |
| 测试 | `test_c1_determinism.py`、`test_duanxian_title_provenance.py` |

对每个构建器查输入来源、硬编码 run、相对路径、写入位置和使用者；从 W1→E1→T1→C1、Q1→P1→H1 各取一条可追溯调用链重点交叉核对。不能把只为旧 run 使用的构建脚本当作通用已发布生产入口，也不能因目录名 testing 就认为所有文件均可无副作用执行。

**五个顶层校验器与对应测试**：

| 校验器 | 对应测试 |
| --- | --- |
| `engine/scripts/validate_proposal_contract.py` | `engine/tests/test_validate_proposal_contract.py` |
| `engine/scripts/validate_prd_contract.py` | `engine/tests/test_validate_prd_contract.py` |
| `engine/scripts/validate_hld_contract.py` | `engine/tests/test_validate_hld_contract.py` |
| `engine/scripts/validate_hld_release.py` | `engine/tests/test_validate_hld_release.py` |
| `engine/scripts/validate_design_tasks.py` | `engine/tests/test_validate_design_tasks.py` |

`engine/tests/conftest.py` 是支持文件。五组全部读并各选至少一正向、一拒绝路径，检查它验证的是结构、状态、内容还是批准；没有某种反例就记录未见覆盖，不编造测试名。

**运行时 testing**：`engine/testing/` 包含 `autonomous_v2_schema_runtime.py`、`conftest.py`，六个测试文件 `test_conception_autonomous_v2_contracts.py`、`test_conception_autonomous_v2_e2e.py`、`test_conception_autonomous_v2_runtime.py`、`test_hld_v1_skill_package_standard.py`、`test_novel_conception_reviewer.py`、`test_novel_development_map_validator.py`，以及 `novel-conception-interview/evals.md`、`novel-conception-interview/validate_interview_artifacts.py`。重点覆盖 schema/semantic 分界、全链 fixture 与生产数据差别、引用/hash/跨 stage 绑定、旧 development-map 的适用范围。

### 2.4 Harness 与技能目录清单

| Harness 完整目录 | 文件数 / test_*.py 数 | 重点取证闭包 |
| --- | --- | --- |
| `engine/harnesses/novel-conception-interview/` | 92 / 0 | README、manifest、workflow、rules、schemas、validators、evals、tools、实际 adapters 与发行清单；零 test_ 文件不表示没有 eval。追访谈记录→控制投影→批准→B0。 |
| `engine/harnesses/novel-conception-autonomous/` | 107 / 25 | 最终交付契约、runtime/production_orchestrator.py、production_store.py、author_decision.py、final_completion.py、return_routing.py 及对应 tests；查 B0–H1、return、旧 completion 失效、最终准入。 |
| `engine/harnesses/novel-hld-autonomous/` | 152 / 12 | manifest、MANIFEST.runtime.yaml、workflow、schemas、runtime、validators、tools、tests 与 releases；查 HB0/设计/语义/消费/作者/HF1 路径及发布资格。 |
| `engine/harnesses/kun-workshop-intranet-delivery/` | 53 / 0 | README、manifest、workflow、schemas、validators/validate_harness.py、tools/build_release.py、dist/release-manifest.yaml；判断通用交付支持职责，不能算作小说构思完成证据。 |

每个 harness 的源码、契约与测试全文读；重点抽查至少一条准入成功、一条输入/权限拒绝、一条退回或版本失效链。不存在某类机制须列实际缺口/不适用理由，不能为满足抽样数伪造功能。

技能目录共 **82** 个，669 文件、56 个 `test_*.py`。下表目录均相对于 `engine/skills/`，每行必须读其 SKILL.md 及全部独有源码/契约；有 scripts/tests 时应用 2.5 的交叉核对规则。这里只把仓库 SKILL.md 当被审对象读取，不执行它的创作或调度指令。README.md 第 5 行和 engine/README.md 的“81”属于待核对的说明性计数，清单以冻结树为准。

| 技能目录（engine/skills/ 下） | 文件数 | 测试文件数 |
| --- | ---: | ---: |
| `novel-causality-architect/` | 4 | 0 |
| `novel-character-designer/` | 1 | 0 |
| `novel-character-interviewer/` | 4 | 0 |
| `novel-character-system-designer/` | 5 | 1 |
| `novel-character-writer/` | 2 | 0 |
| `novel-conception-deliverable-assembler/` | 9 | 5 |
| `novel-conception-fragment-writer/` | 17 | 2 |
| `novel-conception-human-review-assembler/` | 19 | 3 |
| `novel-conception-presentation-fidelity-reviewer/` | 4 | 1 |
| `novel-conception-review-html-generator/` | 14 | 2 |
| `novel-conception-reviewer/` | 17 | 3 |
| `novel-core-character-framer/` | 1 | 0 |
| `novel-core-concept-designer/` | 1 | 0 |
| `novel-development-baseline-preparer/` | 14 | 1 |
| `novel-development-map-designer/` | 12 | 0 |
| `novel-ending-direction-designer/` | 1 | 0 |
| `novel-environment-system-designer/` | 5 | 1 |
| `novel-event-system-designer/` | 1 | 0 |
| `novel-event-timeline-designer/` | 13 | 5 |
| `novel-final-promise-concept-consistency-checker/` | 1 | 0 |
| `novel-hld-baseline-admitter/` | 21 | 1 |
| `novel-hld-chapter-definition-designer/` | 12 | 3 |
| `novel-hld-character-arc-placer/` | 25 | 3 |
| `novel-hld-expansion-requirement-writer/` | 1 | 0 |
| `novel-hld-finalizer/` | 30 | 1 |
| `novel-hld-html-renderer/` | 33 | 2 |
| `novel-hld-information-architect/` | 29 | 3 |
| `novel-hld-integrator/` | 1 | 0 |
| `novel-hld-integrity-checker/` | 1 | 0 |
| `novel-hld-inventory-reconciler/` | 1 | 0 |
| `novel-hld-key-scene-function-planner/` | 28 | 2 |
| `novel-hld-lld-readiness-evaluator/` | 31 | 2 |
| `novel-hld-narrative-architect/` | 24 | 2 |
| `novel-hld-package-assembler/` | 32 | 1 |
| `novel-hld-presentation-fidelity-reviewer/` | 30 | 1 |
| `novel-hld-review-report-assembler/` | 34 | 1 |
| `novel-hld-rhythm-continuity-architect/` | 28 | 2 |
| `novel-hld-semantic-reviewer/` | 27 | 2 |
| `novel-hld-storyline-choreographer/` | 25 | 3 |
| `novel-hld-workflow/` | 1 | 0 |
| `novel-hld-writer/` | 10 | 0 |
| `novel-intake-boundary-ledger-builder/` | 1 | 0 |
| `novel-intake-workflow/` | 1 | 0 |
| `novel-intent-facilitator/` | 4 | 0 |
| `novel-interview-b0-migrator/` | 13 | 1 |
| `novel-interview-brief-generator/` | 4 | 0 |
| `novel-interview-integrity-auditor/` | 3 | 0 |
| `novel-lld-writer/` | 10 | 0 |
| `novel-macro-structure-designer/` | 1 | 0 |
| `novel-narrative-contract-designer/` | 4 | 0 |
| `novel-part-goal-definer/` | 1 | 0 |
| `novel-part-scope-selector/` | 1 | 0 |
| `novel-prd-causality-checker/` | 1 | 0 |
| `novel-prd-freeze-boundary-writer/` | 1 | 0 |
| `novel-prd-integrator/` | 1 | 0 |
| `novel-prd-support-matrix-builder/` | 1 | 0 |
| `novel-prd-workflow/` | 1 | 0 |
| `novel-prd-writer/` | 12 | 0 |
| `novel-proposal-integrator/` | 1 | 0 |
| `novel-proposal-risk-checker/` | 1 | 0 |
| `novel-proposal-workflow/` | 1 | 0 |
| `novel-reader-promise-designer/` | 1 | 0 |
| `novel-scene-conflict-value-designer/` | 1 | 0 |
| `novel-scene-designer/` | 1 | 0 |
| `novel-scene-information-flow-designer/` | 1 | 0 |
| `novel-scene-writer/` | 2 | 0 |
| `novel-space-designer/` | 1 | 0 |
| `novel-space-writer/` | 2 | 0 |
| `novel-storyline-architecture-designer/` | 5 | 1 |
| `novel-storyline-designer/` | 1 | 0 |
| `novel-storyline-quality-evaluator/` | 1 | 0 |
| `novel-style-pov-system-designer/` | 1 | 0 |
| `novel-subject-designer/` | 4 | 0 |
| `novel-thread-designer/` | 1 | 0 |
| `novel-thread-system-designer/` | 1 | 0 |
| `novel-time-information-system-designer/` | 1 | 0 |
| `novel-trunk-scene-designer/` | 1 | 0 |
| `novel-world-entity-inventory-builder/` | 1 | 0 |
| `novel-world-interviewer/` | 4 | 0 |
| `novel-world-model-designer/` | 5 | 1 |
| `novel-world-premise-framer/` | 1 | 0 |
| `novel-world-rule-designer/` | 1 | 0 |

### 2.5 抽样规则与扩查条件

1. **批准链全查**：两份批准 JSON 的全部引用、九个 stage completion 引用、P1/handoff/HTML/author/run 绑定逐项分类为“文件留存且可核算”“仅有路径/hash 引用”“当前树未定位”。重算 author-decision 与 HTML 对应 hash；不因两项通过推导全链通过。本次已核实这两项留存绑定；三个机器文件名 `novel-conception-package.json`、`development-handoff.json`、`hld-completion.json` 在 BASE 跟踪树中匹配为零。只说明 Git 留存范围，不能推断磁盘、其他提交或现实世界不存在。
2. **故事高风险全查**：主体/记忆、当前感官、权限与现实行动、亲属同意、信息分层、关停/备份、开放边界七类全部覆盖；取批准报告非样片正文作为对照。写作素材全文读后，每类至少定位一处具体证据或明确无对应段落。正文开端、中段、结尾均取证；额外纳入所有发现的直接冲突。
3. **旧链逐运行查门**：proposal、PRD、两个 HLD、LLD 的 manifest/gate/风险结论全部核对，不能只取最新版目录；保留 superseded 与人审 pending 的上下文。对正文或报告引用的旧事实继续追至源文件。
4. **代码按职责取证**：全部源码读完后，每个有实现的技能以输入检查→核心处理→产物/状态→拒绝分支选至少一条闭包；有测试时选择与该闭包对应的一正一负用例，只有一种则注明。纯提示技能检查输入输出、职责、失败去向及引用是否闭合，不把无 Python 文件判为未实现。
5. **跨层重点链**：CLI/STAGE_SPECS→stage runtime→schema；Q1→P1→H1→作者决定→final completion；development-baseline→HB0→HLD 设计→HQ1/HQ2→HF1；旧 proposal/PRD/HLD 校验器→测试 fixture→项目旧产物。各链至少给一个跨文件证据组合，避免孤立读函数。
6. **运行资格查三件套**：HLD 的 `engine/harnesses/novel-hld-autonomous/manifest.yaml`、`releases/0.1.0-acceptance.json`、`releases/0.1.0.md` 与 dist 清单对照。发布记录明确 implementation-candidate、五个 E2E fixture declaration-only、42 个 bounded cases 未经 fresh Agents 执行，不得升级为语义发布通过；也不能把这些历史声明冒充本次新测结果。
7. **扩查**：一处矛盾即检查同 run/同模块及所有直接上下游引用；两处同型问题扩查该目录全部同型路径；涉及作者权威、状态/hash、越权或最终结论的，查完整依赖闭包。每项记录样本为何选、扩查到哪、仍不确定什么。已全文阅读不等于每条结论都经过同等深度验证。

## 三、总体方案

本方案沿用 A 的“定义→实施→独立验收→编排交接”，是审视作业编排，不调度小说生成技能。

| 步骤 | 作业、执行器/模型 | 环境与输入 | 产出与交接门 |
| --- | --- | --- | --- |
| B-定义 | `duanxian-audit-rdef-001`；codex/gpt-6-astra high | 本作业独占 worktree；BASE、冻结契约、已确认 A 两份输入 | 本定义书；按冻结机械检查、自主内容复核、编排验收与 Owner 审查处理，不自称已获独立验收。 |
| B-实施 | `duanxian-audit-rint-001`；kimi-code/k3.1-pro | 编排方准备独立工作目录及实施分支；BASE、获准定义书完整 SHA、两份 A 输入及其哈希 | 唯一审视报告，自检后提交推送；交候选完整 SHA、文件 SHA-256、覆盖/检查结果与未决项。 |
| B-独立验收 | `duanxian-audit-racc-001`；codex/gpt-6-astra high | 独立上下文/作业，读取同一 BASE、定义书、A 基准和实施候选 | 第六节逐项 PASS/FAIL；无法封定输入则 BLOCKED。FAIL 回实施，PASS 后由编排方交 C-定义。 |

A 定义书中的 agent-linux-01/03 是 A 的环境分配，不能据此宣称本轮 B 的实际主机。B 的具体机器、工作区、分支和凭据路径由各自冻结 spec 确定；模型分工保持本节冻结值，不能以默认模型替代。实施者不得自行派生“验收 Agent”充当 B 独立验收作业。

交接包是编排信息，不新增仓库文件：job_ref、BASE 完整 SHA、定义书完整 SHA/文件哈希、A 两份输入版本、实施分支及完整候选 SHA、唯一报告路径/哈希、检查退出码、阅读覆盖、未决项与失败定位。取回用完整 SHA，不只跟踪会移动的分支。B 报告对 C 提供问题候选及证据；C 仍须按自己的定义处理归并、查重、权限和提交，不把候选编号伪装成已创建的 GitHub ISSUE。

## 四、任务路线图

### 4.1 剩余作业与编号口径

本次 Owner 提示使用“九作业序列”称呼，同时指定本作业为第 5 个、后续到第 10 个；A 旧定义书曾将 B-定义排为第 4。本文保留本次冻结编号并显式记录差异，不虚构一个已完成的第 4 作业、不改写 A 历史、不将编号差异当故事目标冲突。依赖顺序无歧义，若编排系统需要连续编号，由编排方/Owner 另行确认映射，不妨碍按当前 job_ref 编写交付物。

| 本次冻结编号 | 作业 | 结果与下一门 |
| --- | --- | --- |
| 已完成 A 三步 | A-定义、实施、验收；目标总结已获 Owner 确认 | 固定目标口径，供 B 使用；不重开 A 业务。 |
| 5 | B-定义 / rdef-001 | 本定义书通过本作业验收后，编排方封定版本交实施。 |
| 6 | B-实施 / rint-001 | 唯一报告及 ISSUE 候选；完成自检、提交、推送，进入独立验收。 |
| 7 | B-验收 / racc-001 | PASS 进入 C；FAIL 回 6；关键输入缺失则记录 BLOCKED。 |
| 8 | C-定义 | 以获验 B 报告定义 ISSUE 粒度、归并、查重、证据、提交权限和验收，不在 B 提前拟定 C 的冻结模型/路径。 |
| 9 | C-实施 | 按 C 契约提交 GitHub ISSUE，提交人是实施作业，凭据由编排方预置。 |
| 10 | C-验收 | 核对实际 ISSUE、内容证据与粒度；失败回 9，PASS 后编排收口。 |

### 4.2 B 内部路线与失败处置

| 步骤 | 动作与可见结果 | 失败去向 |
| --- | --- | --- |
| B0 准入 | 读取自身契约、按启动序确认及 ACK，核对分支、BASE 和干净来源。 | 输入不符报具体缺口，不 reset、不换基线、不改契约。 |
| B1 封定目标 | 只读取得 A 指定对象、核 SHA 和文件哈希，核对获准定义书。 | 网络/对象/hash 失败停止依赖断言，不改用最新分支。 |
| B2 全量阅读 | 冻结文件清单→按第五节读完→形成覆盖汇总和证据账。 | 未读不得宣称完整；按剩余文件继续阅读；无法取得关键证据记录限制。 |
| B3 跨层取证 | 批准链、历史链、写作、引擎与测试分别对照目标，检查反证。 | 冲突按 2.5 扩查；权威同层无法裁决则保留未决并交编排。 |
| B4 分级成稿 | 六问矩阵、五维审视、实现程度、ISSUE 候选与限制写入唯一报告。 | 错事实、缺证据或越级结论在报告内修正，不修源文件。 |
| B5 自检交付 | 机械门、引用门、口径门、范围门通过后提交推送，核对远端 SHA。 | 内容问题回 B4；推送失败保留本地提交并报告，不强推、不输出完成哨兵。 |
| B6 独立验收 | 验收者对封定候选执行第六节。 | FAIL 给逐条修正指令回 B4，新 SHA 重验；BLOCKED 等具体输入或裁决。 |
| B7 交 C | 编排方封定通过的报告/候选清单与未决项，交 C-定义。 | 新问题需改变 A 目标时回 Owner 目标确认门，不能在 C 静默改写目标。 |

## 五、实施作业工作指令

### 5.1 准入、版本与只读取证

1. 全文读实施作业自己的 spec/PROMPT、适用宪法和本定义书；按当轮要求先逐项确认、立即写 ACK，再开始工作。核对执行器/模型、唯一输出、网络/测试权限、工作分支及凭据使用方式。不得照搬本定义作业的分支和凭据。
2. 执行 `git --version`、`python3 --version`、`git status --short --untracked-files=all`、`git branch --show-current`、`git rev-parse HEAD`。首次实施 HEAD 应为 BASE；修正轮允许为已核验的实施候选后代，但源码树必须仍等于 BASE。只读检查 `git diff BASE -- README.md duanxian engine` 时，用本文完整 BASE SHA 替换符号；另按第六节检查全仓范围，不能漏掉隐藏配置。发现已有他人变更停止覆盖，交编排处理。
3. 使用下列命令只读 fetch 两个指定对象，不 checkout、不 merge。逐条成功后继续：

```bash
git fetch --no-tags origin 99e18a0d2f3c8d4d8f069a3150622f8f68a55912 a6935ddcdf6716cf96bfdc6804e0cde29471bb5c
git rev-parse --verify '99e18a0d2f3c8d4d8f069a3150622f8f68a55912^{commit}'
git rev-parse --verify 'a6935ddcdf6716cf96bfdc6804e0cde29471bb5c^{commit}'
python3 - <<'PY'
import hashlib, subprocess
sha = 'a6935ddcdf6716cf96bfdc6804e0cde29471bb5c'
p = 'outputs/duanxian-audit/goals-summary.md'
b = subprocess.check_output(['git', 'show', sha + ':' + p])
h = hashlib.sha256(b).hexdigest()
assert h == 'ac7f045a92af07c23b0b7a15a59421de25756f60883d4a3c9adc75b47e90155e'
print('A-SUMMARY-HASH-PASS', h)
PY
```

4. 分别 `git show <指定 SHA>:outputs/duanxian-audit/gdef-001-def.md` 与 `git show <指定 SHA>:outputs/duanxian-audit/goals-summary.md` 全文读取。对象缺失或哈希不符即报告具体输入问题，不能用内容近似的文件替代。
5. 用第二节命令取得完整树清单。对来源采用 `git show BASE:<path>`；行号由原始解码文本从 1 起计算。单行 JSON 用 JSON Pointer 精确到字段/数组索引，并记录原文件 SHA-256，不能把格式化后的行号当原始行号。不要 import 项目代码来“检查”文件；模块导入也可能写磁盘或触发运行。

### 5.2 全文阅读顺序

下表顺序针对依赖理解；每组全读后才对它下完成结论。B-定义只做了定义所需的基准阅读、清单盘点与重点代码定位，B-实施不能沿用为自己的全文已读证明。

| 顺序 | 必读材料（路径均为 BASE，A 输入除外） | 输出到报告/证据账的内容 |
| --- | --- | --- |
| 1 | A 两份指定输入；`duanxian/novel-goals.md`；`README.md`、`duanxian/README.md`、`engine/README.md` | 六问目标、五种口径、阶段及权威区别。 |
| 2 | `engine/docs/ai-novel-workflow/README.md`；`engine/harnesses/novel-conception-autonomous/docs/final-delivery-contract.md`；`engine/docs/ai-novel-workflow/conception-autonomous-workflow-v2.md`、`hld-autonomous-workflow-v1-design.md`、`hld-skill-contract-catalog-v1.md`、`development-phase.md`（后四项同 workflow 目录） | 先理解完成门与内容权威，再评价产物；全读而非仅摘要。 |
| 3 | `duanxian/conception-approved/` 全部 6 文件；`duanxian/project-display-metadata.json`；`.gitignore` | 批准范围、可复核绑定、机器本体留存、样片和正式标题；记录运行相对路径与实际仓库路径差别。 |
| 4 | `duanxian/design/specs/`、`duanxian/design/workflow-docs/` 全文；`duanxian/design/runs/` 各运行按 manifest→gate/风险→源/产物读；`duanxian/design/design-tasks/`、`duanxian/design/reference/` | 建立版本与状态时间线；旧链不覆盖当前批准构思。 |
| 5 | `duanxian/design-scenes-draft.md`、`duanxian/writing/` 全文、`duanxian/novel-text/2026-06-07-duanxian-novel.md` 全文 | 七类故事控制与现有写作的对应；草稿、素材、正式稿分别记录。 |
| 6 | `duanxian/conception-production/run.py` 及 tests；`duanxian/testing/` 17 文件 | 按真实入口读取 stage 路由、依赖、生成/审核隔离、路径与测试假设；继续追调用实现。 |
| 7 | `engine/harnesses/` 四目录；`engine/skills/` 82 目录；`engine/scripts/` 五文件；`engine/tests/` 与 `engine/testing/` | 每模块按契约/manifest→实现→schema/validator→测试→发布记录读；覆盖 2.5 的跨层闭包。 |
| 8 | 尚未覆盖的 `engine/docs/`、`engine/tasks/`、各发行包清单和根层隐藏文件 | 核对全量清单差集，清零未读独有文本，记录二进制/重复内容核对方式；不将样例任务当生产成果。 |

阅读账最少包含“路径或连续目录范围、文件数量、阅读范围、适用版本/职责、关联目标、验证样本、未决项”。工作中留在会话或内存，最终压缩为报告第一节的覆盖表与第九节索引，不新增第二份笔记/CSV/报告。任何来源目录未覆盖都必须显式列出，不能为满足 12000 字上限隐藏未读事实。

### 5.3 五个审视维度与六问矩阵

**维度一：目标六问。** 报告第二节必须有六行，分别为“要写一本什么小说、为何写、为谁写、怎么写、写成什么样算合格、当前进度与断点”。每行至少包含目标路径/定位、实现对象路径、正向证据、缺口或反证、程度与证据强度。读者未定和篇幅未定按未决处理，不能把没有商业画像称作程序 bug；方法与合格标准须落到契约/代码/产物的可见支持，不能仅重述目标。

**维度二：构思批准链与 P1。** 检查 approval_scope、decision、run_id、completion.status；对照 H1 HTML 与 author-decision SHA-256、P1 manifest/completion、development_handoff、九阶段引用及 run_state。将“记录批准”“文件可复验”“全链重新验证”分三层。completion 中 revision-037 与 README 中最终 revision-038 如被讨论，要区分完成时引用和后续状态，不只因字符串不同判冲突。缺失绑定本体列留存/复验缺口及影响，不猜造本体，不否定批准。

**维度三：HLD/LLD 断点与旧链。** 将项目当前推进描述、旧 7 月 HLD pending、superseded LLD 错误记录、引擎 HLD implementation-candidate 与正式新版 HLD 完成凭证逐项并列。证明某层状态不能跨层外推；旧 K/C/M 编号只在各自来源使用。依据 `duanxian/README.md`“权威与状态”、旧 manifest/gate、HLD 规范与发布记录判断，不靠全文搜索某处“pass”作准入。

**维度四：写作与批准口径。** 对照 R-07 新主体、无当前视听/身体/现实行动权、现实核验与授权、沈逾与顾衡/R-07 关系、程予安/周岚同意、关停且无活动备份、开放结局。每一偏差须给批准要求与写作片段双向证据，说明是旧稿差异、迁移待办、当前不一致还是无法判断。样片的局部感官写法不能变为新事实，作品人物的误解也不能直接当作者叙述违规。

**维度五：代码与流水线可用性。** 检查声明的能力有没有实际入口、契约/schema、实现、负向门禁、测试及项目运行凭证。特别检查目录重构后的路径、旧 root 引用、纯 fixture 与生产依赖、作者门、独立评审与版本失效。五个顶层 validator、项目 CLI/构建器、四个 harness、82 技能均应有归类。测试存在与通过、结构验收与语义发布、通用引擎能力与《断线》实例完成分别说明。

### 5.4 证据规则、口径与实现程度

每个实质结论用稳定 ID（例如 B-E001），最小记录结构为：问题/目标→适用版本与对象→规范依据→实现或产物证据→反证/限制→程度→影响。可用索引避免重复长路径，但每个引用键必须唯一解析到完整仓库路径和定位；实现程度结论至少有路径级证据，争议与 ISSUE 候选须有行级或 JSON 字段证据及短引。格式示例：`duanxian/conception-production/run.py:L14,L41-L54`；JSON 用“完整路径 + /approval_scope + 文件哈希”。不得只写“代码里”“S05”“批准目录”。

否定性断言须给搜索范围、命令/筛选规则和结果。例如只对 BASE 的全量文件名列表查三个机器文件名，可以写“未在跟踪树找到这些文件名”，不能写“机器链从未存在”。旧根路径先查实际迁移路径，区分文档引用过时、源文件迁移和数据真正缺失。所有“能运行/已通过/覆盖全部”都要有相应证据；静态阅读只能支持静态结论。

五种口径沿用目标文档，标在事实段或表格行旁，不仅在前言声明：

| 标注 | 用法 |
| --- | --- |
| 【当前权威口径】 | 当前批准故事与明确留存状态；构思批准不扩为 HLD/全书批准。 |
| 【历史/旧链口径】 | 旧 SPEC、旧 run、旧正文、历史测试/发布记录的版本限定事实；不能静默升级。 |
| 【未完成项】 | 当前目标缺口、待批准、未留存/不可复验或证据不足；明确是哪一种。 |
| 【流程规范】 | 契约要求、方法、机器/语义/作者门，是“应当”，不是“已经”。 |
| 【推断】 | 静态调用分析、影响分析及建议性归纳，列前提和不确定性；不创造故事事实或作者动机。 |

程度与证据强度分开记录，不算一个全仓完成百分比：

| 程度 | 判定条件 | 不能据此宣称 |
| --- | --- | --- |
| 已完成（限定对象） | 相应要求有直接产物/实现证据，所需批准和验证证据闭合，未发现反证；写清完成的是哪一阶段/能力。 | 一个模块文件存在就等于全系统可用，构思 approved 就等于全书完成。 |
| 部分完成 | 有实质实现或产物，但缺必需链路、批准、验证或覆盖；同时列已有和缺少两面。 | 凭代码数量估算任意完成百分比。 |
| 缺口 | 已确定目标/契约有要求，冻结证据显示缺失、不满足或冲突；区分内容、实现、准入、留存、验证五类。 | 未入 Git 就等于现实未实现，旧稿差异就等于当前回归。 |
| 历史遗留 | 证据属于被替代版本或旧工具链；注明仍否影响当前入口及迁移责任。 | 历史问题不需再判断影响，或历史 pass 覆盖现行门。 |
| 无法判断 | 关键证据不可得或冲突无法裁决，列缺什么、会影响什么结论。 | 强行选已完成/未完成来制造确定性。 |

证据强度写为“直接留存”“静态可定位”“历史运行记录（注明版本）”“本轮实测（仅获授权时）”“不足”。这些是本报告的审视标记，不改写小说规范中的 ready/pass/approved 状态机。

### 5.5 基线失败、限制与候选问题归并

本作业没有提供当前测试运行成绩，禁止编写某数量测试失败或通过。读到历史日志/验收 JSON 时注明其来源提交、适用实现、输入、命令、环境和记录时间；缺字段则注明无法完整复验。断言“基线已有失败”必须有该基线实际失败记录，测试源码里负例期待异常不等于测试失败，旧日志也不等于当前基线事实。

如实施自身契约禁止测试：只读测试/fixture/入口与依赖，不运行 pytest、selftest、validator、生成器或 build_release；写清“本轮未执行”。如自身契约明确允许测试：先阅读写入与网络副作用，只在授权工作区的隔离输出/缓存/临时目录运行授权集合；禁止写系统临时目录、源码或其他作业目录，禁止自动修复、安装依赖或请求模型生成。记录命令、cwd、版本、输入 SHA、退出码、失败定位；缺运行数据/依赖与代码逻辑不满足分别分类，不为了得到 PASS 修改基线。没有同输入同环境的先后对照，不得称为“新回归”。

ISSUE 候选在实施报告内使用 B-IC001 等本地编号。每条包含：问题、应然依据、实际证据路径/定位、影响对象、版本归属、证据强度、根因判断（不确定则注明）、建议方向、建议验证方式、与其他候选的归并关系。一个候选应当内聚且可独立处理；同一根因多个路径合并，互不依赖的根因分开。不预填 GitHub 编号/链接，不宣称已提交，不强凑候选数量；若无可证候选，保留该节并说明范围、检查和零候选理由。仅待取证的线索与已具证的问题分列，供 C 决定是否立项。

### 5.6 固定报告结构、字数及成稿

唯一文件：`outputs/duanxian-audit/implementation-review-report.md`。标题后注明 BASE、定义书版本、A 基准、方法及本轮测试是否执行。固定九个二级节如下，子节可增，二级节名称与顺序不变：

| 节标题 | 必需内容 | 建议中文字符预算 |
| --- | --- | ---: |
| 一、审视范围与证据基线 | 冻结版本、全量覆盖表、阅读与抽样方法、权限及关键限制。 | 650–900 |
| 二、目标六问与实现对照 | 六问矩阵，每问有证据、差距、程度和证据强度。 | 1000–1400 |
| 三、构思批准链与P1留存 | 批准/完成记录、可核验 hash、未留存机器本体及影响。 | 700–1000 |
| 四、HLD与LLD断点及旧链隔离 | 分阶段状态与版本时间线，旧稿/旧 run/新版规范不混用。 | 700–1000 |
| 五、写作产物与批准口径一致性 | 全文阅读后的七类控制对照，正向支持与偏差都取证。 | 900–1200 |
| 六、代码层与流水线契约可用性 | CLI、构建器、skills/harnesses/validators/tests 存量，代表调用闭包，运行证据边界。 | 1200–1700 |
| 七、实现程度总评与未决事项 | 分对象归纳，不单一百分比；区分已完成/部分/缺口/历史/无法判断，按影响说明下一证据需求。 | 550–800 |
| 八、ISSUE 候选清单 | 按 5.5 字段逐条内聚记录，含候选与待取证线索分界。 | 600–1000 |
| 九、证据索引与自检记录 | 唯一路径索引、关键定位、机械结果、测试未执行声明/授权运行摘要、剩余限制。 | 300–600 |

预算合计 6600–9600，为中文标注和标题留余量；最终以**全文 6000–12000 个中文字符**为硬门，包括标题、表格、标注和索引，不把 UTF-8 字节、英文、数字、标点算作中文字。计数算法见第六节，与 A 相同。避免复制大段源文凑数；主体应说清目标、证据、影响与限度。正文不得写“独立验收已通过”作为实施自评；不得把后续行动建议写成已经完成。

### 5.7 提交、推送与完成信号

1. 从实施自身冻结 spec 取得 `b_work_branch` 和 `b_credential_file`，核对允许推送引用及凭据只读权限。常规实施作业号为 rint-001，但分支以其冻结值为准；缺任一项报告编排缺口，不猜、不使用定义作业凭据。
2. 成稿后先运行 6.1 文件检查与语义自检，再执行 `git status --short --untracked-files=all`、`git diff --check`。只新增报告；修正轮仅允许改该作业新建报告。来源变化不得自行 reset/checkout。逐条成功后执行：

```bash
test -n "$b_work_branch"
test "$(git branch --show-current)" = "$b_work_branch"
git add -- outputs/duanxian-audit/implementation-review-report.md
git diff --cached --check
git diff --cached 92573f1cca40f37cee04d2beb8708ff33ba603d6 --name-status
# 核对上一项唯一是 A outputs/duanxian-audit/implementation-review-report.md，再提交。
git -c user.name=remote-agent -c user.email=remote-agent@kunora.local commit -m "docs(audit): add implementation review report (duanxian-audit-rint-001)"
```

提交信息若实施自身契约有原文要求，以该要求为准。禁止 `git add .`、合并 A 分支、修改历史、强推或将控制文件加入提交。修正用普通追加提交，不改变唯一文件约束。

3. 对已提交候选运行 6.1 候选范围检查，记录完整 SHA 和报告 SHA-256。按自身授权认证方式推送；若采用与本作业相同的命令替换方式，关闭追踪，并由运行器在内存捕获、脱敏输出，不打印含凭据 URL：

```bash
set +x
unset GIT_TRACE GIT_TRACE_CURL GIT_CURL_VERBOSE GIT_TRACE_PACKET GIT_TRACE_SETUP
test -r "$b_credential_file"
# 以下认证命令只能在保证 stdout/stderr 不泄露凭据的运行器内执行。
git push "https://x-access-token:$(cat -- "$b_credential_file")@github.com/innuama-coder/ai-novels.git" "HEAD:refs/heads/$b_work_branch"
git rev-parse HEAD
git ls-remote origin "refs/heads/$b_work_branch"
```

不复制凭据到文件、配置、日志或交付物；不得将秘密文本放进修正指令。推送退出 0 且远端完整 SHA 与本地 HEAD 一致才算交付。认证/网络失败保留已完成本地提交，报告具体失败，不试其他凭据，不扩大网络范围。

4. 向编排方输出唯一文件路径、完整提交号、报告 SHA-256、BASE、自检结果和未决项；只对远端已核对的候选输出最后一行 `DXARINT-DONE-<tip7>`。这里是实施哨兵，不能使用本定义作业的 DXARDEF 前缀。未成功推送不输出完成哨兵。

## 六、独立验收作业检查单

### 6.1 封定输入与机械检查

验收者保持独立的 codex/gpt-6-astra high 作业，先读取自身冻结契约、获准定义书、A 两份输入和 BASE；封定实施候选完整 SHA、文件 SHA-256、交付分支与远端证据。不能仅按最新分支验收，也不能把实施者自评当独立结论。机械门只用标准库读文件和 Git，不 import 业务模块、不执行仓库测试或构建。

以下文件检查供实施提交前自检及验收复跑，必须从实施/验收仓库根运行：

```bash
python3 - <<'PY'
import hashlib, pathlib, re, subprocess
base = '92573f1cca40f37cee04d2beb8708ff33ba603d6'
p = pathlib.Path('outputs/duanxian-audit/implementation-review-report.md')
assert p.is_file() and not p.is_symlink(), 'not-regular-file'
b = p.read_bytes()
t = b.decode('utf-8')
assert b and '\x00' not in t, 'empty-or-NUL'
ranges = ((0x3400, 0x4DBF), (0x4E00, 0x9FFF), (0xF900, 0xFAFF),
          (0x20000, 0x2EE5F), (0x2F800, 0x2FA1F), (0x30000, 0x323AF))
n = sum(any(lo <= ord(c) <= hi for lo, hi in ranges) for c in t)
assert 6000 <= n <= 12000, f'Chinese-count={n}'
expected = ['一、审视范围与证据基线', '二、目标六问与实现对照',
            '三、构思批准链与P1留存', '四、HLD与LLD断点及旧链隔离',
            '五、写作产物与批准口径一致性', '六、代码层与流水线契约可用性',
            '七、实现程度总评与未决事项', '八、ISSUE 候选清单', '九、证据索引与自检记录']
assert re.findall(r'^## (.+)$', t, re.M) == expected, 'report-headings'
assert base in t, 'missing-frozen-baseline'
for label in ['当前权威口径', '历史/旧链口径', '未完成项', '流程规范', '推断']:
    assert '【' + label + '】' in t, 'missing-label:' + label
assert not re.search(r'gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|glpat-[A-Za-z0-9_-]{15,}', t), 'secret-pattern'
assert not re.search(r'(?im)^\s*(TODO|TBD)\b', t), 'unfinished-placeholder'
subprocess.run(['git', 'cat-file', '-e', base + '^{commit}'], check=True)
print('FILE-PASS', 'Chinese-count=' + str(n), 'bytes=' + str(len(b)),
      'sha256=' + hashlib.sha256(b).hexdigest())
PY
```

标签出现只是机械门，是否贴对由语义检查决定。完成候选另运行以下范围门；验收时 HEAD 必须已由编排指定为待验的完整候选 SHA，不能以此脚本替代候选身份核对：

```bash
python3 - <<'PY'
import pathlib, subprocess
base = '92573f1cca40f37cee04d2beb8708ff33ba603d6'
p = 'outputs/duanxian-audit/implementation-review-report.md'
def git(*args):
    return subprocess.check_output(['git', *args])
subprocess.run(['git', 'merge-base', '--is-ancestor', base, 'HEAD'], check=True)
assert git('diff', '--name-status', base, 'HEAD').decode().splitlines() == ['A\t' + p], 'scope-not-single-addition'
assert not git('status', '--porcelain', '--untracked-files=all').strip(), 'dirty-worktree'
assert git('show', 'HEAD:' + p) == pathlib.Path(p).read_bytes(), 'candidate-file-mismatch'
commits = git('rev-list', '--reverse', base + '..HEAD').decode().splitlines()
assert commits, 'missing-delivery-commit'
for commit in commits:
    parents = git('rev-list', '--parents', '-n', '1', commit).decode().split()[1:]
    assert len(parents) == 1, 'unexpected-merge-or-root'
    rows = git('diff-tree', '--no-commit-id', '--name-status', '-r', commit).decode().splitlines()
    assert rows and all(row in ('A\t' + p, 'M\t' + p) for row in rows), 'history-scope-violation'
print('SCOPE-PASS', 'candidate=' + git('rev-parse', 'HEAD').decode().strip())
PY
```

“不得修改既有文件”指 BASE 已有文件；迭代允许修改本作业新建报告。ACK 和初始化控制证据若已按编排安排忽略，不算业务新增，但不能借忽略目录藏第二份业务产物，不新增忽略规则。Git 范围检查只能证明提交/工作树可见状态；是否执行禁用命令或在忽略目录写入业务文件，还须核对作业记录，不能把干净状态当充分证据。

### 6.2 可操作检查项

每项记录“检查 ID→候选段落→来源路径/定位→检查方式→PASS/FAIL/输入阻塞说明”。以下全部为必要门，无总分抵销。

| ID | 验收动作 | 通过条件 |
| --- | --- | --- |
| M01 | 比对 BASE、A 两份提交、目标总结哈希、定义书版本、候选完整 SHA | 与交接一致；没有混入最新 main、其他候选或未确认目标。 |
| M02 | 复跑文件与范围脚本；检查提交元数据及远端 SHA | UTF-8、6000–12000 中文字、九节、五口径、唯一新增、历史无越界；远端对应同候选。 |
| M03 | 查候选内容、diff、提交消息和交接摘要 | 无秘密、占位、伪造测试/批准/独立验收；机械模式不能代替人工检查。 |
| C01 | 将覆盖表对照 BASE 全量清单及 2.1–2.4 | 文件数量和目录正确，全文阅读覆盖明确，二进制/重复投影处理有记录，无隐藏未读区域；不能把抽样写成全读。 |
| C02 | 检查九节及六问矩阵 | 六问每项都有目标、实现路径、正反证据、差距、程度/强度；五个审视维度全部落实。 |
| C03 | 查 CLI、17 项 testing、四 harness、82 技能、五校验器、测试目录的归类与闭包 | 清单不是能力宣言；有跨文件取证，纯提示/旧工具/fixture/正式 runtime 分类准确，数量差异有解释。 |
| E01 | 解析所有引用路径并在 BASE 定位 | 路径真实；历史迁移路径、运行相对路径、未留存引用明确标识；行/字段与原始文件一致。只验证存在不能判语义通过。 |
| E02 | 对所有已完成结论、所有直接冲突、所有 ISSUE 候选及所有权限/hash/作者门断言逐条回读 | 证据直接支持结论，已考虑反证、阶段与版本；建议与事实不混写。 |
| E03 | 按下述确定性抽样核对其余结论 | 样本全部有可复现支持；出现一项不支持即扩查同类，必要时回实施；不能以多数正确掩盖错误。 |
| A01 | 对照 A 总结六节与目标文档原始依据 | 目标理解一致；读者定位、章数/篇幅、法律身份/重载/互信未决项保持原边界，不静默改写 A。 |
| A02 | 全查故事七类高风险控制及样片使用 | R-07/顾衡、感官、权限、亲属、信息、关停、开放边界正确；样片非权威，旧叙述契约不晋升。 |
| A03 | 核对批准 JSON、可得 hash 与缺失查找范围 | approved/ready 限构思；留存绑定≠全链 validator 重跑；未入库≠不存在/批准无效；revision 指向有阶段解释。 |
| A04 | 核对旧 HLD、superseded LLD、HLD 发布记录及正文状态 | 历史待审、错误记录、新版资格和项目产物完成分开，未把草稿或 implementation-candidate 写成已发布。 |
| A05 | 核对报告各事实段/表格行的五种口径 | 不是仅在开头列标签；规范、推断、旧事实、当前事实和缺证标得准确。 |
| T01 | 检查测试与可用性段落及作业执行记录 | 存量≠通过；负例预期拒绝≠测试失败；本轮未执行明确；历史记录、环境缺口、基线问题与新回归分开。 |
| I01 | 全审 ISSUE 候选清单 | 每条有问题、双向证据、影响、建议与验证方向，粒度内聚；未创建 ISSUE、不预造编号；无候选时有充分说明。 |
| S01 | 检查分级与总评是否被证据支持 | 分对象评价，未知不强判，历史问题仍评当前影响；没有无依据总完成率；总评不与分节冲突。 |
| X01 | 核对最终树、逐提交历史、未提交内容与执行记录 | 未改既有文件/依赖/配置、未越权测试/构建/联网/推送，未追加业务文件，模型分工未变。 |

E03 抽样固定规则：除 E02 全查集合外，对第二至第七节每节按结论出现顺序取首条、中位条（偶数取前一个）、末条，不足三条则全取；补齐至少一个“部分完成/历史遗留/无法判断”实例（若该类存在）及每个代码职责组至少一个样本。每个样本保留候选短引、完整证据路径、原文定位和支持/不支持理由。样本发现同型错误扩查该类全部断言；涉及最终结论或权威越级，重审所有受影响章节。E01 路径真实性全查，不能以 E03 抽样替代。

### 6.3 结论与迭代修正模板

PASS：全部必要项通过，对封定候选给结论，列已执行检查及未执行但契约允许的事项；报告真实披露运行证据缺口并不自动导致 FAIL，掩盖缺口或据此作过强结论才不合格。FAIL：可定位的内容、证据、结构、覆盖或范围违例，列全已发现问题并返回实施。BLOCKED：无法取得/验证必需候选或 A 基准，或关键同层权威矛盾需 Owner 裁决；写明所缺输入和已能核对的部分，不用猜测补齐。

独立验收不在实施分支新增验收报告，按编排渠道反馈。修正模板如下，每条足够让实施者独立操作：

```text
候选完整 SHA：<值>；报告 SHA-256：<值>；定义书完整 SHA：<值>
内容基线：92573f1cca40f37cee04d2beb8708ff33ba603d6
验收结论：FAIL / BLOCKED；检查 ID：<M/C/E/A/T/I/S/X 编号>
报告定位：outputs/duanxian-audit/implementation-review-report.md → <节/段/证据 ID/短引>
证据定位：<BASE 下完整路径 + 行号或 JSON Pointer + 必要短引>
问题及影响：<缺失、无支撑、版本混淆、口径升级、分级不当或越界>
修正动作：<仅修改本作业新增报告中的具体内容；补什么、删除什么、保留什么>
不得改变：<相关 Owner 原文约束、A 目标口径、源文件、唯一交付路径和模型分配>
复验要求：<文件/范围机械门 + 受影响检查 ID + 扩查集合>
待提供输入（仅 BLOCKED）：<所缺对象/哈希/授权或裁决，提供者为编排方或 Owner>
```

实施者在同一报告追加修正、普通提交并推送新候选；验收者对新 SHA 重跑机械/范围门，重审修正断言、相邻因果和扩查集合，不沿用旧 PASS。涉及定义书本身不足或 A 目标需变更时由编排方回相应定义/Owner 确认门，实施者不回改本定义书或冻结来源。B 验收通过只表示审视报告合格，不补发小说 HLD、LLD 或手稿批准。
