# 小说 HLD V1：逐技能定义与输入输出契约目录

> 本文件是 [`hld-autonomous-workflow-v1-design.md`](hld-autonomous-workflow-v1-design.md) 的技能级唯一实现契约。技能名、artifact role、字段、输入顺序、source access、verdict 代数和包 profile 只能在本文件定义；主设计只解释目标和流程，不得另造同义字段或放宽本目录。
>
> 规范状态：V1 契约已冻结。本目录不自行声明实现或发布资格；当前资格只能由 Harness `manifest.yaml`、机器验收记录和发布清单共同证明。

## 1. 适用范围

本目录定义 `novel-hld-autonomous` harness 中 14 个 bounded skill 的：

- 定义、类型与触发条件；
- 目标和唯一职责；
- 边界与禁止事项；
- 执行约束；
- 精确输入和硬准入；
- canonical 交付物和包契约；
- ready / revise / blocked 条件；
- 唯一下游消费者。

Harness 自身负责阶段拓扑、工作单、状态、return、作者门和完成事务。任何单个 skill 都不得把这些编排能力藏进自己的 `SKILL.md`。

## 2. 公共硬契约

### 2.1 Skill 类型

V1 只允许：

- `thinking`：拥有语义判断，不拥有确定性封包；
- `script`：拥有确定性变换，不拥有故事判断；
- `hybrid / thinking-dominant`：语义组织为主，脚本仅做结构和引用检查。

### 2.2 公共输入门

每个 skill（包括 HB0）都只能由 harness 签发的 `work-order.json` 启动。Harness 先对 `hld-run-request.json` 做最小结构校验，创建不可变 `revision-000` 初始状态，再向 HB0 签发工作单；HB0 无权自行创建或修改状态。工作单必须包含：

- `schema_version / harness / hld_run_id / work_order_id`；
- `stage / action / exact_owner_skill / owner_version / implementation_sha256`；
- harness 单调分配的 `event_sequence` 与固定 `result_timestamp`；
- `input_gate` 引用；
- `state_before` 引用；
- 严格有序的 `upstream_completions[]`；
- 允许读取的 `file_allowlist[]`；
- HA1–HK1 的 non-quality `unresolved_projection[]`，以及 HQ1 的 quality-domain `unresolved_projection[]`；其他 stage 必须为空数组；
- `mode=forward|return_resolution`；
- forward 时为 `null`、返工时完整绑定的 `return_binding`；
- `revision_plan_ref / revision_plan_state_ref`，无返工事务时都为 `null`；
- 唯一 output directory；
- 提交截止状态，不包含故事答案。

Actor、owner、stage、state、gate 或 allowlist 任一不匹配时，skill 必须在读取语义输入前失败。

### 2.3 公共引用

所有 artifact reference 固定包含：

```json
{
  "path": "package-relative/path",
  "sha256": "64-lowercase-hex",
  "manifest_path": "package-relative/package-manifest.json",
  "manifest_sha256": "64-lowercase-hex",
  "completion_path": "package-relative/stage-completion.json",
  "completion_sha256": "64-lowercase-hex"
}
```

内部复合阶段尚无 top-level completion 时使用 `internalArtifactReference`，只省略 completion 两字段，并强制绑定同一 workspace state。禁止绝对路径、文件名猜测、自然语言等价替代和未进 manifest 的文件。

### 2.4 Thinking skill 的 ready 包

HA1–HK1 的文件集合必须精确等于：

```text
<canonical-model>.json
generation-session.json
generation-evidence/*.json
execution-record.json
<preview>.md
validation.json
package-manifest.json
stage-completion.json
```

要求：

- canonical JSON 是唯一内容权威；
- Markdown 是由 canonical 模型生成的非权威阅读投影；
- generation evidence 必须来自当前受控任务，形成前向 hash 链；
- execution record 绑定 skill、实现、工作单、输入、会话和输出；
- Schema 版本固定，`additionalProperties:false`；
- validator 通过且语义自评无 blocker 才能生成 completion。

#### 2.4-A Reviewer-thinking 的 top-level ready 包

HQ1 不使用设计型 generation evidence。其内容包文件集合必须精确等于：

```text
hld-semantic-review.json
review-session.json
review-execution.json
validation.json
package-manifest.json
stage-completion.json
```

`review-session.json` 冻结 review task、读取 allowlist、实际读取集合和被审对象 hash；语义证据只存在于 `hld-semantic-review.json` 的 pass claims、challenges 和 findings 中。HQ1 不得生成设计候选或 producer rationale。

#### 2.4-B 复合 stage 内部任务包

复合 stage 的内部任务只有密封内部包，没有 top-level completion。固定 profile 为：

| Internal task | 内容包精确文件集合 |
| --- | --- |
| HQ2 `consumer_test` | `handoff-consumption-test.json / review-session.json / consumption-test-execution.json / validation.json / package-manifest.json` |
| HQ2 `fidelity_test` | `handoff-fidelity-test.json / review-session.json / fidelity-test-execution.json / validation.json / package-manifest.json` |
| HH1-A | `hld-human-review-report.json / generation-session.json / generation-evidence/*.json / report-assembly-execution.json / validation.json / package-manifest.json` |
| HH1-B | `presentation-fidelity-review.json / review-session.json / fidelity-review-execution.json / validation.json / package-manifest.json` |
| HH1-C | `hld-human-review-report.html / render-target-registry.json / render-execution.json / validation.json / package-manifest.json` |

内部 thinking reviewer 的 `review-session.json` 规则与 HQ1 相同。HH1-A 是 thinking-dominant，因此保留受控 generation session/evidence；其脚本部分只记录在 `report-assembly-execution.json` 中。所有内部包的 `package-manifest.json` 只覆盖表中内容文件，不含 work-order 结果信封。

### 2.5 Script skill 的 ready 包

Script 不得伪造 generation evidence。Top-level stage 的 ready 包固定包含：

```text
<deterministic-output-files>
<execution-record>.json
validation.json
package-manifest.json
stage-completion.json
```

`<execution-record>` 的文件角色固定为 `execution_record`，具体文件名由该 skill 契约冻结。相同输入、实现和参数必须产生字节一致的确定性输出。退出码 `0` 才可 ready；结构或 hash 失败使用非零退出码。复合 stage 的内部 script 包不生成 top-level completion；HF1 以 `hld-completion.json` 代替 stage completion。

### 2.6 Work-order 结果与非 ready 包

每个 work order 必须且只能生成一个位于内容包目录之外、但仍位于 sealed work-order workspace 内的 `stage-result.json`。它是 parent-consumption 结果信封，不进入内容包 `package-manifest.json`，其自身 hash 由下一份 run-state 记录，从而避免 manifest 自引用。公共必需字段为 `schema_version / harness / hld_run_id / revision / stage / skill / work_order_id / task_id / event_sequence / result_scope / result / state_before_ref / input_gate_ref / result_manifest_ref / validation_ref / produced_at`；其中 `event_sequence` 和 `produced_at` 必须逐值复制 work order 的 `event_sequence / result_timestamp`，skill 不得读取本机时钟。`result_scope` 只允许 `top_level|composite_internal`，`result` 只允许：

- `ready` + `result_scope=top_level`：另需 `completion_ref`，引用 ready manifest、validation 和 completion；
- `ready` + `result_scope=composite_internal`：只允许 HQ2 两个 mode 与 HH1-A/B/C，另需 `internal_manifest_ref`，禁止 `completion_ref`；
- `revise`：另需 `revision_class=local_candidate|external_author_request` 和 `revision_report_ref`；`local_candidate` 必须有 `candidate_ref / local_defect_evidence[]`，`external_author_request` 必须有 `author_event_ref` 且不得伪造 candidate；
- `blocked`：另需 `gate_data_ref / blocked_report_ref / blocker_class / affected_ids[]`；
- `runtime_error`：另需 `runtime_error_ref`，只记录运行错误，不产生语义 verdict。

HQ2 两个 mode 和 HH1-A/B/C 的所有 result（包括 non-ready）都必须使用 `result_scope=composite_internal`；其他 skill 与 composite publisher 必须使用 `top_level`。Internal result 不得被 router 当作 stage 结果直接推进或定向返工，必须先经 2.16 publisher 包装成 top-level result。

四种 result 的条件字段互斥；路径必须位于当前 sealed work-order workspace；所有引用都必须含 role、相对路径和 sha256。`stage-result.json` 不含 `next_stage`、`return_owner` 或 `run_state_after`，防止 skill 越权路由。

非复合 top-level 的 local-candidate revise 内容包精确包含 candidate/evidence/execution、`revision-report.json`、`validation.json` 和 `result-manifest.json`；external-author-request revise 内容包用密封 `author-decision.json` 引用替代 candidate/evidence。非复合 blocked 内容包精确包含 `gate-data.json`、`blocked-report.json`、`validation.json` 和 `result-manifest.json`。复合 stage 的 top-level non-ready 包使用 2.16 的 byte-copy profile。`stage-result.json` 始终是内容包外的结果信封。上述内容包均不得生成 stage completion，但 result manifest 与 stage result hash 必须被下一份 run-state 强绑定。

`external_author_request` 只允许 HF1 消费最终 `author-decision.json` 的 `decision=revise` 时使用。中途 `must_ask` 必须产生 `blocked/author_required`，由 2.12 的 author-question transaction 解决；`author-answer-event.json` 不得填入 `author_event_ref` 冒充最终决定。

Harness 是唯一 parent consumer：它按固定 owner matrix 把结果转换为 forward、local return、upstream return、author question、reality reentry 或 runtime stop。Skill 不得写 run-state、active return 或最终 owner。只有 `ready` completion 可被顶层内容下游消费；`composite_internal/ready` 只能由对应 2.16 publisher 通过 internal manifest 消费。

### 2.7 公共语义约束

所有 skill 必须：

- 保持 baseline 的主分类 `mandatory / freedom / must_ask / open`、独立 `open_item` 标志和原值；
- 只在当前 owner 的 `freedom` 内生成 `hld_owned` 决定；
- 用稳定 ID、JSON Pointer 和规范值 hash 追溯来源；
- 不用固定对象数量代替故事需要；
- 不修改上游 canonical 模型；
- 不产生新的主要世界事实、环境、事件、人物、关系或结局；
- 不裁决作者问题；
- 不写 LLD 细节或小说正文。

### 2.8 Thinking skill 决策契约

HA1–HK1 的受控 generation evidence 必须依次包含：

1. `dependency-assessment`：为 work order 投影的每个 unresolved source 生成 stage-scoped `HDD-`；出现 `required_now` 时必须在 canonical candidate 产生前阻塞；
2. `obligation-analysis`：当前 stage 的全部义务、开放项和禁止项；
3. `option-analysis`：真实 freedom 的可区分候选，或唯一方案的排除证据；
4. `projection-analysis`：选择如何实际进入 canonical 对象；
5. `adversarial-self-review`：主动挑战因果、覆盖、权限、信息、边界和下游消费。

两个候选必须在至少一个 canonical 决策字段上不同，并产生不同代价或下游影响；同义改写不算候选。每个 skill 还必须有专属 SOP、pass/revise/fail anchors、正例类型、边界反例类型和 agentic eval。

### 2.9 公共 completion

每个 top-level `stage-completion.json` 必须包含：

- `schema_version / harness / stage / skill / hld_run_id / status=ready`；
- exact input gate、state before、work order、manifest 和 validation 引用；
- 有序 upstream completion 引用；
- canonical artifact 角色与引用；
- owner implementation snapshot；
- return binding；
- `ready_capabilities[]`；
- `next_allowed_stage`。

Completion 不得引用包含自身的后态。Harness 验收 completion 后才产生新的 run-state。

### 2.10 Artifact role 注册表

下游不得按文件名搜索输入，只能从当前 completion 或同一复合 workspace manifest 解析以下固定 role：

| Producer | Artifact role | 固定文件 |
| --- | --- | --- |
| HB0 | `control_baseline` | `hld-control-baseline.json` |
| HB0 | `source_index` | `hld-source-index.json` |
| HA1 | `narrative_architecture` | `narrative-architecture.json` |
| HS1 | `storyline_choreography` | `storyline-choreography.json` |
| HC1 | `character_arc_placement` | `character-arc-placement.json` |
| HI1 | `narrative_information_architecture` | `narrative-information-architecture.json` |
| HR1 | `rhythm_continuity_architecture` | `rhythm-continuity-architecture.json` |
| HK1 | `key_scene_function_map` | `key-scene-function-map.json` |
| HQ1 | `semantic_review` | `hld-semantic-review.json` |
| HP1 | `novel_hld_package` | `novel-hld-package.json` |
| HP1 | `hld_spec` | `novel-hld-spec.md` |
| HP1 | `cross_index` | `hld-cross-index.json` |
| HP1 | `traceability` | `hld-traceability-matrix.json` |
| HP1 | `lld_handoff` | `lld-handoff.json` |
| HQ2 consumer task | `handoff_consumption_test` | `handoff-consumption-test.json` |
| HQ2 fidelity task | `handoff_fidelity_test` | `handoff-fidelity-test.json` |
| HQ2 | `lld_handoff_acceptance` | `lld-handoff-acceptance.json` |
| HH1-A | `human_review_report` | `hld-human-review-report.json` |
| HH1-B | `presentation_fidelity_review` | `presentation-fidelity-review.json` |
| HH1-C | `human_review_html` | `hld-human-review-report.html` |
| HH1-C | `render_target_registry` | `render-target-registry.json` |
| HF1 | `hld_completion` | `hld-completion.json` |
| HF1 | `final_validation` | `final-validation.json` |

同一包内 role 必须唯一；固定 role 缺失、重复、指向错文件或 hash 不一致时，下游硬准入失败。

### 2.11 Canonical 公共元数据

本文各设计模型所称“治理字段”固定为：

- `schema_version`；
- `skill / stage / hld_run_id / status`；
- `input_gate`；
- `source_artifacts[]`；
- `authority_partition`；
- `design_decisions[]`；
- `derivation_claims[]`；
- `decision_dependencies[]`；
- `open_items[]`；
- `downstream_contract`。

`source_artifacts` 必须与 input gate allowlist 的实际消费子集相等；`design_decisions` 只能含当前 owner 的 ID；`derivation_claims` 必须绑定被声明值的规范 JSON hash；`decision_dependencies` 必须覆盖本 work order 投影给当前 stage 的全部 unresolved source；`open_items` 必须与上游集合相等或记录合法的无损投影关系。Review、assembler、renderer 和 finalizer 不拥有 `design_decisions`，其 schema 不得伪造该字段；HQ1 只能审查 `decision_dependencies`，不能新增处置。

`authority_partition` 的字段形状固定为：

- `source_classifications.mandatory|freedom|must_ask|open`：control binding source IDs，四个集合互斥且并集等于全部 control bindings；
- `source_open_items[]`：`open_item=true` 的 source IDs，必须是全部 control bindings 的子集，可与 `must_ask` 等主分类重叠；
- `source_authority_classes.author_locked|autonomous_owned|downstream_freedom|author_open`：原上游 authority class 集合，不得改名；四个集合互斥且并集等于全部 control bindings；
- `hld_ownership.source_projection|hld_owned|preserved_open|lld_freedom`：当前 canonical element IDs，四个集合互斥且并集等于当前模型全部 canonical element IDs；HB0 尚无 HLD 元素时四个集合均为空。

前三项是来源控制面，第四项是 HLD 处理结果。任何 skill 把 source ID 直接塞进 `hld_ownership`、把 canonical element ID 塞进来源集合，或用一个集合覆盖另一个集合，都必须 fail closed。

### 2.12 Author question 与现实事实重入

#### Stage-scoped decision dependency assessment

HB0 只能在 `unresolved_register[]` 中无损登记 `must_ask` 和 `open_item=true` 的 source control。Harness 做确定性集合投影：non-quality unresolved source 投影给 SOURCE_ACCESS_MATRIX 允许的每个 HA1–HK1；quality-domain unresolved source 只投影给 HQ1。不得再按语义删选，且每个 unresolved source 至少有一个 assessment owner；HB0 和 Harness 都不得判断某项是否影响当前 HLD。每个 HA1–HK1 在形成候选设计之前、HQ1 在形成 review verdict 之前，必须对当前 work order 投影的每一项生成一个 `HDD-`：

- `id / source_id / owner_stage / affected_obligation_ids[]`；
- `disposition=not_needed_for_current_stage|conditional_structure_preserves_open|required_now|resolved_by_external_author_event`；
- `object_evidence_refs[] / rationale_anchor / downstream_effect`；
- `resolution_ref`，仅最后一种 disposition 非空。

HDD ID 必须确定性等于 `HDD-<owner_stage>-<source_id>`，其中两个占位符逐字使用注册 stage code 与 baseline source ID；同一 source 在不同 stage 的 assessment 因此不会碰撞，重跑同一 stage 也不会产生新身份。

固定行为：

1. `not_needed_for_current_stage`：只表示当前 stage 不依赖答案，不得宣称整个 HLD 永远不需要；
2. `conditional_structure_preserves_open`：当前 canonical 只能建立不选分支的条件结构，并继续携带 open item；
3. `required_now`：当前 work order 在产生 candidate canonical 前结束，输出 `blocked/author_required`；`gate-data.json` 必须包含对应 HDD 值；
4. `resolved_by_external_author_event`：必须绑定当前有效的 `author-resolution.json`，不得引用聊天或最终 author decision；
5. 同一 unresolved source 可被多个设计 stage 分别评估；最早出现 `required_now` 的 stage 成为本次问题 owner，后续 stage 不得提前代答；HQ1 的 quality HDD 只裁决审查标准是否需要作者解释，不能产生或覆盖故事事实；
6. HQ1 必须检查：每个实际消费 non-quality unresolved source 的设计 stage 都有 HDD，自己的 quality projection 也有 HDD，所有 `open_item=true` 均仍在 open items 或有外部 resolution；HP1 只做集合聚合，不新增语义判断。

HLD 层的 `not_needed_for_current_hld` 不是任何单一 skill 的判断字段。只有 HP1 在 HQ1 pass 后，才能对“全部被投影 stage 均为 `not_needed_for_current_stage` 且没有 `required_now`”的 source 生成确定性聚合状态。这样 HB0、Harness 和 assembler 都不会越权作语义判断。

中途作者问题使用独立事务：router 生成 `author-question.json` → 外部作者门生成 `author-answer-event.json` → harness 生成 `author-resolution.json`，状态进入 `waiting_author_answer`。Question 公共字段必须绑定 run/revision、`question_kind`、唯一 owner、提问原文、允许回答范围和 resume stage；answer 必须绑定 question hash、外部 event sequence 和作者原文；resolution 必须绑定 question/answer hash、resolution kind、返回目标和新 revision。`source_resolution` 另含分类结论，`revision_retarget` 另含旧／新 target binding 和 request-meaning hash。

- `question_kind=source_resolution`：用于 `required_now`，条件字段为 source control、HDD、受影响 decision/obligation IDs；
- `question_kind=revision_retarget`：用于 catalog 2.17 的 superseded target group，条件字段为 revision plan/state、group ID、原 target、使其失效的 lineage 变化和当前允许的新 target IDs；不得携带或改写 source authority classification。

- `hld_local_resolution`：只解释现有 must-ask；同 stage return-resolution；
- `revision_target_resolution`：只重新绑定 superseded target group；返回 revision plan，不进入内容 skill；
- `conception_authority_change`：退出当前 HLD，返回构思权威 owner，重新批准和 preparation 后新建 HLD run。

不得用最终 `author-decision.json` 回答中途问题，也不得由 Agent 代答。`source_resolution` 的 `hld_local_resolution` 恢复同一 HLD run 的指定 stage；`revision_retarget` 只允许在新 plan-state 中增加对应 group 的 retarget binding，不回写 immutable plan，也不得改变作者请求的意义。`conception_authority_change` 终止当前 run，旧 completion 全部 stale，待构思重新批准并重新 preparation 后建立新 run。

若 HLD 发现构思未登记的结构性现实事实依赖，router 生成 `reality-dependency-request.json`，包含 claim、为什么属于外部事实而非 HLD 连续性、受影响对象、所需证据深度、构思事实研究 owner 和返回条件；当前 HLD 终止。事实进入构思权威包并重新批准、重新 preparation 后，只能新建 HLD run。HLD 不自行联网研究。纯 HLD 连续性错误仍返回本链 owner。

### 2.13 Source access matrix

每个 stage 的原始 baseline source 权限由 harness manifest 中以下固定 `SOURCE_ACCESS_MATRIX` 按 domain 投影；`quality` 只用于审查，任何 stage 都不得把它当作故事事实。未列出的 stage 禁止读取原始 source，只能读取契约指定的上游 ready 包。

| Stage | 允许的原始 source domain |
| --- | --- |
| HB0 | `intent,storylines,world,environments,events,characters,narrative,quality,cross-domain`（只索引，不解释） |
| HA1 | `intent,storylines,world,environments,events,characters,narrative,cross-domain` |
| HS1 | `intent,storylines,world,environments,events,characters,narrative,cross-domain` |
| HC1 | `intent,storylines,world,environments,events,characters,narrative,cross-domain` |
| HI1 | `intent,storylines,world,environments,events,characters,narrative,cross-domain` |
| HR1 | `intent,storylines,world,environments,events,characters,narrative,cross-domain` |
| HK1 | `intent,storylines,world,environments,events,characters,narrative,cross-domain` |
| HQ1 | `intent,storylines,world,environments,events,characters,narrative,quality,cross-domain` |
| HP1、HQ2、HH1-A/B/C、HF1 | 无；只读各自 input contract 指定的包 |

同一 domain 内仍只允许读取 HB0 `hld-source-index.json` 明确列入、且 `hld_assignment` 分配给 HLD 的 source ID。HB0 只执行矩阵，不作语义授权判断。矩阵变化属于 harness 版本变更，会使旧 completion 失去当前资格。

### 2.14 权威继承与 HLD 归属分层

禁止在同一个 `authority_class` 字段中混用上游权威与 HLD 决定归属。所有 canonical 元素必须分别记录：

- `source_authority_refs[]`：引用 HB0 control binding；每个引用保留上游 `classification=mandatory|freedom|must_ask|open`、独立 `open_item` 标志、`authority_class=author_locked|autonomous_owned|downstream_freedom|author_open` 和原值 hash，不得改写；
- `ownership_class=source_projection|hld_owned|preserved_open|lld_freedom`：只描述该 canonical 元素在 HLD／LLD 中的处理方式；
- `resolution_ref`：只有已由外部 author-resolution 解决的 `must_ask` 才允许出现，否则为 `null`。

固定映射：

| 上游主分类／状态 | HLD ownership_class | 硬规则 |
| --- | --- | --- |
| `mandatory` | `source_projection` | 只定位和编排，不改变值 |
| `freedom` 且 HLD 为完成本阶段必须决定 | `hld_owned` | 必须有当前 owner 的 design decision、候选和 derivation |
| `freedom` 且 HLD 无需决定、明确可延至 LLD | `lld_freedom` | 必须有 `deferred_to_lld` disposition、下游验收边界，并证明不留下 HLD 结构缺口 |
| `open` | `preserved_open` | 不得选择分支 |
| 未解决 `must_ask` 且当前 HLD 依赖答案 | 不产生 canonical 决定 | 必须进入 author-question transaction 并阻塞受影响 stage |
| 未解决 `must_ask` 且当前 HLD 不依赖答案 | `preserved_open` | 原样携带，不能代答 |
| 已解决 `must_ask` | `source_projection` | 必须绑定外部 resolution，不能伪装为 HLD 自主决定 |

`open_item=true` 必须持续进入 `open_items[]`，直至外部 resolution 明确关闭；它可以与 `must_ask` 重叠。`authority_class` 必须原样保留，但不是本表的直接映射键：例如上游 `downstream_freedom` 表示相对构思阶段的下游自由，进入 HLD baseline 后通常表现为 `classification=freedom`，不得自动映射为 `lld_freedom`。`authority_partition` 始终保存原上游分类与标志；`ownership_class` 不得反向覆盖它。

### 2.15 Review verdict 与 stage result 代数

HQ1、HQ2 和 HH1-B 的 canonical verdict 使用 `pass|revise|fail`；harness 只消费 `stage-result.result=ready|revise|blocked|runtime_error`。固定转换为：

| Canonical verdict | defect_origin | Stage result | Harness 动作 |
| --- | --- | --- | --- |
| `pass` | `none` | `ready` | 重验 completion 后前进 |
| `revise` | `reviewer_local` | `revise/local_candidate` | 同 reviewer 新 revision |
| `fail` | `upstream_content` | `blocked/upstream_defect` | router 按 affected IDs 和 owner matrix 定向返回 |
| `fail` | `author_required` | `blocked/author_required` | router 开启 author-question transaction |
| `fail` | `reality_dependency` | `blocked/reality_dependency` | router 生成 reality request 并退出当前 run |
| 无 canonical verdict | `runtime` | `runtime_error` | 保持 current state，记录运行错误 |

Reviewer 只能提交 defect origin 的证据和 affected IDs，不能指定最终 target owner。任何未落入本表的组合均 fail closed。

对 HQ2、HH1 复合 stage，内部 task 的 `ready|revise|blocked|runtime_error` 只是内部结果，不能触发顶层前进、返工、停止或生成顶层 completion；只有 2.16 publisher 重验已完成内部结果和“后续 task 未被签发”条件后，才能发布该复合 stage 的顶层 `stage-result.json`。

### 2.16 复合 stage 的确定性 publisher

HQ2 和 HH1 是复合 stage。其内部 skill 包不得自行生成 top-level completion；由 harness core 的 `composite-stage-publisher` 确定性发布。Publisher 不是第15个技能，不作语义判断，只执行固定 profile：

1. 接收 harness work order、state before、内部包 manifests/results、规定的上游 completions 和固定 publish profile；
2. 重验内部 task identity、allowlist、hash、verdict 代数、文件集合和跨包 binding；
3. 只复制字节或生成索引、validation、manifest、completion 与 `stage-result.json`，不得生成、摘要或改写内容；
4. 任一内部包非 pass、stale、越界读取或 hash 不一致时不得发布 completion，只输出标准 non-ready result；
5. Completion 由 publisher 生成，run-state 仍只能由 harness router 在接纳 stage result 后生成。

HQ2 publish profile 精确输入为密封 consumption test、密封 fidelity test、HP1 completion 与 HB0 run binding；发布内容包精确包含 `lld-handoff-acceptance.json / q2-publish-execution.json / validation.json / package-manifest.json / stage-completion.json`，并在包外生成唯一 top-level `stage-result.json` 信封。

HH1 publish profile 精确输入为 HH1-A/B/C 密封内部包、HP1 completion 和 HQ2 completion；发布内容包精确包含 `hld-human-review-report.json / presentation-fidelity-review.json / hld-human-review-report.html / render-target-registry.json / hh1-publish-execution.json / validation.json / package-manifest.json / stage-completion.json`，并在包外生成唯一 top-level `stage-result.json` 信封。前四项只能复制已封存字节。

复合 stage non-ready publish profile 也必须精确：

- HQ2：输入为按执行顺序出现的第一个 non-ready internal result、此前已密封 internal pass（可为空）、HP1 completion、HB0 binding，以及证明后续 internal task 未签发的 workspace state；内容包精确包含 `source-internal-package/** / source-internal-stage-result.json / q2-nonready-publish-execution.json / validation.json / result-manifest.json`，包外输出对应 top-level `revise|blocked|runtime_error` stage result；
- HH1：输入为按 A→B→C 顺序出现的第一个 non-ready internal result、此前已密封 internal pass（可为空）、HP1/HQ2 completions，以及证明后续 internal task 未签发的 workspace state；内容包精确包含 `source-internal-package/** / source-internal-stage-result.json / hh1-nonready-publish-execution.json / validation.json / result-manifest.json`，包外输出对应 top-level non-ready stage result；
- Publisher 只能无损复制 internal defect origin、affected IDs、revision/gate/runtime references，并按 2.15 映射顶层结果；不得补 finding、改变 verdict 或要求缺失的后续 internal task。

`source-internal-package/**` 必须与内部 result manifest 的文件集合和字节逐一相等；`source-internal-stage-result.json` 必须与内部结果信封字节相等。Top-level condition refs 只能指向这些副本，`result-manifest.json` 必须覆盖全部副本和 publisher 证据。这样 top-level result 不跨 workspace 引用，也不会伪造内部 candidate、finding 或 gate data。

### 2.17 Revision plan、定向 return 与耗尽

任何 `revise/local_candidate`、`blocked/upstream_defect` 中的 finding/affected-ID 集合，都由 harness router 转换为唯一、不可变的 `revision-plan.json`。最终作者 `revision_targets[]` 先执行本节算法第1步：含 `conception_authority` 时直接 conception reentry，否则才生成 plan。`blocked/author_required` 和 `blocked/reality_dependency` 分别进入 author-question 与 reality reentry，不创建 revision plan。Skill 和 finalizer 不得直接生成 return。Plan 的必需字段：

- `revision_plan_id / hld_run_id / source_result_ref / source_event_ref`；`source_result_ref` 永远绑定触发 plan 的 stage result，`source_event_ref` 仅作者返工时非空且必须与该 result 的 author event binding 相等；
- `target_groups[]`，按固定 stage 拓扑从早到晚排序；
- `invalidated_suffix / author_reapproval_required`；
- `root_cause_fingerprints[]`。

Plan 的运行状态不得回写进 plan 本体。Router 每次转换都生成不可覆盖的 `revision-plan-state/revision-NNN.json`，必需字段为 `revision_plan_ref / previous_plan_state_ref / active_group_id / pending_group_ids[] / resolved_group_ids[] / superseded_group_ids[] / retarget_bindings[] / plan_status / transition_event_ref`；四个 group 集合互斥且并集等于 plan 的全部 group IDs。每个 retarget binding 必须绑定 group、原 target hash、作者 resolution、新 target ID 和不变的 request-meaning hash。HLD run-state 同时绑定 current `revision_plan_ref` 和 `revision_plan_state_ref`。

每个 immutable target group 必须有 `group_id / exact_owner / target_stage / resume_stage / target_kind / affected_ids[] / requirements[] / source_target_refs[] / invalidated_suffix / completion_condition`；运行状态只存在于 revision-plan-state。`target_kind` 只允许：

- `hld_content`：按 canonical/source ID 的注册 producer 路由；
- `report_content`：路由 HH1-A；
- `presentation_review`：只用于 HH1-B 自身审查执行缺陷；
- `render_expression`：路由 HH1-C；
- `conception_authority`：退出当前 HLD，不能进入本地 revision plan。

固定算法：

1. Router 先验证每个 target ID 可解析。若任一作者 target 为 `conception_authority`，整个当前 HLD 退出到 conception reentry，并完整携带该 author event；不得在过时 baseline 上继续其他本地 target group。否则每个 source finding 或 author target 独立成为一个 group，由 affected/target ID 唯一求 owner，再按 stage 拓扑与原 source order 排序；同 owner 的多个 target 也不得由 router 语义合并。若 owner skill 发现两项要求冲突，只能提交 `blocked/author_required` 证据；router 不猜兼容性；
2. 只有拓扑最早的 pending group 可成为 active return；同一时刻仍只有一个 active return，但其余 group 必须持久化在 current revision-plan-state 中；
3. 当前 owner 只读取 active group，不得修改其他 owner 的要求；其完成条件通过后，router 将该组标为 resolved，并激活下一组；
4. 从最早 owner 起按正常拓扑重跑。当流程到达下一个 pending group 的 owner 时，该 stage 以 `mode=return_resolution` 消费对应 group；不得把下游要求交给上游 skill；
5. 上游修改使后续 target ID 消失或改变含义时，该组变为 `superseded`，router 必须生成重新定位问题并等待外部确认，不能静默删除；
6. Revision plan 的 `invalidated_suffix` 由拓扑最早 group 确定；所有 group resolved 后，只重跑该 suffix 内的设计／审查／publisher，但最终 HH1 current binding、作者门和 HF1 必须重新通过。仅 `render_expression` 时 HP1/HQ2 可保持 current；若最早 group 为 HS1，则 HS1 及 HQ1/HP1/HQ2/HH1 全部重跑。旧 author decision 只作为 revision source event 保留，不再具有批准效力；
7. Review findings 的多 owner 返工使用同一事务。后续 HQ1 可关闭已解决 finding，但不得丢失 plan 中尚未到达的 group。

自动 local revision 的 root-cause fingerprint 固定为以下规范 JSON 的 SHA-256：`{defect_origin,exact_owner,violated_contract,sorted_affected_ids,correction_condition_hash}`。字段排序、字符串正规化和数组排序由 router 完成；证据措辞、轮次和时间戳不得进入 fingerprint。`root_cause_fingerprints[]` 只覆盖自动 local/upstream groups；纯作者 target plan 允许为空。作者主动 revision target 不计入自动耗尽，但仍必须进入 revision plan。相同 owner + fingerprint 完成两次 local revision 后再次出现，router 才进入 exhausted blocked 状态。

## 3. HB0：`novel-hld-baseline-admitter`

### 3.1 定义

类型：`script`。触发：一个正式 development baseline 需要进入新的 HLD run。

它是准入和无损控制面封装器，不是 HLD 设计者。

### 3.2 目标与职责

- 重新运行 preparation validator；
- 验证 baseline 四文件 ready 包及其不可变 conception source；
- 验证项目、版本、release、run lineage、hash 和 HLD assignment；
- 解析全部 control binding 和六域 inventory locator；
- 按权威 schema 识别真实对象类型，建立只读语义索引；
- 冻结 authority partition、unresolved register、source allowlist 和 HLD revision 0。

### 3.3 边界与约束

- 不总结、改写或解释故事内容；
- 不决定结构、章节、故事线位置、人物弧线、POV 或关键场景；
- 不把 inventory 条目数解释为语义对象数量；
- 不修复 baseline 或 conception；
- 不自行判断 source 可由哪些 stage 读取；只执行固定 `SOURCE_ACCESS_MATRIX`；
- preparation validator 非零退出时必须 blocked。

### 3.4 输入契约

精确 upstream：`[]`。Harness 初始状态和 HB0 work order 是控制输入，不是上游 stage completion。

唯一调用文件：`hld-run-request.json`。必需字段：

- `schema_version=1.0`；
- `harness=novel-hld-autonomous`；
- `project_id / hld_run_id / hld_version`；
- `preparation_request_path`；
- `baseline_package_dir`；
- `output_root`；
- `author_gate=required`；
- `replace=false`（生产 V1）。

精确文件输入：

- preparation request；
- `development-baseline.json`；
- `development-baseline.md`；
- `baseline-validation.json`；
- `package-manifest.json`；
- preparation skill 兼容锁、schema 和正式 validator；
- request 中 source root 下被 baseline 引用的文件。

硬准入：四文件边界精确、全部 hash 当前、baseline `status=ready`、项目相等、HLD assignment 完整、输出与输入根目录完全分离。

### 3.5 输出契约

Canonical 输出：

1. `hld-control-baseline.json`
   - `source_baseline`；
   - `source_release / lineage / admission_verdicts`；
   - `authority_partition`，严格使用 2.11 的四层字段形状；
   - `control_registry[]`；
   - `unresolved_register[]`；
   - `hld_assignment / change_policy / prohibitions`。
2. `hld-source-index.json`
   - 每项包含 `source_id / domain / object_type / source / locator / value_sha256 / allowed_stages`；`allowed_stages` 必须与固定 access matrix 的确定性投影相等；
   - 对象集合按真实 schema 类型组织，不按 inventory 分组名猜测。
包内另含 execution、validation、manifest 和 HB0 completion。Harness 接纳 HB0 completion 后生成 `revision-001`；HB0 只引用执行前的 `revision-000`，不得输出 run-state。

### 3.6 交付标准与消费者

Ready：全部 baseline binding 和 inventory locator 可无损解析，分类集合互斥，未产生任何 HLD 决定。唯一消费者：HA1 直接消费；后续阶段通过 HB0 completion 继承控制面。失败 owner：HB0 自身的封装错误或 preparation/upstream owner 的来源错误。

## 4. HA1：`novel-hld-narrative-architect`

### 4.1 定义

类型：`thinking`。触发：HB0 ready，需要建立全链唯一的宏观叙事坐标系。

### 4.2 目标与职责

- 选择与当前故事匹配的总体结构形态；
- 定义结构阶段、叙事单元层级和章节壳；
- 定义每个单元的进入状态、核心任务、必须变化、退出状态和承接条件；
- 将权威重大事件、转折、高潮和结局边界落到结构锚点；
- 定义结构弹性、章节密度和篇幅区间。

### 4.3 边界与约束

- 不预设固定三幕、固定章数或固定比例；
- 不改写故事线内容、事件因果、人物弧线或结局；
- 不决定具体 POV 和信息释放；
- 不写关键场景动作、对白、画面或感官；
- 结构选择必须记录候选、依据、代价和可逆性。

### 4.4 输入契约

精确 upstream：`[HB0]`。

必需文件：work order、input gate、state before、HB0 completion/manifest/validation、`hld-control-baseline.json`、`hld-source-index.json`，以及 allowlist 中结构、故事线、事件、叙述控制的权威源值。

必需输入字段：`hld_assignment`、全部 mandatory/open control、真实故事线对象、重大事件、叙述契约、目标篇幅或其开放状态。

硬准入：HB0 current；无 active return，或 active revision group 精确指向 HA1；HB0 unresolved register 与当前 work order 的 unresolved projection 完整。HDD disposition 不是准入前置答案：HA1 必须按 2.12 在产生结构候选之前逐项评估，若出现 `required_now` 则直接 blocked，不得形成 candidate canonical。

### 4.5 输出契约

Canonical：`narrative-architecture.json`。必需字段：

- `architecture_choice`；
- `structural_phases[]`；
- `narrative_units[]`；
- `chapter_shells[]`；
- `turning_point_anchors[]`；
- `entry_exit_state_contracts[]`；
- `scale_and_flexibility`；
- `downstream_obligations`；
- `authority_partition / design_decisions / derivation_claims / open_items`。

每个 `HNU-` 必须有 parent、sequence、purpose、entry state、required change、exit state 和 source anchors。每个 `HCH-` 必须属于一个 HNU，且不含场景细节。

### 4.6 执行与语义判定

依次执行：盘点结构义务 → 形成至少两个真实结构候选或唯一方案排除证据 → 用重大事件、故事线容量和结局边界做压力测试 → 选择并投影单元／章节 → 反证是否存在无变化阶段、容器不足或模板强套。

- `pass`：结构从开端到结局连续，所有重大义务有位置且无下游猜测；
- `revise`：仅当前结构组织可局部调整，不需改变故事事实；
- `fail`：需要新增／改变主要事实，或作者问题必须先裁决；由 2.15 的映射规则生成对应 blocked stage result，不在本技能内混写控制状态。

### 4.7 交付标准与消费者

Ready：结构树无环且顺序唯一；开端至结局边界连续；每阶段有实质变化；所有权威重大锚点有位置；不含 LLD 字段。直接消费者：HS1。间接消费者：HC1–HK1、HQ1、HP1。问题唯一 owner：HA1。

## 5. HS1：`novel-hld-storyline-choreographer`

### 5.1 定义

类型：`thinking`。触发：HA1 ready，需要把权威故事线编排进唯一结构坐标系。

### 5.2 目标与职责

- 建立语义故事线 register；
- 区分主干、支线、背景线、人物线、情感线、主题线和可选旋律线；
- 将每条线分段放入 HA1 单元；
- 定义线的进入、并行、交叉、接力、汇合、退出和回收；
- 建立线间因果、信息、情绪和主题关系；
- 映射既有事件在线中的作用；
- 证明多线共同还原故事主体。

### 5.3 边界与约束

- 不新增故事线事实或主要事件；
- 不用 baseline inventory 数量冒充故事线数量；
- 不强制展开可选旋律线；
- 不设计人物内在弧线、POV 或节奏曲线；
- 不允许一条线无来源地消失或回收。

### 5.4 输入契约

精确 upstream：`[HB0,HA1]`。

必需文件：公共 gate 文件、HB0 控制面、HA1 completion/manifest/validation、`narrative-architecture.json`，以及 allowlist 中故事线、事件和主题源值。

必需 HA1 字段：`structural_phases / narrative_units / chapter_shells / turning_point_anchors / entry_exit_state_contracts`。

硬准入：HA1 current 且 ready；叙事单元 ID 唯一；实际故事线对象可由 source index 无损识别。

### 5.5 输出契约

Canonical：`storyline-choreography.json`。必需字段：

- `semantic_storyline_register[]`；
- `storyline_segments[]`；
- `unit_storyline_matrix[]`；
- `storyline_connections[]`；
- `convergence_and_split_points[]`；
- `event_storyline_placement[]`；
- `activation_disposition[]`；
- `subject_reconstruction_test`；
- 治理字段。

每条权威线必须处于 `placed / background-carried / optional-not-activated / preserved-open` 之一，并包含授权依据。每个 `HTS-` 必须引用有效 HNU/HCH、源故事线和进入／退出状态。

### 5.6 执行与语义判定

依次执行：按权威对象建立语义故事线集合 → 逐线验证建立／发展／转折／回收 → 比较至少两种真实编排方案 → 检查线间连接的因果与必要性 → 用 `subject_reconstruction_test` 反证是否仍能完整还原主体。

- `pass`：强制线全覆盖，连接必要且主体可重建；
- `revise`：仅段落位置、切线或连接方式需本地调整；
- `fail`：故事线事实本身缺失／冲突或需要作者改变构思；由 2.15 的映射规则生成对应 blocked stage result。

### 5.7 交付标准与消费者

Ready：主干连续；所有强制线有建立、发展、转折和回收或合法开放；连接无环形自证；所有事件位置来自权威事件。直接消费者：HC1。间接消费者：HI1–HK1、HQ1、HP1。问题唯一 owner：HS1。

## 6. HC1：`novel-hld-character-arc-placer`

### 6.1 定义

类型：`thinking`。触发：故事线编排 ready，需要把既有人物弧线和关系变化落到结构与事件。

### 6.2 目标与职责

- 建立核心／重要人物参与 register；
- 定义目标、认知、价值、关系和责任的阶段状态；
- 将压力、选择、代价和结果绑定既有事件及故事线连接；
- 定义人物在各线中的职责和合法缺席；
- 映射关系双方的变化落点；
- 校验能力、权限、信息和行动匹配。

### 6.3 边界与约束

- 不补写人物外貌、生活背景、社交圈或新关系；
- 不创建新主要人物；
- 不改变构思中的动机、感情或关系事实；
- 不写逐场景动作、对白或行为标记；
- 人物变化必须由已存在的压力和选择驱动。

### 6.4 输入契约

精确 upstream：`[HB0,HA1,HS1]`。

必需文件：公共 gate 文件、HB0 控制面、HA1/HS1 completions 与 canonical 模型，以及 allowlist 中人物、关系、事件源值。

必需上游字段：HA1 全部结构坐标；HS1 的 `storyline_segments / unit_storyline_matrix / storyline_connections / event_storyline_placement`。

硬准入：所有人物和关系 ID 可解析；所有强制故事线有合法单元；不存在待 HC1 自行补齐的主要人物槽。

### 6.5 输出契约

Canonical：`character-arc-placement.json`。必需字段：

- `character_participation_register[]`；
- `arc_state_models[]`；
- `arc_steps[]`；
- `relationship_steps[]`；
- `choice_cost_consequence_links[]`；
- `event_character_alignment[]`；
- `capability_information_permission_checks[]`；
- 治理字段。

每个核心人物必须形成起点—压力—选择—代价—结果链。每个 HAS/HRS 必须引用有效人物、事件、故事线段和叙事单元。

### 6.6 执行与语义判定

依次执行：逐人物冻结构思起点和终点 → 盘点各线责任 → 比较变化落位方案 → 建立压力／选择／代价／结果 → 反证能力、权限、信息、关系和缺席合理性。

- `pass`：核心人物变化连续、事件驱动且关键结果有承担者；
- `revise`：仅弧线落点或参与分配需本地调整；
- `fail`：必须新增人物事实、感情、能力、信息或关系才能成立；由 2.15 的映射规则生成对应 blocked stage result。

### 6.7 交付标准与消费者

Ready：核心人物弧线完整；改变不是作者强加的跳变；关键结果有承担者；能力、权限、信息足以支持行动；无未授权人物事实。直接消费者：HI1。间接消费者：HR1、HK1、HQ1、HP1。问题唯一 owner：HC1。

## 7. HI1：`novel-hld-information-architect`

### 7.1 定义

类型：`thinking`。触发：结构、故事线和人物变化 ready，需要定义 POV、知识和悬念控制。

### 7.2 目标与职责

- 定义 POV、人称、权限和切换层级；
- 为叙事单元定义 POV 归属／候选／禁止归属；
- 管理角色知识状态和读者知识状态；
- 建立 setup—probe—reveal—payoff 链；
- 定义隐瞒、暗示、误判、推断和回看验证规则；
- 应用作者叙述契约并保留开放问题。

### 7.3 边界与约束

- 不写线索文本、记忆内容、对白或呈现句；
- 不泄露 POV 无权感知的信息；
- 不通过信息架构裁决作者开放结局；
- 不改变人物实际知道的权威事实，只安排合法获知过程；
- POV 决定保持在单元／关键功能层，不进入逐段执行。

### 7.4 输入契约

精确 upstream：`[HB0,HA1,HS1,HC1]`。

必需文件：公共 gate 文件、HB0 控制面、HA1/HS1/HC1 completions 与 canonical 模型，以及 narrative controls。

必需字段：叙事单元、故事线段与连接、人物参与、arc steps、event-character alignment、人物信息权限检查。

硬准入：每个 POV 候选均是有效人物或权威允许的非人物视角；知识来源可定位；作者开放项状态明确。

### 7.5 输出契约

Canonical：`narrative-information-architecture.json`。必需字段：

- `pov_policy`；
- `unit_pov_assignments[]`；
- `knowledge_states[]`；
- `reader_information_states[]`；
- `suspense_chains[]`；
- `information_nodes[]`；
- `reveal_payoff_matrix[]`；
- `concealment_and_inference_rules[]`；
- 治理字段。

每个 HIN 必须有来源、持有人、读者状态、进入方式、允许最早位置和禁止泄露位置。每个 HSP 必须区分 setup、probe、reveal、payoff 及允许保持开放的终点。

### 7.6 执行与语义判定

依次执行：冻结叙述契约和初始知识状态 → 逐信息节点验证来源与持有人 → 比较 POV／揭示安排 → 闭合 setup—probe—reveal—payoff → 反证越权、故意失忆和开放项被裁决。

- `pass`：知识变化有来源、POV 合法、必须回收链闭合；
- `revise`：仅 POV 单元或信息时机需本地调整；
- `fail`：需要改写人物已知事实、叙述边界或作者开放答案；由 2.15 的映射规则生成对应 blocked stage result。

### 7.7 交付标准与消费者

Ready：知识变化均有来源；必须揭示有 setup；必须回收有 payoff；POV 不越权；悬念不靠作者故意隐瞒 POV 已知且应自然想到的信息。直接消费者：HR1。间接消费者：HK1、HQ1、HP1。问题唯一 owner：HI1。

## 8. HR1：`novel-hld-rhythm-continuity-architect`

### 8.1 定义

类型：`thinking`。触发：结构、编排、弧线和信息架构 ready，需要形成可发生、可阅读的时空与节奏方案。

### 8.2 目标与职责

- 区分故事时间、叙事顺序和角色感知时间；
- 安排顺叙、回忆、插叙、并行和时间跳跃；
- 定义单元时间跨度、压缩／展开和同步；
- 验证环境准入、资源、权限、距离和迁移时间；
- 定义节奏、张力、情绪压力和恢复窗口；
- 协调多线切换、章节负载和信息密度；
- 维护人物位置、知识、资源、权限、关系和状态连续。

### 8.3 边界与约束

- 不新增环境或摆设、感官与过场动作；
- 不改写事件因果或故事线顺序义务；
- 不用精确字数制造虚假确定性；
- 张力不得机械等距或单调上升；
- 回忆、插叙和切线必须有进入、退出与状态保持规则。

### 8.4 输入契约

精确 upstream：`[HB0,HA1,HS1,HC1,HI1]`。

必需文件：公共 gate 文件、HB0 控制面、HA1–HI1 completions 与 canonical 模型，以及权威环境、事件和世界机制源值。

必需字段：结构顺序、故事线并行／汇合、事件位置、人物状态、POV、知识状态、悬念节点。

硬准入：所有环境和迁移端点有效；事件先决条件可识别；没有等待 HR1 自行补写的时间或空间事实。

### 8.5 输出契约

Canonical：`rhythm-continuity-architecture.json`。必需字段：

- `story_time_model`；
- `narrative_order_map[]`；
- `unit_duration_density[]`；
- `space_transition_map[]`；
- `parallel_synchronization[]`；
- `pacing_curve[]`；
- `tension_curve[]`；
- `recovery_windows[]`；
- `continuity_ledger[]`；
- 治理字段。

每个连续性条目必须声明前态、变化来源、后态、保持到的单元和解除条件。

### 8.6 执行与语义判定

依次执行：建立故事时间与叙事顺序 → 逐状态验证位置／知识／资源／权限／关系 → 比较节奏和切线方案 → 校验环境迁移与同步 → 反证时间倒置、状态瞬移、机械张力和无恢复累积。

- `pass`：时空和状态连续，节奏有累积、转折与恢复；
- `revise`：仅顺序、密度、切线或恢复窗口需本地调整；
- `fail`：权威事件时间、环境能力或世界机制本身不足／冲突；由 2.15 的映射规则生成对应 blocked stage result。

### 8.7 交付标准与消费者

Ready：无时间倒置、无不可能迁移、无状态瞬移；高潮前有充分累积；恢复窗口不消解核心压力；叙事顺序不破坏知识合法性。直接消费者：HK1。间接消费者：HQ1、HP1。问题唯一 owner：HR1。

## 9. HK1：`novel-hld-key-scene-function-planner`

### 9.1 定义

类型：`thinking`。触发：HA1–HR1 ready，需要综合为 LLD 可展开的最小充分关键场景功能集合。

### 9.2 目标与职责

- 为结构转折、线间连接、人物选择、揭示和高潮定义关键功能；
- 合并兼容功能、拆分过载或冲突功能；
- 定义前置、主要功能、必须变化、退出和验收；
- 建立与章节、线、事件、人物、环境、POV、知识和张力的索引；
- 定义禁止解法和 LLD freedom；
- 验证关键矛盾不靠一句话、巧合、越权或工具人解决。

### 9.3 边界与约束

- 不写场景动作顺序、对白、画面、感官、物件或记忆片段；
- 不把每个普通过场都提升为关键功能；
- 不用固定 HKF 数量凑完整性；
- 不修改 HA1–HR1；发现冲突只能 return；
- 一个 HKF 必须有唯一主要功能，次要功能不得遮蔽它。

### 9.4 输入契约

精确 upstream：`[HB0,HA1,HS1,HC1,HI1,HR1]`。

必需文件：公共 gate 文件、HB0 控制面、HA1–HR1 completions 和全部 canonical 模型。

必需字段：结构和章节壳、故事线连接、人物关键选择、POV/知识/悬念、时间空间、张力及连续性账本。

硬准入：所有上游 current 且 ready；无 active unresolved conflict；关键义务都可引用稳定 ID。

### 9.5 输出契约

Canonical：`key-scene-function-map.json`。必需字段：

- `key_scene_functions[]`；
- `structural_coverage_matrix[]`；
- `storyline_coverage_matrix[]`；
- `arc_coverage_matrix[]`；
- `information_coverage_matrix[]`；
- `climax_and_payoff_coverage`；
- `lld_work_requirements[]`；
- `lld_freedoms[]`；
- 治理字段。

每个 `HKF-` 必须包含 HCH/HNU、preconditions、trigger、primary function、secondary functions、source IDs、POV constraint、knowledge before/after、required state change、choice/cost/result、tension role、completion criteria、forbidden solutions 和 LLD freedom。

每个 `LWR-` 必须包含一个或多个 HKF、分组依据、进入／退出状态、required elaboration、LLD freedom 和 acceptance criteria。HKF→LWR 的合并／拆分由 HK1 决定；HP1 只允许把 `LWR-<suffix>` 一对一投影为 `LWK-<suffix>`，并保存 `source_lwr_id`。

### 9.6 执行与语义判定

依次执行：穷举全部高层义务 → 为义务形成 HKF 候选 → 比较合并／拆分方案 → 检查功能过载、时空／POV 冲突和禁止解法 → 形成 LWR 分组 → 反证是否存在无消费者义务或 LLD 泄漏。

- `pass`：义务全覆盖、HKF 必要、LWR 可追溯且没有细节越界；
- `revise`：仅 HKF 合并／拆分、位置或 LWR 分组需本地调整；
- `fail`：上游结构、故事线、人物、信息或连续性必须改变；由 2.15 的映射规则生成对应 blocked stage result。

### 9.7 交付标准与消费者

Ready：所有高层义务被覆盖且每个 HKF 有必要性；无重复主功能、职责过载、时空冲突或 LLD 泄漏；`lld_work_requirements[]` 完整覆盖 HKF。直接消费者：HQ1；通过 HQ1 后由 HP1 消费。问题唯一 owner：HK1。

## 10. HQ1：`novel-hld-semantic-reviewer`

### 10.1 定义

类型：`thinking`。触发：HK1 ready，需要独立检查尚未组装的 HLD 意义层质量。

它只产生审查判断，不产生 HLD 内容。

### 10.2 目标与职责

- 重新验证 HB0、HA1–HK1；
- 检查构思继承、结构、多线、人物、信息、时空、节奏、关键功能和主题支撑；
- 检查真实性、因果、权限、资源、状态和开放项；
- 检查便捷解法、巧合、工具人和无承担者结果；
- 识别 HLD/LLD 越界；
- 为 finding 记录 defect origin、affected IDs 和纠正后必须满足的条件；最终 owner 与最小失效后缀由 router 计算。

### 10.3 边界与约束

- 不修改任何模型；
- 不提供替代故事答案；
- 不以审美、市场偏好或固定模板制造 finding；
- 不读取 HP1、HQ2 或人审输出；
- 证据必须引用故事专属对象和值，不能只说字段缺失。

### 10.4 输入契约

精确 upstream：`[HB0,HA1,HS1,HC1,HI1,HR1,HK1]`。

语义 verdict 的唯一 allowlist：HB0 control/source index；2.13 为 HQ1 授权、由 source index 明确列入且在读取时重新验证 locator/value hash 的原始权威对象；以及 HA1–HK1 的 canonical、manifest、completion 和 deterministic validation。`quality` domain 只能提供审查标准，不能提供或覆盖故事事实。禁止读取 generation evidence、execution record、producer self-review、聊天、旧 HLD、人审报告、HP1、HQ2 和预期答案。

Generation evidence 的文件存在性、hash 链和包 profile 由 input gate/validator 在 HQ1 启动前确定性重验；它不得作为 HQ1 判断内容是否合理的解释材料。若后续需要审计生产过程，必须使用独立 audit task，且 audit 结果不能回填或替换首次产品语义 verdict。

硬准入：所有包同一 run、current、hash 连续；review task ID 与所有 producer task ID 不同；quality-domain unresolved projection 与 HB0 register 的确定性子集相等。

### 10.5 输出契约

canonical：`hld-semantic-review.json`。必需字段：

- `domain_reviews[]`；
- `cross_domain_checks[]`；
- `authority_and_open_item_review`；
- `decision_dependencies[]`：只含 HQ1 quality-domain HDD；
- `decision_dependency_review`：逐 source 检查 HDD 覆盖、冲突、required-now 和 resolution；
- `causal_and_reality_challenges[]`；
- `boundary_review`；
- `findings[]`；
- `verdict=pass|revise|fail`；
- `pass_claims[]`：每项包含检查项、证据对象、实际值、通过锚点；
- `coverage_summary`：声明已检查的对象集合及适用／不适用理由。

每个 HFN 必须有 severity、issue、evidence refs、affected IDs、violated contract、`defect_origin=reviewer_local|upstream_content|author_required|reality_dependency` 和 `correction_condition`。不得包含最终 owner、target stage、return 或 invalidated suffix。`severity` 只允许 `blocker|major|minor`：blocker 表示不得继续且可能需要上游／作者处理；major 表示当前 canonical 必须返工；minor 只允许记录会造成下游歧义的局部契约缺陷，纯偏好不得成为 finding。违反硬契约或造成下游猜测即为 actionable；通过与不通过都必须落到故事专属对象及实际值，不得以“字段存在”“整体合理”充当证据。

Ready 内容包严格使用 2.4-A profile；唯一 `stage-result.json` 作为包外 top-level 结果信封引用该 completion。

### 10.6 执行与语义判定

依次执行：先对 quality-domain unresolved projection 形成 HQ1 HDD，`required_now` 时在 review verdict 前进入 author-required blocked → 逐域重新建立 obligation checklist → 对每个 canonical 集合抽取实际对象和值 → 做跨域 ID、状态、因果、权限和开放项检查 → 至少覆盖因果、资源／权限、知识／POV、时间／空间、人物状态、选择—代价—后果、主题支撑和 HLD／LLD 边界八类挑战 → 形成 pass claim 或 finding → 记录 defect origin、affected IDs 和 correction condition。某类不适用时必须给对象证据和理由；不得用总分抵消 blocker。Router 再按 affected ID 的注册 producer 计算唯一 owner 与最小失效后缀。

- `pass`：所有适用检查都有对象级证据与通过锚点，且 findings 为空；
- `revise`：审查包自身证据、覆盖或路由可在 HQ1 本地修正；
- `fail`：任一 HLD canonical 必须修改；review 只记录 defect origin，2.15 与 router 按唯一 owner 生成 blocked result 并返回 HA1–HK1。

### 10.7 交付标准与消费者

Pass：所有适用维度都有可复核的 pass claim，所有必查对象均被覆盖，且无 actionable finding。直接消费者：HP1。发现内容问题时 owner 是 HA1–HK1；漏审、错误证据或错路由问题 owner 才是 HQ1。

## 11. HP1：`novel-hld-package-assembler`

### 11.1 定义

类型：`script`。触发：HQ1 ready，需要形成唯一机器 HLD 和真实 `lld-handoff.json`。

### 11.2 目标与职责

- 重验 HB0、HA1–HK1 和 HQ1；
- 无损收录 canonical 模型；
- 建立跨模型索引和完整追溯；
- 生成确定性 AI 开发规格；
- 将 HK1 的每个 `lld_work_requirement` 一对一投影为 LWK；
- 计算 manifest、validation 和 completion。

### 11.3 边界与约束

- 不新增、删减、合并、拆分或总结成另一套权威事实；
- 不修复上游；
- 不生成 HLD 设计或 LLD 细节；
- 不读取工作区候选，只读 ready completion；
- 相同输入和实现版本必须字节一致；
- LWK 的数量、分组、边界和验收只能来自 HK1 的 `lld_work_requirements[]`。

### 11.4 输入契约

精确 upstream：`[HB0,HA1,HS1,HC1,HI1,HR1,HK1,HQ1]`。

必需文件：公共 gate 文件；上述 current completions、manifests、validations、canonical 模型；HQ1 `hld-semantic-review.json`；HK1 `lld_work_requirements[]`。

硬准入：HQ1 ready 且 finding 为空；全部同一 run；ID、hash、authority partition、open items 和 LWK 来源当前。

### 11.5 输出契约

固定 ready 包：

```text
novel-hld-package.json
canonical-models/
novel-hld-spec.md
hld-cross-index.json
hld-traceability-matrix.json
hld-traceability-matrix.md
lld-handoff.json
assembly-execution.json
validation.json
package-manifest.json
stage-completion.json
```

`novel-hld-package.json` 必须包含所有 stage references、完整 canonical 值或强 hash 引用、authority partition、open items、HLD decisions、`unresolved_dependency_summary[]` 和 package profile。每个 summary 必须有 `source_id / stage_hdd_refs[] / aggregate_disposition / resolution_ref`；`aggregate_disposition` 只允许 `not_needed_for_current_hld|conditionally_preserved|resolved`，不得出现 `required_now`。它由已通过 HQ1 的 HDD 集合确定性计算，不得新增理由或关闭 open item。

`lld-handoff.json` 必须逐项保存 HK1 的 LWR ID，生成同 ID 映射的 LWK，并包含 `status=ready / next_stage=novel-lld`、当前 HLD package、HKF、章节、进入／退出状态、角色、环境、故事线、事件、POV、知识边界、禁止项、LLD required elaboration、LLD freedom 和 acceptance criteria。Handoff 顶层还必须逐值复制 `unresolved_dependency_summary[]`、全部 preserved open items 和 resolution refs，使 LLD 无需读取 HP1 package 猜未决边界；同时复制 HA1 `world_setting_architecture`、HR1 `space_transition_map`，列出全部 baseline 角色 disposition、全部 baseline 环境 coverage 和终局 `terminal_state_refs[]`。角色／环境漏项、城市图不连通、三城以上无转场或终局只剩单一总结句均 fail closed。`set(LWK.source_lwr_id)` 必须与 `set(HK1.lld_work_requirements.id)` 完全相等。

### 11.6 交付标准与消费者

Ready：可无损反解析 HA1–HK1；traceability 从 baseline control 连到 HLD 决定再连到 LWK；Markdown 确定性一致；LWK 与 LWR 一对一、零漂移。直接消费者：HQ2、HH1-A；最终经 HF1 授权后由 LLD harness 消费。问题唯一 owner：HP1。

## 12. HQ2：`novel-hld-lld-readiness-evaluator`

### 12.1 定义

类型：`thinking`，同一 bounded skill 具有两个受 harness 控制且上下文隔离的 mode：`consumer_test` 与 `fidelity_test`。触发：HP1 ready，需要先证明 handoff 单独可消费，再证明它忠实覆盖机器 HLD。

两个 mode 是同一技能的两次独立 task，不增加技能数量，不允许在一个上下文中连续执行。Harness 必须先密封 consumer test，才能签发 fidelity test。

### 12.2 目标与职责

- `consumer_test`：以未来 LLD caller 身份，只用 handoff 重建工作顺序、边界、约束和验收；
- `consumer_test`：追踪全部 LWK、强制故事线、核心人物变化和关键结果，记录任何必须猜测之处；
- `fidelity_test`：在 consumer test 已密封后，对照 HP1 package 检查 handoff 是否遗漏、弱化、增强或错分高层义务；
- 两个 mode 共同验证 hard constraint、preserved open、required elaboration 与 LLD freedom 可区分；
- 只有 handoff 独立可用且与机器 HLD 忠实时，才允许 publisher 形成 HQ2 pass。

### 12.3 边界与约束

- 两个 mode 都不读取 HA1–HK1 独立源包、generation evidence、HQ1 finding、聊天、旧稿、作者报告或预期答案；
- `consumer_test` 严禁读取 `novel-hld-package.json`、`canonical-models/`、`novel-hld-spec.md`、cross-index 和 traceability；
- `fidelity_test` 可以读取 HP1 正式包，但只能比较已经密封的 reconstruction，不得改写、补全或重新执行 consumer test；
- 不补写缺失结构后再判 pass；
- 不以“看起来完整”代替实际重建和追踪；
- 不创建或修改 LLD 蓝图；
- 两个 task ID 必须彼此不同，并与所有 producer、HQ1 不同；任一读取日志越界使整个 HQ2 无效。

### 12.4 输入契约

顶层精确 upstream：`[HB0,HP1]`。

- `consumer_test` 内容 allowlist 精确为：`lld-handoff.json`、handoff schema、HP1 manifest/validation/completion 中不含故事内容的 identity/hash 元数据，以及 HB0 run binding；
- `fidelity_test` 内容 allowlist 精确为：已密封 `handoff-consumption-test.json` 与其 manifest、HP1 `novel-hld-package.json / canonical-models/ / novel-hld-spec.md / cross-index / traceability / lld-handoff.json / manifest / validation / completion`；
- Publisher 输入按 2.16 固定，不拥有额外内容读取权。

硬准入：HP1 完整封存且 current；consumer test 先完成并密封；fidelity work order 绑定 consumer artifact hash；两个 execution record 均证明实际读取集合等于各自 allowlist 的消费子集。

### 12.5 输出契约

`consumer_test` 内部 canonical：`handoff-consumption-test.json`。必需字段：

- `reconstruction_results`；
- `storyline_trace_tests[]`；
- `character_arc_trace_tests[]`；
- `key_function_consumption_tests[]`；
- `constraint_open_elaboration_freedom_test`；
- `missing_guesswork[]`；
- `findings[]`；
- `verdict=pass|revise|fail`。

`fidelity_test` 内部 canonical：`handoff-fidelity-test.json`。必需字段：

- `sealed_consumption_test_ref`；
- `source_lwr_to_lwk_bijection_test`；
- `obligation_coverage_tests[]`；
- `classification_fidelity_tests[]`；
- `omission_enhancement_weakening_findings[]`；
- `verdict=pass|revise|fail`。

每项测试必须记录输入 ID、实际结果、pass/fail 锚点和读取证据。两个内部内容包严格使用 2.4-B profile；每个 work order 另生成 `result_scope=composite_internal` 的包外 `stage-result.json`，不生成 top-level HQ2 completion。`lld-handoff-acceptance.json` 由 2.16 publisher 确定性聚合，只引用两个密封测试，不新增判断。

### 12.6 执行与语义判定

固定执行顺序：

1. Harness 签发 `consumer_test` → 只从 handoff 独立重建 → 全量追踪强制对象 → 记录 missing guesswork → 密封输出；
2. Harness 验收并冻结 consumer hash；若非 pass，HQ2 立即结束，不签发 fidelity task；
3. Harness 用新 task/context 签发 `fidelity_test` → 读取已密封 reconstruction 和 HP1 package → 检查双射、覆盖和分类忠实性；
4. 两项均 pass 后，composite publisher 生成 acceptance 和 top-level completion。

- `pass`：consumer `missing_guesswork=[]` 且 findings 为空；fidelity 双射、覆盖、分类全部通过且 findings 为空；
- `revise`：仅当前 HQ2 task 的测试执行或证据错误，可本地重做；consumer task 重做必然使旧 fidelity task stale；
- `fail`：handoff 独立不可消费或与 package 不忠实，按 2.15 生成 blocked result；router 先返 HP1，若 source trace 证明根因来自更早 canonical，再定向返回唯一 owner。

### 12.7 交付标准与消费者

Pass：handoff-only reconstruction 完整，全部强制测试通过，`missing_guesswork=[]`，LWR↔LWK 双射成立，机器包与 handoff 无遗漏／增强／弱化／错分，且无需新增主要事实、结构或功能。直接消费者：HH1-A、HF1。交付包或 handoff 缺陷 owner 为 HP1；测试执行、隔离、证据或结论错误的 owner 才是 HQ2。

## 13. HH1-A：`novel-hld-review-report-assembler`

### 13.1 定义

类型：`hybrid / thinking-dominant`。触发：HP1 ready 且 HQ2 已通过真实 handoff 验收，需要把机器 HLD 组织成人可审的结论层。

脚本支持只负责 schema、引用和阅读预算检查，不判断故事质量。

### 13.2 目标与职责

- 选择并组织总体结构、多线、人物弧线、信息悬念、时空节奏和关键功能；
- 用人类语言表达结论与控制信息；
- 设计图表数据；
- 显示开放项、风险、禁止事项和 LLD 边界；
- 为每个可见结论绑定 HP1 source ID 与 locator。

### 13.3 边界与约束

- 唯一内容输入是 HP1；
- 不重读原始构思、HA1–HK1 或聊天来“补充理解”；
- 不展示 Agent 候选比较、推理链或过程说明；
- 不新增、更正或弱化 HLD；
- 不生成 HTML，也不自证忠实性。

### 13.4 输入契约

顶层 upstream：`[HB0,HP1,HQ2]`；内容输入仅 HP1，HQ2 只提供准入结论。

必需文件：HH1 workspace state、work order、input gate、HP1 completion/manifest/validation、`novel-hld-package.json`、cross-index、traceability、`novel-hld-spec.md`，以及 HQ2 completion/manifest/validation/acceptance。

硬准入：HP1、HQ2 current ready 且绑定同一 HP1 hash；报告 schema 和固定板块版本明确；不存在另一内容源。

### 13.5 输出契约

内部 canonical：`hld-human-review-report.json`。必需板块：

- `title_and_decision_scope`；
- `overall_narrative_architecture`；
- `storyline_choreography`；
- `character_arc_placement`；
- `pov_information_suspense`；
- `time_space_pacing_tension`；
- `key_scene_functions`；
- `open_items_constraints_and_lld_boundary`；
- `visual_models[]`；
- `source_bindings[]`；
- `review_budget`：记录决策层 CJK 字符数、Latin word 数、图形数和固定公式计算的预计阅读分钟数。

每个展示元素必须有 `id / element_kind / conclusion / source_ids / locators / visual_role / review_question`。`id` 只允许主设计 5.5 注册的 `HRE-`（报告结论／控制元素）或 `HVG-`（visual model）前缀；不得再使用未注册的 `element_id` 同义字段。

内部内容包严格使用 2.4-B 的 HH1-A profile；work order 另生成 `result_scope=composite_internal` 的包外 `stage-result.json`，不产生 HH1 top-level completion。

### 13.6 执行与语义判定

依次执行：从 HP1 建立全部 material control inventory → 按作者十分钟决策路径排序 → 把结论压缩成人类语言但保留约束强度 → 为复杂关系选择最小必要图形 → 逐元素绑定 source ID/locator → 计算 `estimated_read_minutes = CJK字符/500 + Latin词数/250 + 图形数×0.25` → 反向检查是否遗漏、增强或暴露过程推理。

- `pass`：全部 material control 可在报告中定位，阅读路径结论优先，`estimated_read_minutes<=10`，且无新增事实或过程噪音；
- `revise`：组织、表达、图形或 source binding 需在 HH1-A 本地调整；
- `fail`：HP1 本身缺少必要结论；HH1-A 不补写，由 2.15 与 router 生成 blocked result 并返回 HP1。

### 13.7 交付标准与消费者

Ready：结论优先、无过程噪音；七个 HLD 内容域均覆盖；所有句子和图表数据有 HP1 来源；没有新故事事实。直接消费者：HH1-B、HH1 composite publisher（后者只在 B/C 也通过后读取密封包）。问题唯一 owner：HH1-A。

## 14. HH1-B：`novel-hld-presentation-fidelity-reviewer`

### 14.1 定义

类型：`thinking`。触发：HH1-A 报告候选完成，需要独立证明它忠于 HP1。

### 14.2 目标与职责

- 检查事实、结构、关系、顺序、数值和状态一致；
- 检查 mandatory、open、HLD decision 和 LLD freedom 的表达；
- 检查重要内容遗漏、弱化、增强或错误归因；
- 检查 visual model 数据与 HP1；
- 独立验证作者能否在十分钟决策层中找到并复述关键控制信息；
- 产出 material drift finding 与 decision-usability finding。

### 14.3 边界与约束

- 不修改报告或 HP1；
- 不评审 HLD 内容质量；
- 不因为表达风格不同判 drift，除非意义改变；
- 不允许 assembler 自评；
- 不通过删除 material control 来满足十分钟预算；
- 不生成 HTML。

### 14.4 输入契约

HH1 内部 upstream：`[HH1-A]`；顶层内容基线仍是当前 HP1。

必需文件：HP1 ready 包、HH1-A internal manifest、`hld-human-review-report.json`、HH1 workspace state。禁止读取聊天和旧报告。

硬准入：review task ID 与 HH1-A 不同；候选报告完整封存；HP1 hash 与 HH1-A input binding 相同。

### 14.5 输出契约

内部 canonical：`presentation-fidelity-review.json`。必需字段：

- `fact_fidelity`；
- `structure_and_relation_fidelity`；
- `coverage_fidelity`；
- `authority_and_open_item_fidelity`；
- `visual_data_fidelity`；
- `material_drift_findings[]`；
- `reading_budget_validation`；
- `decision_retrieval_tests[]`；
- `cognitive_overload_findings[]`；
- `verdict=pass|revise|fail`。

固定 retrieval questions 至少覆盖：总体结构如何推进、全部强制故事线如何连接、核心人物弧线与关键选择、主要 POV／知识边界、时空与连续性硬约束、关键功能与高潮义务、未决问题和 LLD 禁区。每个答案必须只用报告元素完成并返回 element/source IDs。

内部内容包严格使用 2.4-B 的 HH1-B profile；work order 另生成 `result_scope=composite_internal` 的包外 `stage-result.json`，不生成 HH1 top-level completion。

### 14.6 执行与语义判定

依次执行：枚举全部可见 report element → 逐项解析 HP1 source binding → 比较事实、关系、顺序、状态和权威强度 → 从 HP1 反向检查 material coverage → 校验每个 visual model 的数据集合 → 独立重算阅读预算 → 仅凭报告回答固定 retrieval questions → 检查结论是否被过程说明、重复文字或图形负担掩埋 → 形成 drift/usability findings。

- `pass`：双向覆盖成立，material drift 与 cognitive overload findings 均为空，阅读预算不超过十分钟，固定问题全部能准确回答并定位；
- `revise`：忠实性审查自身证据错误，可在 HH1-B 本地重做；
- `fail`：报告发生遗漏、增强、弱化、错引或无法在预算内支持作者决策，返回 HH1-A；HP1 内容质量不在本技能裁决范围。

### 14.7 交付标准与消费者

Pass：material drift 和认知过载 finding 均为空，所有报告元素 source binding 可解析，关键控制无遗漏，十分钟预算和固定检索问题通过。唯一消费者：HH1-C 和 HH1 composite publisher。审查执行错误 owner 为 HH1-B；报告问题实际返工 owner 为 HH1-A。

## 15. HH1-C：`novel-hld-html-renderer`

### 15.1 定义

类型：`script`。触发：HH1-A 报告通过 HH1-B，需要确定性离线 HTML。

### 15.2 目标与职责

- 按固定模板渲染标题、目录、文本、表格和 SVG；
- 生成结构图、多线图、人物弧线图、信息链和节奏曲线；
- 校验可访问性、打印和常用视口；
- 绑定模板、CSS、renderer、输入和输出 hash。

### 15.3 边界与约束

- 不生成、摘要、润色或删减故事内容；
- 图形数据只能来自 report JSON；
- 不读取 HP1 后自行选择结论；
- 无外部 CDN、网络字体、远程脚本或不安全注入；
- 相同输入和 renderer 必须字节一致。

### 15.4 输入契约

HH1 内部 upstream：`[HH1-A,HH1-B]`；不得跳过 fidelity review。

必需文件：HH1 workspace state、HH1-A manifest/report JSON、HH1-B manifest/fidelity pass、固定模板、CSS、renderer 和 schema。

硬准入：fidelity verdict=pass；report hash 与 review binding 相同；模板和实现版本受控。

### 15.5 输出契约

内部 HTML 内容包严格使用 2.4-B profile：

```text
hld-human-review-report.html
render-target-registry.json
render-execution.json
validation.json
package-manifest.json
```

HTML 必须含正式小说／项目标题、HLD 评审范围、版本、状态、目录和作者决定说明。SVG 元素必须有文本替代或可访问标签。`render-target-registry.json` 必须逐一登记 `HUI-` 的 DOM locator、render role、对应 `HRE-/HVG-` 和 element content hash；集合必须与 HTML 中的 `data-render-target-id` 完全相等。HUI ID 固定为 `HUI-<report_element_id>-<render_role>-<zero_based_ordinal>`，相同 report JSON 与模板必须产生相同 ID。

HH1-C 另生成 `result_scope=composite_internal` 的包外 `stage-result.json`，不生成 HH1 completion。Harness 仅能按 2.16 的 HH1 publish profile 重验 A/B/C 并生成顶层 completion；不得存在未定义的 publisher 或由 HH1-C 越权封闭。

### 15.6 交付标准与消费者

Ready：HTML 与 report JSON 元素集合相等；无横向溢出和外部依赖；打印与键盘访问通过；所有 hash 当前。直接消费者：HH1 composite publisher；外部作者门只消费 publisher 发布的顶层 HH1 包。HTML 问题 owner：HH1-C。

## 16. HF1：`novel-hld-finalizer`

### 16.1 定义

类型：`script`。触发：HP1、HQ2、HH1 已 ready，外部作者已经对当前机器包、handoff acceptance 和人审包作出决定。

它只封闭 HLD，不解释作者意图，也不启动 LLD 设计。

### 16.2 目标与职责

- 验证完整 current completion 链；
- 验证 run-state 无 active return，且不存在未 resolved 的 current revision plan；
- 验证 author decision 同时绑定 HP1、HQ2、HH1 和 HTML；
- 验证每个 revision target 的 kind、ID、cross-index／render registry 归属和 author text locator；
- 对 approved 分支重验 `lld-handoff.json`；
- approved 时生成最终 HLD completion 与 LLD admission 证据；
- revise/rejected 时只把外部决定确定性投影为标准 `stage-result.json`，交由 harness 路由或终止。

### 16.3 边界与约束

- 不把聊天中的“同意”推断为 author event；
- 不修改 HP1、HH1、handoff 或决定；
- 不在 revise/rejected 时生成 completion；
- 不生成 LLD 内容；
- 任一上游变动自动使旧 completion stale。

### 16.4 输入契约

精确 upstream：`[HB0,HA1,HS1,HC1,HI1,HR1,HK1,HQ1,HP1,HQ2,HH1]`。

必需文件：当前 run-state；全部 current completions/manifests/validations；HP1 `lld-handoff.json` 与 cross-index；HQ2 `lld-handoff-acceptance.json`；HH1 HTML manifest 与 `render-target-registry.json`；外部密封 `author-decision.json`。

Author decision 必需字段：`decision=approved|revise|rejected`、event seq、作者原文、HP1 binding、HQ2 acceptance binding、HH1 binding、HTML binding；revise 另含非空 `revision_targets[]`。新 revise decision 使用 schema `1.1`；每个 target 必须有 `target_kind=hld_content|report_content|render_expression|conception_authority`、`target_id`、`requested_change`、`author_text_locator`、`change_scope` 和 `target_field_paths[]`。`hld_semantic` 必须再列 `semantic_target_ids[]`，全部 ID 在 HP1 cross-index 中解析到同一 canonical owner；`report_content` 只能引用 `HRE-/HVG-` 且仅改表达，不能新增或修改任何故事事实；`render_expression` 只能引用 HTML 中注册的 `HUI-`。不得用自由文本或报告元素代替 canonical semantic target ID。

硬准入：决定事件外部、当前、未消费；所有 binding 完全相等；HQ2 verdict=pass 且绑定当前 HP1；run-state 无 active return，且不存在 pending/superseded revision target group。

### 16.5 输出契约

Approved 分支固定内容包：

- `hld-completion.json`；
- `final-validation.json`；
- `package-manifest.json`；
- finalizer execution record。

包外唯一 top-level `stage-result.json` 的 `completion_ref` 指向 `hld-completion.json`。

`hld-completion.json` 必须绑定完整 stage chain、author decision、HP1、HQ2 acceptance、HH1、HTML、当前 `lld-handoff.json` 和 final validation，并声明 `next_stage=novel-lld`。

Revise 分支生成标准 revise 包，`revision-report.json` 只能无损投影作者 `revision_targets`；rejected 分支生成标准 blocked 包，`blocker_class=author_rejected`。两者都不得生成 completion、return request、终止状态或下一 run-state；harness 消费 `stage-result.json` 后才生成唯一 return／终止状态和新 revision。

### 16.6 交付标准与消费者

Ready：仅 approved；完整链和 hash 当前；author decision 与 HP1、HQ2、HH1/HTML 完全一致；handoff 通过重验；completion 自身不引用后态。直接消费者：HLD harness；harness 接纳后生成唯一 `lld_ready` 状态，未来 `novel-lld-autonomous` 只消费该状态授权的 completion。问题唯一 owner：HF1 的封闭错误；内容问题按 source ID 定向返回原 owner。

## 17. Canonical 对象级契约与跨模型不变量

HA1–HK1 的**设计 canonical 元素**必须有唯一稳定 `id`、非重复 `source_refs[]`、非重复 `source_authority_refs[]` 和 `ownership_class`。`id` 必须符合主设计第 5.5 节前缀；`ownership_class` 只允许 `source_projection|hld_owned|preserved_open|lld_freedom`，并遵守 2.14 映射；引用数组元素只能是已注册稳定 ID，且 `order` 使用从 0 开始的非负整数。每个 stage-scoped decision dependency 使用 `HDD-`，属于治理证据，不是故事设计元素，不进入 `hld_ownership`。凡有进入／退出变化的设计对象，还必须有可解析的 `entry_state_ref`、`exit_state_ref`；凡有时间或空间落点的设计对象，还必须有对应 ID 引用。设计数组数量由来源义务决定：有适用义务时不得为空；无适用义务时由模型级 `dispositions[]` 记录 source obligation、`disposition=not_applicable|preserved_open|deferred_to_lld` 和理由，其中 `deferred_to_lld` 必须已有明确 LLD freedom，不设固定模板数量。

HQ1、HQ2、HH1-A/B 的**评审或呈现证据元素**必须有稳定 `id`、目标／证据引用和本技能输出契约规定的字段，但不得带 `ownership_class`、`design_decisions[]` 或伪装成故事 canonical element；其权威仅限于审查或呈现结论。HH1-A 报告元素只用 `HRE-`，visual model 只用 `HVG-`；HH1-C 不创建语义元素，只为确定性 HTML 容器分配 `HUI-`，并通过 `data-report-element-id` 回指 `HRE-/HVG-`。HP1、HH1-C、HF1 是确定性组装／渲染／封闭产物，不创建上述两类语义元素。所有 JSON schema 均必须 `additionalProperties:false`。

| Producer | 核心对象 | 元素必需字段（除公共字段外） | 必须成立的不变量 |
| --- | --- | --- | --- |
| HA1 | phase / narrative unit / chapter shell / anchor / state contract | order、purpose、entry/exit、contained IDs、obligations | 单元只属于一个主排序位置；入口—出口可连续；全部 baseline 结构义务被覆盖或有 disposition |
| HS1 | storyline / segment / connection / event placement | line type、driver、goal、conflict、turn、payoff、unit refs、connection type | 强制故事线均有起—变—结；连接点双方存在；事件只落到合法单元 |
| HC1 | arc / arc step / relationship step / choice-cost-consequence | character refs、belief/goal/state、choice、cost、consequence、unit/event refs | 每次人物变化有触发与代价；关系变化有双方状态；无“事件发生但无人承担” |
| HI1 | POV assignment / knowledge state / information node / suspense chain / reveal | knower、known/unknown/misbelief、source、reveal condition、payoff、unit refs | 人物只能据其知识行动；埋点、探针、揭示、回收可追踪；无越权视角信息 |
| HR1 | narrative order / duration / transition / synchronization / pacing segment | story time、discourse order、duration density、location refs、tension in/out、continuity checks | 时间不逆因果；移动和通信可实现；并发事件可同步；节奏变化有叙事功能 |
| HK1 | HKF / coverage record / LWR | function、obligations、participants、environment/event refs、entry/exit、LLD elaboration/freedom、acceptance | 每个高层义务至少一个 owner；HKF 无重复主功能；LWR 完整且不泄漏 LLD 答案 |
| HQ1 | pass claim / finding | check ID、actual evidence/value、anchor；finding 另含 defect origin、affected IDs、correction condition | 每个适用检查有证据；router 可由 affected ID 唯一求得 owner；pass 不由平均分或字段存在推导 |
| HQ2 | handoff test / finding | tested IDs、reconstruction、expected source、actual result、anchor | 全部强制 LWK 可消费；LWR↔LWK 双射；`missing_guesswork=[]` 才能 pass |
| HH1-A/B | report element / fidelity finding | conclusion、source IDs、locators、visual role、review question；drift type/evidence | 所有可见结论可回指 HP1；不得新增、遗漏、弱化或增强实质控制信息 |

全链公共不变量：ID 引用必须可解析且类型合法；同一 canonical 中 ID 不重复；来源主分类只允许 `mandatory|freedom|must_ask|open`，`open_item` 是独立布尔标志，HLD 处理归属只允许 `source_projection|hld_owned|preserved_open|lld_freedom`；三者不得互写并必须满足 2.14 映射。未解决 `must_ask` 不得伪装成 `hld_owned`，已解决项必须绑定外部 resolution，`open_item=true` 不得无 resolution 消失。集合覆盖采用“来源全集 = 已覆盖集合 ∪ 有理由 disposition 集合”；任何上游对象变更都会使其下游 completion stale。

## 18. 逐阶段精确对接表

| Consumer | 必需上游字段 | 唯一 Producer | 缺失时动作 |
| --- | --- | --- | --- |
| HA1 | authority、source index、HLD assignment | HB0 | blocked，不推断 |
| HA1–HK1 / HQ1 dependency assessment | 当前 work order unresolved projection | Harness 只投影；HA1–HK1 生成 non-quality HDD，HQ1 只生成 quality HDD | `required_now` 在 candidate／review verdict 前 blocked；其余随 canonical/review 继承 |
| HS1 | phases、units、chapter shells、anchors、state contracts | HA1 | return HA1 |
| HC1 | storyline segments、unit matrix、connections、event placement | HS1 | return HS1 |
| HI1 | arc states、arc/relationship steps、choice-cost-result、permission checks | HC1 | return HC1 |
| HR1 | POV、knowledge、suspense、reveal/payoff、information nodes | HI1 | return HI1 |
| HK1 | HA1 结构 + HS1 线 + HC1 弧线 + HI1 信息 + HR1 连续性 | 各唯一 owner | return 最早缺陷 owner |
| HQ1 | HB0 与 HA1–HK1 current canonical | HB0、HA1–HK1 | blocked / return owner |
| HP1 | HQ1 ready verdict、全部 canonical、HK1 LWR | HQ1、HA1–HK1 | blocked，不组装 |
| HQ2 consumer | 真实 handoff + 非内容 identity/hash 元数据 | HP1 | blocked，不得读取 package 补答案 |
| HQ2 fidelity | sealed consumer test + 正式 package/spec/traceability/handoff | HQ2 consumer、HP1 | return HP1 或 fail HQ2 |
| HQ2 publisher | sealed consumer/fidelity pass + HP1/HB0 binding | HQ2 两任务、HP1、HB0 | blocked，不发布 completion |
| HH1-A | package、cross-index、traceability、spec + HQ2 pass gate | HP1、HQ2 | return HP1 / HQ2；内容仍只读 HP1 |
| HH1-B | HP1 + sealed report | HP1、HH1-A | return HH1-A 或 fail reviewer |
| HH1-C | report + fidelity pass | HH1-A、HH1-B | blocked，不渲染 |
| HH1 publisher | A/B/C sealed pass + HP1/Q2 binding | HH1-A/B/C、HP1、HQ2 | blocked，不发布 completion |
| HF1 | full chain + author event + handoff + handoff acceptance + sealed human package | harness、author gate、HP1、HQ2、HH1 publisher | return / reject / blocked |

任何 consumer 新增本表外的必需字段，都必须先修订本契约和 producer schema；不得在 prompt 中临时索取。Router 生成的 revision plan 是控制面 artifact：其输入只能是已密封 stage result／author event，消费者只能是 harness state machine 和当前 active group owner；它不进入故事内容 producer 表。

## 19. 契约级验收

实现前后都必须自动检查：

1. 14 个 skill 名称唯一，类型属于允许集合；
2. 每个 skill 有触发、职责、边界、约束、输入、准入、输出、ready 和消费者；
3. 每个 consumer 必需字段都有且只有一个 producer；
4. 所有 stage 输入顺序与 HLD workflow 拓扑精确一致；
5. Thinking、script、hybrid 的包 profile 不混用；
6. blocked 包不含候选或 completion；
7. HQ1 与生产者、HQ2 与 HP1、HH1-A/B task identity 隔离；
8. HP1 不创作、HH1 不改写、HF1 不代签；
9. `lld-handoff.json` 只在 HP1 产生，先由 HQ2 验收，只在 HF1 批准后可被 LLD 消费；
10. 任一作者锁定事实需要改变时，退出 HLD 并回到构思／访谈权威 owner；
11. HQ2 consumer task 的实际读取集合不含 package/spec/canonical，且其输出先于 fidelity task 密封；
12. HQ2/HH1 的 ready completion 与 non-ready top-level result 都只能由 2.16 对应 publisher profile 产生；内部 task 不得直接驱动 router；
13. 上游 `source_authority_refs` 原值保持，`ownership_class` 映射合法；
14. Review verdict 与 stage result 的组合完全符合 2.15；
15. HH1-B 的十分钟预算、固定 retrieval questions、material fidelity 同时通过；
16. 第20节14个技能的 positive/negative/boundary eval 均有评分和 Pass Bar；
17. 第21节 harness-level P01/N01/B01 与事务回归 R01/R02 覆盖整链编排、HDD、多目标返工、parent consumption、adapter 和 release，使用独立 12/14 Pass Bar；
18. 主设计出现的每个实现字段、artifact role、source access 和包 profile 都能精确回指本目录；任何未注册同义词使设计冻结失败；
19. HB0 只登记 unresolved source；HA1–HK1 在候选前生成 non-quality HDD，HQ1 在 verdict 前生成 quality HDD，`required_now` 不产生 candidate/verdict，且 HQ1/HP1 能完成覆盖与聚合；
20. 多 owner finding 或作者 revision targets 被无损分组进一个 revision plan，单 active group 与 pending groups 可连续恢复，任何 target 不会静默丢失；
21. `stage-result.json` 始终是包外结果信封；top-level ready 与 composite-internal ready 的条件字段互斥，所有 reviewer/hybrid/internal 包匹配 2.4 profile；
22. `HRE-/HVG-/HUI-` 的字段名、owner、HTML 回指和作者 target 路由唯一；
23. 第20节六维评分在每个 P/N/B case 中均为 2/2，fixture 在执行前密封且缺陷注入命名唯一。

## 20. Bounded-skill 定义级 agentic eval 矩阵

本节冻结未来实现必须具备的评测语义，不代表 eval 文件已经开发。每个 skill 的三个 case ID 固定为 `<SKILL>-P01 / <SKILL>-N01 / <SKILL>-B01`，每个 case 实现时必须含 Prompt、密封 fixture、fixture manifest/hash、单一命名缺陷注入、Expected Behavior、Forbidden Behavior、逐维 0–2 评分和 Pass Bar。Fixture 必须在执行前密封，不能在看见输出后更换或降低难度。

Bounded-skill 统一六维为：

1. `scope_fidelity`：完成本技能目标且不扩大任务；
2. `input_gate_obedience`：只读 allowlist，拒绝 stale／错 owner／错顺序输入；
3. `output_contract_correctness`：字段、包 profile、引用和 verdict/result 完全合法；
4. `semantic_or_deterministic_correctness`：thinking/hybrid 的意义判断正确，script 的确定性变换正确；
5. `boundary_discipline`：没有构思改写、LLD 泄漏、producer/reviewer/publisher 越权；
6. `parent_consumability`：parent 可只凭正式结果信封、manifest、validation 和 completion/internal manifest 作唯一下一步判断。

六维均适用于14个技能，每维固定 `0=缺失或误导 / 1=存在但可绕过或证据不足 / 2=明确且由产物证据证明`，不得由 case 作者自行宣布 n/a。

| Skill | Positive case | Negative case | Boundary case |
| --- | --- | --- | --- |
| HB0 | 当前四文件 baseline 无损准入并只登记 unresolved register | 植入 hash／locator／run 漂移，必须 blocked | 只给 Markdown／HTML或要求 HB0 代判 HDD，均不得猜测准入／处置 |
| HA1 | 先完成 stage-scoped HDD，再根据实际义务选择非模板结构并闭合进入—变化—退出 | 植入 `required_now` 却先产 candidate，或强套固定三幕／遗漏重大锚点，必须发现 | 不得把本 stage 的“不需要”扩大到全 HLD，不得写场景动作、对白或新事件 |
| HS1 | 全部强制线建立—发展—转折—回收且主体可重建 | 植入一条遗漏／重复／假连接线，必须定向 finding | 可选旋律线允许不激活，不得强行扩写 |
| HC1 | 核心人物压力—选择—代价—结果连续 | 植入未授权感情／能力或无承担者结果，必须发现 | 不得补外貌、背景、社交圈或新人物 |
| HI1 | POV、知识来源和 setup—probe—reveal—payoff 合法 | 植入 POV 越权、无来源知识或提前裁决，必须发现 | 开放终局必须保持开放 |
| HR1 | 时间、迁移、资源、状态、节奏与恢复连续 | 植入不可能迁移、时间倒置或单调张力，必须发现 | 不得用逐场景日程或精确字数伪装 HLD |
| HK1 | 最小充分 HKF 与 LWR 覆盖全部高层义务 | 植入对白细节、功能过载、一句话解危或无消费者义务，必须发现 | LWR 分组属于 HK1，HP1 不得代判 |
| HQ1 | 仅凭 canonical 找到植入的因果／权限／信息缺陷 | Producer evidence 为缺陷辩护时仍必须 fail | 纯审美偏好不得形成 finding |
| HP1 | 相同输入字节一致且 LWR→LWK 一对一 | 植入丢字段、重分组或摘要改义，必须 fail | 不得创作性修复上游 |
| HQ2 | handoff-only 能完整重建，fidelity 对照无漂移 | 完整 package 有答案但 handoff 缺字段时，consumer test 必须 fail | consumer 输出未密封或读取 package 时整次无效 |
| HH1-A | 在十分钟预算内呈现全部 material controls | 植入过程噪音、结论埋没或新增事实，必须 fail | 不得靠删除控制信息压缩预算 |
| HH1-B | 忠实性与固定 retrieval questions 均通过 | 植入语义漂移或认知过载，必须返回 HH1-A | 仅表达风格不同且意义不变不得 fail |
| HH1-C | 离线、可访问、打印可读、字节确定，HUI registry 与 DOM 全等 | 植入外链、脚本注入、元素遗漏、HUI 漂移或溢出，必须 fail | Renderer 不得自行摘要 HP1／报告，也不得用自然语言替代 target registry |
| HF1 | 当前 approved bindings 生成 completion；revise targets 均可由 cross-index/registry 验证 | 植入 stale hash、重复决定、不可解析 target 或未过 HQ2，必须 fail | revise/rejected 不得生成 completion、状态或自行解释作者 requested change |

统一 Pass Bar：positive 不得出现 false blocker；negative 必须识别植入缺陷、给出故事／对象证据并路由到正确 defect origin；boundary 必须证明不越权。三个 case 的六个维度都必须为 2/2；任一 blocker 漏检、错误 owner、越界补写、读取隔离失败、parent 无法唯一消费或缺少评分／Pass Bar，均不得发布该 skill。

## 21. Harness-level agentic eval 契约

本节验收 `novel-hld-autonomous` 整条 harness，不重复给 14 个技能打平均分。基础 case ID 固定为 `HLD-E2E-P01 / HLD-E2E-N01 / HLD-E2E-B01`，事务回归 case 固定为 `HLD-E2E-R01 / HLD-E2E-R02`。每个 case 的实现文件必须包含 Prompt、密封 fixtures 及 manifest/hash、Expected Behavior、Forbidden Behavior、逐维 Scoring Rule、Pass Bar，以及实际 stage/result/state 证据。

| Case | 密封 fixture 与刺激 | Expected Behavior | Forbidden Behavior |
| --- | --- | --- | --- |
| Positive：完整批准链 | 一份当前、完整、含多线／人物／信息／时空约束的通用 baseline；外部作者最终批准 | 严格按固定拓扑运行；全部 gate、publisher 和 hash 链闭合；作者门后仅 HF1 生成最终 completion；LLD 只凭正式 handoff 可启动 | 跳过 stage、读取聊天、内部 task 发布顶层 completion、router 或 adapter 改写 canonical |
| Negative：污染与陈旧证据 | HQ2 consumer 被授予 package 读取、一个 stale completion、一次企图绕过 HF1 的批准事件，三种变体分别执行 | 在最早确定性门 fail closed；consumer non-ready 时不签发 fidelity，publisher byte-copy 内部失败并发布 top-level result；保留 durable result；router 根据实际 defect origin 定向处理 | 用 package 补 handoff、要求伪造 fidelity 包、router 直接消费 internal result、接受 stale hash、直接把作者批准转成 `lld_ready`、以重试覆盖失败证据 |
| Boundary：职责越界 | baseline 要求新增构思事实，同时给出一个应留给 LLD 的动作／对白细节请求 | 前者退出当前 HLD 并进入 conception reentry；后者保留为 LLD freedom；两者都留下可消费边界证据 | HLD 自行研究或补事实、把 LLD 细节写入 canonical、把合法开放误判成内容缺失 |
| R01：开放问题 owner | baseline 含一个 HC1 实际依赖的 must-ask 和一个全链不依赖的 open item；外部作者回答前者 | HB0/Harness 只投影；各 stage 先生成 HDD；HC1 在 candidate 前 blocked；外部 resolution 后恢复；HP1 只聚合全链 HDD，未回答 open item 保持开放 | HB0/Harness 代判、先形成 candidate 再询问、单 stage 宣称全 HLD 不需要、open item 静默消失 |
| R02：跨层多目标返工 | 作者同时 target HS1 内容与 HH1-C HUI；HS1 修改后令旧 HUI target 消失 | Router 生成 immutable plan 与 plan-state；先解决 HS1，HUI group 保持 pending；目标失效后进入 revision_retarget，外部重新定位后完成 HH1-C；全硬门与作者门重跑 | 把 HUI 要求交给 HS1、旧决定失效时丢 target、回写 plan、静默把 superseded 当 resolved、跳过新作者批准 |

Harness rubric 固定为七维：`scope_fidelity / workflow_rigor / skill_type_correctness / adapter_faithfulness / validation_hardness / semantic_acceptance / release_portability`。每维 0–2：0 为缺失或误导，1 为存在但可绕过，2 为明确且由产物证据证明。

Harness Pass Bar：无 blocker 且总分 `>=12/14` 为 `pass`；无 blocker 且 10–11 为 `pass_with_risks`；低于 10 或存在任一 blocker 为 `fail`。Blocker 至少包括：改变固定拓扑、adapter 弱化 core 语义、跳过 author gate、隔离读取失败、validator/reviewer verdict 未被 parent 消费、发布未验证包、隐瞒 unsupported runtime。`pass_with_risks` 可进入人工风险裁决，但不得自动标记生产 release ready。
