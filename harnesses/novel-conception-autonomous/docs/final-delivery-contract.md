# 小说构思阶段最终交付契约

## 1. 完成定义

构思阶段的目标不是交付一堆过程文件，而是同时交付：一份可供机器继续开发的完整
构思本体、一份可供作者在十分钟内判断方向的人审呈现，以及一份证明二者属于同一版
构思且已获作者决定的准入凭证。

只有当前生产状态为 `development_status=ready`，且
`completion/conception-completion.json` 通过正式 validator，才可声明构思阶段完成。
`revise`、`rejected`、`waiting_author`、任一活动 return 或仅有 HTML 均不是完成。

## 2. 最终交付物

### A. 完整机器构思包（权威本体）

正式目录为当前 P1 package，至少包含：

- `novel-conception-package.json`：B0 作者控制、S1 故事线、W1 世界、E1 环境、
  T1 事件、C1 角色、Q1 审查的无损组合与权威分区；
- `novel-conception-spec.md`：同一构思的确定性机器可读规格；
- `cross-model-index.json` 与 `traceability-matrix.md`：ID、引用、定义位置和来源追溯；
- `development-handoff.json`：必须遵守、允许开发、必须询问和开放项边界；
- 上游正式快照、validation、manifest、completion、execution 与实现快照。

P1 是构思事实的唯一最终权威。任何人审摘要、图形或样章与 P1 冲突时，不得以 P1
自动覆盖后继续交付；必须判定呈现失败并回到其拥有者修正。

### B. 人审构思包（非权威忠实呈现）

正式 H1 链必须共同交付：

- `human-review-report.html`：作者默认阅读入口，清晰呈现世界设定、故事线设计、
  角色定义、样章和批准/修改/否决入口；
- `human-review-report.json`：HTML 的结构化内容源；
- `human-review-report.md`：同一报告的确定性文本投影，供无浏览器场景使用；
- `fragment-package.json` 与 `fragments.md`：严格标注为非权威体验样片；
- `presentation-fidelity-review.json`：P1 到人审内容的独立逐元素语义一致性审查；
- H1-A plan、H1-C render record、各 package manifest、validation、workspace 和
  formal H1 completion。

HTML 可以压缩、重排和图形化 P1，但不得改变作者锁定项、世界规则、故事线关系、
事件因果、角色动机、开放边界或批准范围。样章可以在明确的局部创作自由内实例化
感官、动作和措辞，但不能把这些局部实现升级为新的构思事实。

### C. 作者决定与开发准入包（完成凭证）

必须同时存在：

- 外部密封的 `author-decision.json`，绑定当前 H1 与 HTML hash；
- P1 内的当前 `development-handoff.json`；
- `completion/conception-completion.json` 及其 validation、执行记录和实现快照；
- 最新 append-only run state，且其当前 B0–H1 completion、作者决定和 final
  completion 与上述文件逐项一致。

访谈 I0–I5、V1、V2 的完整记录、报告、控制投影、事实依赖表、批准和 completion 是
强制来源证据；它们不是独立的最终小说构思本体，但必须能从 B0/P1 的 lineage 回溯并
重新验证。缺失来源证据时不得以现有 P1 或 HTML 猜测补齐。

## 3. 内容一致性标准

“完全匹配”指实质语义一致，不要求机器稿与人审报告逐字相同。必须同时满足：

1. **身份一致**：同一 production run、H1 session、P1 completion、plan、fragment、
   assembly 和 HTML manifest 的路径与 SHA-256 链闭合。
2. **范围一致**：人审默认可见元素与 plan 精确相等；关键控制不得只藏在审计字段中，
   支持性细节可进入非公开机器追溯层。
3. **结论一致**：作者意图、世界规则、故事线及连接、事件前提/选择/结果、角色位置/
   动机/关系/变化和结局边界不得反向、删改或无依据确定化。
4. **强调一致**：十分钟压缩不得遗漏会改变作者判断的例外、代价、限制或未决项，也
   不得把支持性信息放大成主控制。
5. **权威一致**：普通呈现元素只能是 `faithful`；样章只能是
   `non_authoritative_sample`；HTML、图形、样章均不得新增权威事实。
6. **决定一致**：人审批准的对象必须是当前完整 P1 及其忠实呈现，允许决定固定为
   `approved`、`revise`、`rejected`，且不得预选。

来源 ID 存在、schema 通过、hash 相同和 HTML 可打开只能证明结构与版本，不能单独证明
上述语义一致性。`novel-conception-presentation-fidelity-reviewer` 的独立逐元素 pass
是 H1-A 发布的必要条件。

## 4. 交付标准与验收方法

| 验收域 | 硬标准 | 正式验收方法 | 失败去向 |
|---|---|---|---|
| 访谈来源 | I0–I5 ready；完整计划、逐轮记录和报告；V1 结构与语义 pass；V2 获作者批准；可进入 B0 | interview harness validators、V1/V2 completion 与批准 hash 重验 | 对应 I0–I5、V1 或 V2 |
| 构思完整性 | S1/W1/E1/T1/C1 全部 ready；Q1 独立审查 ready、无 actionable finding；所有 story demand 被世界、环境、事件、角色覆盖 | 各 stage validator、Q1 semantic/handoff review、cross-model coverage | 最早拥有问题的 S1–C1 |
| 机器包 | P1 无损包含 B0–Q1 当前正式值；authority/open item/index/handoff 完整；相同输入产生同一输出 | P1 validator、manifest/file inventory、逐文件 hash 与确定性重跑 | P1；若来源错误则回来源 stage |
| 人审内容 | 四维内容与决定操作清晰；默认阅读不超过 600 秒；样章非权威；逐元素语义忠实 | H1-A validator + 独立 `presentation-fidelity-review.json` 五维全 pass | H1-A plan 或 H1-B |
| HTML | 仅渲染当前 report；四维导航、图形、样章、决定入口可用；离线可读；无隐藏替代结论 | H1-C validator、render record、DOM/可访问性/打印测试、报告 hash 重算 | H1-C；内容错误不得在 HTML 修 |
| 作者决定 | 决定来自外部作者，绑定当前 H1/HTML；无 Agent 推断；revise/rejected 不准入 | author-decision schema、签封与 lineage validator | 等待作者或确定性 return |
| 最终准入 | 最新状态 ready；九个当前 stage completions、P1/H1 manifests、决定和 handoff 全绑定；无活动 return | final completion validator 与 production state replay | 对应失效 stage，禁止开发 |

## 5. 必须执行的反向验收

发布候选除正向全链外，至少要证明以下篡改会失败：

- 删除或替换一个访谈 completion、P1 模型、H1 元素、样章或 manifest 文件；
- 把旧 P1、旧 H1、其他 run/session 或其他作者决定混入当前链；
- 人审元素保留 source IDs 却改变因果、角色动机、边界或未决状态；
- 样章把局部描写升级为世界规则、人物既定事实或结局；
- 忠实度审查缺失、与生成者身份相同、少审元素、证据引文不在候选内容中或内容
  hash 变化；
- HTML 与 report JSON 不一致，或 approved 决定绑定的 HTML 已变化；
- revise/rejected 分支生成 final completion，或 final 状态仍有活动 return。

所有负例必须 fail closed：不得自动润色掩盖、不得静默降级、不得复用旧成功 verdict。

## 6. 最终交付清单

对作者交付：一个 `human-review-report.html` 入口、对应样章，以及明确的三分支决定。
对开发者交付：当前 P1 package 与 `development-handoff.json`。
对审计/自动化交付：访谈来源链、H1 全链、独立忠实度审查、作者决定、最终
`conception-completion.json` 和最新 production state。

三组缺一不可；只有 A+B 没有作者决定属于“待审”，只有 A 没有 B 属于“不可人审”，
只有 B 没有 A 属于“无权威来源”，都不得称为构思阶段最终完成。
