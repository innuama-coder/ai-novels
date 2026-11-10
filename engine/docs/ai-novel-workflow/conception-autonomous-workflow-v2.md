# 小说构思自主工作流 V2：技能与交付契约

> 状态：目标架构与实现契约  
> 适用范围：访谈成果已经完成、V2 访谈简报已经获得作者批准之后，到小说开发正式准入之前  
> 不适用范围：访谈、事实研究、章节规划、场景开发、正文写作和出版适配

## 1. 目标与完成定义

自主构思阶段把作者已经批准的构思骨架发展为完整、自洽、可开发且可审阅的小说构思。生产顺序固定为：

```text
故事线架构
  → 虚拟世界
  → 具体环境
  → 时间线与事件
  → 角色系统
  → 完整性与一致性审查
  → 机器构思交付物
  → 人审报告
  → 作者批准
```

构思阶段只有同时满足以下条件才算完成：

1. 五个设计模型分别通过自身硬验收；
2. 不可变作者控制基线完整保存 I0–I5、叙述契约和已采用事实依据；
3. 独立审查证明作者控制基线与五个模型共同形成完整、一致的小说主体；
4. 机器构思交付包完整绑定作者控制基线、五个模型和审查结果；
5. 人审报告完整绑定同一机器构思交付包；
6. 作者决定同时绑定机器包和当前 HTML；
7. 工作流生成最终 `conception-completion.json`；
8. 主 harness 重新验证完整链后给出 `ready`。

任何单份 Markdown、单个 `ready`、页面被打开、口头确认或聊天中的“批准”都不构成完成。

## 2. 顶层阶段与独立技能

工作流有八个顶层阶段、十个独立技能。人审报告是一个顶层阶段，内部由三个技能协作。

在八个顶层阶段之前，harness 先执行无创作权的 B0 作者控制基线封装。B0 不是
第九个构思技能；它只把六份作者权威设计稿、批准和已采用研究依据封装成所有阶段
共同读取的不可变输入。

| 阶段 | 技能 | 唯一拥有的决定 |
| --- | --- | --- |
| S1 故事线架构 | `novel-storyline-architecture-designer` | 故事线需求、全部故事线、线内状态变化和线间连接架构 |
| W1 虚拟世界 | `novel-world-model-designer` | 世界公理、历史压力、运行系统、机构、资源、权力与信息机制 |
| E1 具体环境 | `novel-environment-system-designer` | 主要环境、功能区、环境拓扑、准入、资源、风险和承载能力 |
| T1 时间线与事件 | `novel-event-timeline-designer` | 世界时间线、全部主要事件、事件因果和故事线事件序列 |
| C1 角色系统 | `novel-character-system-designer` | 角色需求、人物档案、能动性、职责、关系边和三层人物网络 |
| Q1 独立审查 | `novel-conception-reviewer` | finding、verdict、唯一责任阶段和开发准入判断 |
| P1 构思交付 | `novel-conception-deliverable-assembler` | 无创作决定；只组装、索引、渲染和封包 |
| H1 人审报告 | `novel-conception-human-review-assembler` | 报告信息架构、十分钟阅读预算和片段任务 |
| H1 人审报告 | `novel-conception-fragment-writer` | 非权威小说样片中的局部表达选择 |
| H1 人审报告 | `novel-conception-review-html-generator` | 无内容决定；只做确定性 HTML 呈现 |

旧 `novel-development-map-designer` 不再作为正式生产技能。其故事、世界、环境、事件和角色能力分别迁移到 S1–C1；迁移完成前，它只能用于读取旧包或回归对照，不能生成 V2 completion。

上述十个名称必须分别存在可发现的 `engine/skills/<name>/SKILL.md`。技能入口只能声明本表的
输入、决定权和交付；旧 D1/R1 references 或 scripts 即使仍为历史包保留，也不得被
V2 input gate、manifest 或 completion 引用。缺少入口、入口仍消费 D1/R1、或入口声称
拥有本表之外的决定权时，调用链验证失败。

## 3. 全局权威规则

### 3.1 权威层级

故事事实的权威顺序固定为：

1. 作者批准且由 I0–I5 completion 绑定的六份访谈设计产物；
2. B0 对这些产物的逐字封装、控制点索引及作者已采用的研究包；
3. S1–C1 在自身授权范围内新增且通过验证的设计决定；
4. Q1 只审查，不产生新故事事实；
5. P1 只组装，不产生新故事事实；
6. H1 只呈现；小说片段不是设定权威。

V1、V2、HTML、访谈报告、审阅说明、聊天记录和旧稿只能证明流程、版本或讨论来源，不能提供新的故事事实。

### 3.2 决定分类

所有设计决定必须归入且只能归入一种：

| 分类 | 含义 | 可否由自主技能改变 |
| --- | --- | --- |
| `author_locked` | 作者已经确认的主题、事实、边界、核心选择或结局 | 否 |
| `autonomous_owned` | 作者明确授权自主阶段补足、且由当前技能拥有的设计决定 | 只能由拥有者技能改变 |
| `downstream_freedom` | 不影响控制面的开发实现空间 | 下游可以创造，但不能提升为权威事实 |
| `author_open` | 作者有意保留或尚未裁决的问题 | 否；必须保持开放 |

不得以“合理推断”“一般常识”或“有助于故事”为由改写 `author_locked` 或裁决 `author_open`。

`downstream_freedom` 有两种生命周期不同但不得混淆的记录。S1–T1 可以用稳定需求
或角色槽 ID 记录尚待后续 owner 解析的阶段交接义务；这些 ID 只证明授权来源和交接
历史，不因后续产生了新的权威实现对象而改列为 `autonomous_owned`。C1 必须另外用
`DEV-` 对象声明构思完成后仍留给小说开发的终端实现空间。权威人物、事件、环境、
关系、弧线或决定 ID 不得同时充当 `DEV-`。每个阶段 validator 必须对四个集合做
精确相等和两两不相交检查，P1 仍对五阶段并集做最终互斥检查。

### 3.3 公共包契约

S1–Q1 每个正式 `ready` 包必须包含：

```text
<canonical-model>.json
generation-session.json
generation-evidence/*.json
execution-record.json
<human-readable-preview>.md
validation.json
package-manifest.json
stage-completion.json
```

P1 和 H1 中的确定性技能不需要生成式阶段证据，但必须包含绑定当前脚本、模板、输入和输出的执行记录。H1 内部子包不各自生成顶层 completion；它们遵守
3.8 的复合阶段状态机，只有完整 H1 生成一个 `stage-completion.json`。

所有引用必须：

- 使用相对于当前包的路径；
- 保存 SHA-256；
- 指向 manifest 内文件；
- 属于同一 `run_id`；
- 绑定当前有效 completion；
- 禁止绝对路径、目录猜测和仅凭同名文件消费。

Markdown 只用于阅读。下游唯一内容输入是 canonical JSON；completion 唯一绑定对象是 package manifest。

### 3.4 状态

所有技能只允许：

| 状态 | 含义 |
| --- | --- |
| `ready` | 输入、模型、语义、覆盖、来源和封包全部通过 |
| `revise` | 上游有效，当前技能自身存在可局部修正的问题 |
| `blocked` | 硬准入失败，或继续必须改变更早阶段拥有的决定 |

硬准入失败时，候选模型不得存在。阻塞包只允许：

```text
gate-data.json
blocked-report.md
validation.json
```

`ready`、`revise` 和 `blocked` 产物不得混放在同一包中。

### 3.5 生成真实性

S1–C1、Q1、H1 报告设计和片段写作属于生成式技能，必须：

1. 在当前 `CODEX_THREAD_ID` 中开始受控会话；
2. 在开始时冻结输入 manifest；
3. 按技能定义的阶段顺序提交 evidence；
4. 使用前向哈希链绑定阶段；
5. 最终入口只读取已完成的受控工作区；
6. 禁止把会话外写好的最终稿倒填成阶段证据；
7. `execution-record.json` 绑定技能文件、会话、输入和最终模型。

执行记录证明本地任务和产物链，不声称是密码学签名，也不证明执行者绝对诚实。

### 3.6 Schema 与引用硬约束

每个 canonical JSON 都必须有版本化 JSON Schema。下文列出的字段是该版本的
必需业务字段；实现 schema 时同时加入公共元数据
`schema_version / skill / stage / run_id / status / input_gate`，并设置
`additionalProperties: false`。需要新增字段时必须升级 schema 版本并重跑全部下游，
不得在单次任务中临时扩字段。

公共机器契约的权威 schema 位于
[`contracts/autonomous-v2`](contracts/autonomous-v2/contract-index.md)。
技能实现可以收紧自身 schema，但不得削弱公共 schema、重新定义公共枚举或复制出
不兼容版本。

canonical 内容契约固定为：

| 产物 | 公共 schema |
| --- | --- |
| S1 | `storyline-architecture.schema.json` |
| W1 | `world-model.schema.json` |
| E1 | `environment-system.schema.json` |
| T1 | `event-timeline.schema.json` |
| C1 | `character-system.schema.json` |
| Q1 | `conception-review.schema.json` |
| P1 | `novel-conception-package.schema.json` |
| H1 plan / fragment / assembly | `h1-review-plan.schema.json` / `fragment-package.schema.json` / `human-review-report.schema.json` |

schema 负责单文件封闭结构；确定性 validator 另外负责当前版本、哈希、跨文件引用、
集合相等、package profile、owner 路由和状态转换。二者都通过才可 `ready`。

稳定 ID 前缀固定为：

| 对象 | 前缀 |
| --- | --- |
| 故事线需求 | `SLD-` |
| 故事线 | `SL-` |
| 故事线连接 | `SLC-` |
| 世界需求 | `WR-` |
| 世界事实／规则 | `WF-` |
| 世界系统 | `WS-` |
| 环境需求 | `END-` |
| 环境 | `ENV-` |
| 功能区 | `ZONE-` |
| 事件需求 | `EVD-` |
| 主要事件 | `EV-` |
| 角色需求／角色槽 | `CHD-` / `SLOT-` |
| 人物／关系 | `CHR-` / `REL-` |
| 终端开发自由 | `DEV-` |
| finding | `FND-` |

跨模型引用只能使用 schema 声明的 ID 字段和当前输入允许集合。不得把标题、人名、
自然语言或路径当作对象引用。验证器对需求覆盖、对象覆盖、连接覆盖和开放项使用
集合相等检查，不接受“至少覆盖了一部分”。

所有哈希基于 UTF-8、键排序、无无意义空白的规范 JSON。验证器必须是确定性的：

- 合格包退出码为 `0`，且 `validation.json.verdict == "ready"`；
- 契约失败退出码非 `0`，列出稳定错误码和对象 ID；
- 验证器不得修改 canonical 模型；
- stored validation 必须与无写入重验结果完全相等；
- validator、schema、renderer 或 skill 文件变化都会使旧 completion 失去当前资格。

除“每位核心人物至少三层人物关系”以及片段数量、阅读预算等明确产品约束外，
不得以固定故事线数、环境数、事件数或人物数作为质量替代品。

S1–C1 的 canonical 模型还必须共同具有以下治理字段：

- `source_artifacts`：当前输入 completion 所绑定文件的相对路径和哈希；
- `authority_partition`：作者锁定、自主拥有、开发自由和作者开放的精确集合；
- `design_decisions`：当前技能作出的全部自主决定；
- `derivation_claims`：重要业务值、来源控制点、来源决定和规范值哈希；
- `open_items`：原样保留且带来源的开放问题。

每项非平凡 `design_decision` 必须记录：要解决的缺口、至少两个真实方案
（确实只有一个可行方案时必须说明排除证据）、选择、权限依据、与全部上游模型的
兼容性、影响对象、代价、可撤销性、下游自由和实际投影对象。只列建议、不作选择，
或作出选择但没有进入 canonical 对象，都不得 `ready`。

S1 输出给 W1/E1/T1/C1 的需求，以及 W1 输出给 E1 的需求，不能是只有 ID 的占位符。
每个需求必须同时包含唯一 ID、目标阶段、责任、来源对象、所需能力、约束、验收条件
和下游自由。下游必须逐 ID 消费当前上游需求；增加、遗漏或替换 ID 都属于输入契约
失败，不能由下游自行解释。

S1 的 `environment_requirements` 与 W1 的 `environment_demands` 是两个来源不同的
E1 输入集合。E1 必须把前者原样记录为 `storyline_environment_requirements`，把后者
原样记录为 `environment_demands`，分别验证来源并对两者完成环境承载；不得以 W1
输出覆盖或遗忘 S1 的直接环境义务。

`derivation_claims` 必须对声明值计算规范 JSON 哈希。字段发生变化后旧 claim 自动失效；
Q1 必须复核全部设计决定和派生声明，P1 不得重新生成或替换它们。

### 3.7 B0：不可变作者控制基线

B0 由 harness 确定性生成，不执行创作、摘要或推断。它把以下内容封装为
`author-control-baseline` 包：

- 进入自主阶段前冻结的 source interview run-state；
- I0–I5 completion 及其六份权威设计产物的完整原文；
- V1、V2 completion 和当前 V2 作者批准；
- 从六份设计产物稳定 ID 与精确标题确定性抽取的控制点索引；
- V1 completion 绑定的 `fact-dependency-register.json`；
- 作者已经采用的事实研究包与采用记录；
- 仍需保留的事实依赖和作者开放项。

B0 validator 必须独立读取六份权威设计产物并重新抽取每域 control ID，再与
`design_artifacts[].control_ids` 和 `control_registry` 做三方集合相等及域／artifact
绑定检查。不得用 B0 自己声明的 `control_ids` 反向证明自身无损。

B0 ready 包必须包含：

```text
author-control-baseline.json
control-coverage.md
baseline-execution.json
validation.json
package-manifest.json
stage-completion.json
```

`author-control-baseline.json` 只索引和绑定原始值，不把它们改写为摘要。包 manifest
必须直接绑定六份权威设计产物，保证 P1 可以交付完整作者控制层。

事实依赖只允许：

- `not_applicable`：当前构思不依赖外部事实；
- `adopted`：绑定研究包、作者采用记录、允许用法和虚构边界；
- `open`：只能是非结构性问题，必须保持开放，不得被 W1 当成事实使用。

结构性事实依赖未研究或未获作者采用时，B0 必须 `blocked`，不得进入 S1。研究本身
仍由访谈工作流的条件研究支线完成，不属于自主构思技能。
B0 不负责发现或解释事实依赖；V1 必须交付当前 register，即使结论只是一个明确的
`not_applicable`。缺少 register 不能用空数组代替。

若 W1 或更后阶段的自主决定产生一个 B0 未登记、且不能诚实落入已有 fiction
boundary 的结构性现实主张，发现者不得自行检索后写入世界事实。workflow 生成
`upstream_reentry` return，唯一 owner 为 I2，`target_stage=I2`，
`resume_stage=B0`。I2 的条件研究支线、I3–I5、V1、V2 和作者重新批准完成后，
新的 B0 以 `return_resolution` 模式绑定该 return，旧 B0–H1 全部 superseded。
非结构性主张也只能登记为新的 `author_open`，不能作为当前世界规则使用。

### 3.8 H1 复合阶段状态机

H1 是一个顶层阶段，内部状态固定为：

```text
initialized
  → planned
  → fragments_ready
  → assembled
  → rendered
```

`h1-workspace-state.json` 必须绑定同一 `h1_session_id`、P1 completion 和每个内部包
manifest。每次状态提升都由 harness 重新验证前态和新增包，记录前态哈希；不得手写、
跳级、回退覆盖或混用其他 session 的 plan、fragment、assembly、HTML。
其机器契约为
[`h1-workspace-state.schema.json`](contracts/autonomous-v2/h1-workspace-state.schema.json)。

- plan、fragment、assembly、HTML 各自有 manifest 和 validation；
- 内部包只能由同一 H1 workspace 的下一状态消费；
- 内部包不对其他顶层阶段暴露 completion；
- workspace 到达 `rendered` 后，harness 统一重验四包并生成 H1
  `stage-completion.json`；`ready` 是顶层 H1 completion 状态，不再写回 workspace，
  避免 completion 与 workspace 互相包含哈希；
- 任一内部包变化都会撤销旧 H1 completion、作者决定和最终 conception completion。

### 3.9 自主 run-state 与阶段拓扑

自主阶段不得继续复用只记录 I0–I5 的访谈 run-state 充当当前版本索引。harness
必须在 B0 前创建 `autonomous-run-state.json` revision 0，之后每次状态变化生成新的
不可覆盖快照。其唯一公共契约是
[`autonomous-run-state.schema.json`](contracts/autonomous-v2/autonomous-run-state.schema.json)。

状态快照唯一记录：

- 当前 B0–H1 completion；未完成或已失效的阶段不得留在 current 集合；
- 当前 H1 workspace；
- 唯一 active return 和所有 resolved return；
- superseded completion；
- 当前作者决定与开发失效状态；
- 前一状态的路径和哈希。

B0 中的 `run_state` 是进入自主阶段前冻结的来源状态；每个阶段 completion 绑定执行前
状态；协调器在验收 completion 后生成下一状态。completion 不得引用包含自己的后态，
从而避免哈希自循环。作者批准写入最新状态后，最终 completion 单向绑定该状态；
run-state 不反向保存 final completion。只要之后产生任何新状态，旧 final completion
就不再绑定最新状态并自动失去开发准入资格。

阶段输入拓扑固定为：

| 目标 | baseline | `upstream_completions` 精确顺序 |
| --- | --- | --- |
| B0 | `null` | `[]` |
| S1 | B0 | `[]` |
| W1 | B0 | `[S1]` |
| E1 | B0 | `[S1,W1]` |
| T1 | B0 | `[S1,W1,E1]` |
| C1 | B0 | `[S1,W1,E1,T1]` |
| Q1 | B0 | `[S1,W1,E1,T1,C1]` |
| P1 | B0 | `[S1,W1,E1,T1,C1,Q1]` |
| H1 | B0 | `[P1]` |

输入门只允许两种互斥模式：

- `forward`：`active_return` 与 `return_binding` 必须为 `null`；
- `return_resolution`：只允许 return 指定的 `resume_stage` 进入，输入门和新 completion
  必须逐值绑定同一个 return；其他阶段继续被 active return 阻塞。

以上顺序由
[`input-gate.schema.json`](contracts/autonomous-v2/input-gate.schema.json) 与
[`stage-completion.schema.json`](contracts/autonomous-v2/stage-completion.schema.json)
共同约束，不能由技能自行选择上游。

Schema 只能约束单份状态的结构。coordinator validator 还必须读取 active
`return-request.json` 并执行以下跨文件不变量：

- current completion 精确等于 `resume_stage` 之前的前缀；
- `invalidated_stages` 中没有对象仍留在 current；
- 完整 H1 失效时清除当前 H1 workspace；
- resolved return 的 completion stage 等于其 `resume_stage`；
- resolving completion 必须属于 current 或 superseded，且不得重复解析同一 return。

缺少 active return 正文或其绑定引用时，不得只凭 run-state 中的一条 artifact reference
声称失效已经执行。

## 4. S1：故事线架构设计

### 4.1 目标

从所有批准的构思控制点中发现小说需要承担的故事义务，从主体、对抗、关系、信息、机构、历史、主题和后果等维度设计完整故事线，使任何重要方向都有可追踪的起点、推进、变化和终点，并共同还原同一个故事主体。

“完整”不等于故事线越多越好。每项需求必须被独立成线、并入其他线、设为背景压力、设为可选旋律线，或有证据地判定不适用。

### 4.2 职责

- 扫描全部权威输入，建立 `storyline_demands`；
- 设计全部结构故事线和必要背景线；
- 区分 `precursor / main / supporting / background / optional_melody`；
- 为每条线定义职责、主体角色槽、压力、起点、阶段性状态变化和终点；
- 定义 `merge / split / handoff / collision / reveal / synchronization` 连接；
- 明确入口线、唯一主干、终点线和所有非主线进入主干的路径；
- 把作者锁定的因果、先后、共同前提与信息边界登记为可机器消费的故事义务；
- 对全部 B0 控制点建立精确来源定位和关系型义务处置，禁止静默遗漏；
- 检查各线对同一事实、时间前后和结局性质的解释一致；
- 输出下游世界、环境、事件和角色需求。

### 4.3 边界

- 不设计完整世界系统；
- 不定义具体地点；
- 不把状态变化细化为全局事件；
- 不创建完整人物档案或关系网络；
- 不划分章节、场景或 POV 调度；
- 不把旋律线用于承担主体因果、决定性信息或结局闭合。

允许引用访谈中已经锁定的人名、世界事实和因果节点；新增承担者只能先登记为 `actor_slot`，由 C1 决定规范人物。

### 4.4 输入硬准入

必须绑定：

- 当前 B0 completion、manifest 和完整 `author-control-baseline` 包；
- B0 权威验证器只读重验为 `ready`；
- 输入门通过 3.9：正常前进没有 active return；若 S1 是唯一恢复阶段，则使用
  `return_resolution` 并绑定当前 return；
- S1 的 `input_gate` 精确绑定 B0 manifest，不另行解释聊天或旧稿。

### 4.5 canonical 交付

`storyline-architecture.json` 的必需业务字段：

- `source_artifacts`
- `authority_partition`
- `design_decisions`
- `derivation_claims`
- `storyline_demands`
- `storylines`
- `connections`
- `architecture`
- `temporal_architecture`
- `story_claim_units`
- `story_claim_atoms`
- `story_obligation_register`
- `story_obligation_coverage`
- `cross_line_consistency`
- `world_requirements`
- `environment_requirements`
- `event_requirements`
- `character_requirements`
- `coverage_ledger`
- `open_items`

每条故事线必须定义：稳定 ID、类型、职责、主体角色槽、目标、压力、起点状态、按顺序的状态变化、终点状态、连接点、来源决定和下游自由。

运行时从 B0 控制值确定性重建 `story_claim_units`。显式箭头链的每对相邻节点分别
形成 required unit；编号项、编号相邻 candidate、表格行、句子与结构化叶子分别
登记。每个 unit 必须由一个 `story_claim_atom` 恰好处置一次。编号相邻 candidate
可判为非关系，但必须留下理由并进入语义复核，不得把普通编号分类强制解释为时序。

`story_obligation_register` 每项必须含稳定 `SOB-` ID、义务类型、精确 claim atom
来源、前件状态锚点、后件状态锚点、可证伪理由和验收条件。允许的义务
类型只有 `causes / strict_before / not_before / requires_all /
first_disclosure / must_remain_unknown`。信息义务还必须带稳定 `PROP-` ID 和受众。

`story_obligation_coverage` 必须与 B0 控制点集合精确一一对应，并聚合该控制下
全部 claim atom 与 obligation；一个控制点可以一对多。作者锁定控制点登记为
`obligated`、`mixed`，或在确实不表达跨状态/跨线关系时登记为
`no_relational_obligation` 并强制交 Q1 语义复核；作者开放控制点保持
`author_open`，不得被 S1 擅自硬化。

### 4.6 ready 硬门

- 全部故事线需求集合精确覆盖；
- 每项需求恰好一个处置结论；
- 所有结构线都有起点、变化和终点；
- 所有非主结构线都通过连接路径作用于主干；
- 连接点两端真实存在且状态兼容；
- 每项故事义务的来源 locator 与 B0 artifact/hash/value hash 精确一致；
- source units 与运行时确定性分解逐值一致，每个 unit 恰好一个 atom；
- 显式箭头链的每个相邻 link 分别拥有独占义务，首尾义务不能冒充中间覆盖；
- atom、obligation 与 control-level coverage 的双向索引集合完全相等；
- 每个义务锚点的故事线、状态索引与状态文本三者一致；
- 单线义务不倒序，合并后的因果/先后义务图无环；
- 每个 `causes/requires_all` 前件可沿线内前向状态边和精确 causal SLC 抵达后件；
  反向早期连接与 associative 连接不计入因果可达；
- 同一命题与受众只有一个首次披露点，保密窗口不越过首次披露点；
- 全部 B0 控制点恰有一个故事义务处置，义务与覆盖记录双向索引一致；
- 背景线能持续改变条件，而不只是背景介绍；
- 删除任一结构线都会产生可指出的因果、主题、关系或信息缺口；
- 可选旋律线删除后主体因果、结局、POV 和决定性信息仍完整；
- 不含世界、环境、事件或人物阶段越权决定。

### 4.7 受控生成阶段

```text
demand-scan
  → line-design
  → topology-and-consistency
  → downstream-requirements
  → final-storyline-model
```

## 5. W1：虚拟世界构建

### 5.1 目标

根据全部故事线构建环境、事件和角色可以共同运行的虚拟世界，使世界规则既能支持故事发生，又能主动制造机会、限制、成本、失败和后果。

### 5.2 职责

- 将每条故事线转化为世界能力与压力需求；
- 定义世界时空、现实关系和虚构边界；
- 定义物理、技术、社会、政治、经济、法律／伦理、信息和历史八类信息；
- 设计机构、权力、资源、权限和信息流；
- 设计运行系统的输入、转化规则、输出、行动者、成本、限制和失败；
- 证明全部故事线在同一世界中能够并存；
- 生成具体环境设计需求。

### 5.3 边界

- 不定义具体主要环境及功能分区；
- 不建立全局事件时间线；
- 不创建人物档案；
- 不新增与任何故事线无关的百科设定；
- 不利用新技术、新权限或新资源绕过已确认冲突。

### 5.4 输入硬准入

- S1 completion 和完整 S1 manifest；
- S1 `ready` canonical 验证结果；
- 当前 B0 completion、manifest 和完整作者控制基线；
- B0 与 S1 所绑定的 baseline manifest 完全相同；
- 同一 run，且输入门通过 3.9 的 forward／return-resolution 互斥校验。

W1 必须直接读取 B0 中的 I2 世界契约、I0/I1 约束和 I5 叙述边界；不得把 S1
对世界的需求投影误当成全部作者事实。W1 不得读取聊天或旧地图补事实。

### 5.5 canonical 交付

`world-model.json` 的必需业务字段：

- `storyline_requirements`
- `world_definition`
- `world_facts`
- `reality_claims`
- `world_facets`
- `history_pressures`
- `institutions`
- `systems`
- `resource_flows`
- `authority_flows`
- `information_flows`
- `rule_conflict_matrix`
- `storyline_support_ledger`
- `environment_demands`
- `open_items`

每个系统必须定义：输入条件、行动者、资源、权限、转化规则、可观察输出、成本、限制、失败方式、状态变化和所支持的故事线。

每条 `reality_claim` 必须引用一个 B0 fact dependency：

- `adopted`：同时引用研究包、采用记录和允许用法；
- `open`：只能声明当前构思不依赖该答案，不能把候选当作世界事实；
- `not_applicable`：说明该项属于明确虚构或不主张现实正确性。

遇到 B0 未登记的结构性现实主张时必须执行 3.7 的 I2 研究回退，不得把
`not_applicable` 当作逃避研究的标签。

### 5.6 ready 硬门

- 所有结构故事线和背景线均有世界承载证明；
- 每项关键冲突至少受一项世界规则、系统或资源约束；
- 所有系统输入、输出和权限闭合；
- 机构、资源、权力和信息流不存在自相矛盾的双重所有权；
- 失败方式真实存在，不能只有成功路径；
- 世界规则不能提供未经授权的便捷解法；
- 所有新增世界事实均有 S1 需求或作者控制点来源；
- 所有外部事实主张都由 B0 `adopted` 依赖支持，虚构内容明确落在 fiction boundary；
- 环境需求覆盖全部需要具体承载条件的故事线阶段。

### 5.7 受控生成阶段

```text
requirement-projection
  → world-rules-and-history
  → systems-and-flows
  → cross-line-world-test
  → final-world-model
```

## 6. E1：具体环境定义

### 6.1 目标

把故事线和虚拟世界展开为具有边界、功能、资源、权限、风险和转场条件的具体环境，使后续事件能够在可观察、可行动且自洽的场域中发生。

### 6.2 职责

- 从全部故事线阶段和世界系统建立 `environment_demands`；
- 发现全部主要环境，而不是先做地点清单；
- 定义环境范围、特征、感知条件、准入和控制；
- 定义功能区、资源、人员类型、允许行动、阻断和危险；
- 定义环境之间的连接、距离性质、转场条件和信息通道；
- 定义环境的状态词汇、允许转换和转换所需条件；不决定哪次事件实际触发转换；
- 证明每条故事线所需行动有具体环境承载。

### 6.3 边界

- 不决定事件何时发生、由谁发起和产生什么结果；
- 不进行镜头、走位、尺寸、装饰和场景调度；
- 不创建仅出现一次且不承担控制职责的偶发地点；
- 不修改世界系统；发现不足时建立 W1 return request。

### 6.4 输入硬准入

- S1、W1 当前 completion 和 manifest；
- 当前 B0 completion、manifest 和完整作者控制基线；
- S1、W1 canonical 模型重新验证为 `ready`；
- W1 对 S1 的来源绑定仍然有效；
- B0、S1、W1 绑定同一 baseline manifest；
- 同一 run，且输入门通过 3.9 的 forward／return-resolution 互斥校验。

### 6.5 canonical 交付

`environment-system.json` 的必需业务字段：

- `storyline_environment_requirements`
- `environment_demands`
- `story_transition_universe_digest`、`milestone_universe_digest`、
  `connection_universe_digest`、`obligation_universe_digest`
- `environments`
- `initial_anchor_support`
- `functional_zones`
- `environment_topology`
- `access_and_authority`
- `resource_and_information_channels`
- `hazards_and_failure_modes`
- `storyline_hosting_ledger`
- `event_affordance_catalog`
- `transition_contracts`
- `capability_fact_registry`、`capability_step_registry`
- `ambient_context_hosts`、`actor_authority_bindings`
- `capability_occurrence_requirements`
- `story_transition_support`、`connection_path_readiness`
- `milestone_capability_readiness`、`obligation_capability_readiness`
- `initial_anchor_option_realization_ledger`
- `open_items`

每个主要环境必须定义：范围、叙事职责、特征、可感知条件、准入、资源、允许行动、危险、功能区、区间连接、阻断、状态变化和所承载的故事线阶段。

### 6.6 ready 硬门

- 全部环境需求精确覆盖；
- `storyline_environment_requirements` 与 S1 `environment_requirements` 逐值相等，
  `environment_demands` 与 W1 输出逐值相等；
- 每条结构故事线至少有可验证的环境承载路径；
- 每个主要环境至少承担一个不可被其他环境等价替代的故事职责；
- 功能区和环境连接形成可达拓扑；
- 人员、资源、权限和信息通道支持声明的行动；
- 风险与阻断会对行动产生后果；
- 不含尚未定义的具体事件结果；
- 不以装饰性描述冒充环境能力。
- 当前生产模型固定为 `schema_version: 2.4`。每个承载记录必须把同线的一个
  W1 环境需求和一个 S1 环境要求配成一对，并以结构化证据逐项绑定：来源类型、
  责任规范哈希、全部约束规范哈希、实现环境、受限的环境本地 JSON Pointer、
  本地值哈希和解释。两个来源及其全部 token 在该实现集合内必须精确覆盖一次；
- 环境本体只写本地可执行定义，不复制完整上游责任、追溯标签或其他故事线原文。
  本身就是局部操作规则的单条约束可以原样出现在 `access_rules`、`blockers` 或
  `hazards`，但不得堆入范围、叙事职责、特征等说明字段；
- `event_affordance_catalog` 是环境局部行动接口目录，不是事件覆盖台账。每个 EVD
  至少有一个 affordance；同一 EVD 可以在多个同线承载环境提供不同局部接口。
  affordance 中的全部行动都必须属于对应环境，且不得复制同一语义接口。共享环境
  只向 affordance 施加其实际服务故事线的约束。每 EVD 的精确事件实现由 T1 负责；
- P1 从已封存 S1 重算全部相邻状态转换、里程碑、连接和义务的四个规范摘要；
  P2 为每个 state-0 冻结至少一个确定 ID 的环境能力选项；P4 对全部选项精确实现，
  不得在后阶段新增、改写或漏掉选项；
- P3 必须建立全局 fact-step-authority-occurrence 图。fact 来源使用 S1/W1/E1 封闭
  oneOf，绑定受信 artifact、JSON Pointer 与值哈希；producer/consumer 双向相等，
  前置图无环，权限 token 用精确环境/affordance/action 三元组约束签发与消费。E1
  初态来源只能指向已封 P2 环境的 `state_vocabulary`、`resources` 或 `access_rules`
  唯一值，其 subject ID 由环境、类型、指针和值确定生成，不接受自报来源；
- P4 对全部 S1 相邻状态转换、里程碑、连接和义务逐项给出 readiness。支持模式必须
  属于本地 step；纯 constrain 只有在受审查 ambient host 存在时可用；causal 连接
  必须有端点 step、传递 fact 和必要的连续拓扑路径，associative 连接不得伪造因果。
  消费传递 fact 的目标端 step 不得同时支撑连接目标锚点之前的状态转换；真实需要时
  使用局部 endpoint step，锚点当时或之后的复用仍由结构顺序与语义评审判断；
- P3 authority review 与 P4 transition-support review 都必须在写 evidence 前通过。
  两个请求都显式绑定 session/input-gate、全部先前 evidence、候选、S1/W1
  completion/manifest、实现/schema/protocol 和 reviewer task receipt；P4 还绑定 P3
  review。每次评审密封为 candidate/request/review/validation/manifest 五件套，阶段
  evidence 引用 manifest，public validation 重算完整评审包。任一绑定变化、漏 claim、
  多余文件或失败 verdict 都不得写本阶段 evidence；
- 五个阶段都必须在写本阶段证据之前完成当时可判定的完整结构与闭包验证。
  最终阶段还必须证明模型是已封 P1–P4 的精确投影；失败时不得留下本阶段证据，
  也不得改写此前证据；
- 生成会话冻结 E1 runtime、schema、技能说明及必要上游实现的摘要。上述实现任一
  变化都会使旧会话失效，必须新开 attempt；不能把改版后的包降标为 `2.0/2.1/2.2/2.3`
  绕过新门。历史包只在其打包 runtime/schema 摘要属于受信历史配对，且 manifest、
  completion 与 canonical 摘要命中精确已发布包身份时只读接受；重贴标签或全量重封均拒绝。

### 6.7 受控生成阶段

```text
environment-demand-scan
  → environment-architecture
  → zones-and-topology（先完成独立权限／能力语义评审）
  → storyline-hosting-test（再完成独立转场承载语义评审）
  → final-environment-model
```

P1 精确投影、配对 S1/W1 并冻结四个完整性摘要；P2 验证环境、设计决策和初态能力
选项；P3 验证功能区、拓扑、权限、通道、风险、转换、affordance 及全局能力图，
并完成权限语义评审；P4 验证结构化承载、全部 readiness、初态选项实现及转场语义
评审；P5 验证 P1–P4 精确投影和完整模型。当前生产只生成 2.4；2.0/2.1/2.2/2.3
仅用于有受信历史来源的只读验证。

## 7. T1：时间线与事件定义

### 7.1 目标

把所有故事线投影到同一世界时间线上，用完整主要事件实现各线的状态变化和连接，使小说从最早因果变化经由人物行动、反制和代价抵达最终余波。

### 7.2 职责

- 从故事线状态变化建立 `event_demands`；
- 区分世界时间、背景时间、事件发生时间和叙述披露时间；
- 定义全部主要事件及因果前驱；
- 将 S1 `story_obligation_register` 投影为事件级命题与义务实现；
- 为事件明确声明所需、产生和披露的命题，不从自然语言结果反推；
- 将故事线连接点落实为共享事件或可验证的信息／责任交接；
- 将每个事件放入具体环境；
- 定义发起行动、对抗或复杂化、决定性变化、结果和下一压力；
- 维护信息、资源、权限和世界状态账本；对尚未由 C1 解析的人物，只记录角色槽的
  行动结果、关系状态需求和目标状态需求；
- 证明每条故事线都有完整事件序列。

### 7.3 边界

- 不重新定义故事线职责；
- 不修改世界规则或环境能力；
- 不完成角色心理和关系档案；
- 不按章节或叙述顺序代替世界因果顺序；
- 不把多个分别改变关键状态的步骤压成一个汇总事件。

发现世界或环境无法承载事件时，生成定向 return，不得在事件模型中偷偷增加权限、地点或技术。

### 7.4 输入硬准入

- S1、W1、E1 当前 completion 和 manifest；
- 当前 B0 completion、manifest 和完整作者控制基线；
- 三个 canonical 模型均重新验证为 `ready`；
- B0、S1、W1、E1 绑定同一 baseline manifest；
- 来源链连续、同一 run，且输入门通过 3.9 的 forward／return-resolution 互斥校验。

### 7.5 canonical 交付

`event-timeline.json` 的必需业务字段：

- `event_demands`
- `event_span`
- `timeline_axes`
- `initial_condition_registry`
- `initial_anchor_option_selection_ledger`
- `planned_event_registry`
- `process_state_subject_registry`
- `planned_proposition_registry`
- `planned_causal_edges`
- `transition_event_cover`
- `milestone_event_buckets`
- `connection_event_paths`
- `obligation_event_plan`
- `capability_occurrence_event_cover`
- `authority_token_instance_ledger`
- `lifecycle_scope`
- `lifecycle_contract_registry`
- `proposition_registry`
- `major_events`
- `causal_edges`
- `storyline_event_sequences`
- `connection_realization`
- `obligation_realizations`
- `environment_placement`
- `state_ledger`
- `information_changes`
- `event_coverage_ledger`
- `narrative_timing_constraints`
- `open_items`

每个主要事件必须定义：稳定 ID、事件职责、世界时间位置、故事线、环境、参与角色槽、发起者槽、对抗者槽、前提、发起行动、反制或复杂化、决定性变化、直接结果、前后状态、下一压力、所需／产生／披露命题、信息变化和因果前驱。

T1 不接受仅靠文字看起来合理的时序。运行时必须根据结构字段重新验证 S1 的
`causes`、`strict_before`、`not_before`、`requires_all`、`first_disclosure`、
`must_remain_unknown`，并阻断无因果祖先的前提、提前披露、伪造首次披露和重复终局。
当前 2.5 还要求每个事件披露的命题在 P4 形成至少一个原子 `information_changes`
记录：记录只绑定一个事件、一个命题和该事件内一个支持 `communicate` 的 E1 occurrence；
subject 必须是可见的参与角色槽，可见槽必须由该 capability step 接纳。S1
`first_disclosure` 还必须穿透 E1 obligation occurrence binding 与 T1 occurrence cover
闭合。事件与信息记录双向索引，空信息账本只在全模型没有披露时成立。

当前 2.5 把叙事因果、capability、proposition、token 与 sequencing 依赖分型，
并以 `lifecycle_scope`、`lifecycle_contract_registry` 和权限实例账本闭合正式接受、
许可生产、启动与关停的有效发生顺序。故事线终态 `story_transition` 必须是该线最后一个
transition-span／状态变化事件；只有当 E1 `connection_path_readiness.transport_step_ids`
无重复精确覆盖完整 `source anchor → ordered connection_bridge → target anchor` 路径时，
才允许在终态锚点后保留属于源故事线的非状态 causal SEND bridge。任何生命周期或状态
effect、错线／外来／重复 bridge、端点绕过、目标锚点后的动作或非 bridge 尾随事件都失败。

T1 的人物相关状态是 `slot-level requirement`，不是人物心理、关系语义或人物弧决定。
它回答“事件要求承担者发生什么可观察变化”；C1 回答“哪个人物承担、为何这样选择、
关系对双方意味着什么”。C1 若无法形成可信人物，只能 return T1 或更早阶段，不能
静默改写事件。

### 7.6 ready 硬门

- 全部故事线状态变化和连接需求被事件实现；
- 时间线从最早因果变化覆盖到最终余波；
- 每个非起始事件至少有一个真实前驱；
- 因果图无非法环；
- 世界规则、资源、权限和环境能力支持每个事件；
- 每个重要结果都有发起者、反制者或可信的无反制理由；
- 每个事件只有一个主导状态变化；
- 信息、资源、权限和世界状态连续；角色槽的行动、关系需求和目标需求连续；
- 叙述约束不会提前暴露禁止信息；
- 不用后续事件的 `preconditions` 代替应该真实存在的前序事件。
- 当前生产模型固定为 `schema_version: 2.5`、语义审查协议
  `t1-initial-event-plan-semantics-v5`，且只接受当前 E1 `2.4` 生产契约作为新会话输入；
  T1 `2.0`–`2.4` 仅在打包 runtime/schema 摘要命中受信历史配对、manifest/completion/canonical
  命中精确已发布包身份，并通过包内历史 schema 与历史 phase/lineage 重放时只读接受。
  其中 2.3 只保留了一份精确的完整实现绑定快照，没有发布过 ready package；因此实现
  provenance 可以审计，但 package identity inventory 显式为空，完整 package replay 保持关闭；
  2.4 的受信 implementation-pair 与 ready-package identity inventories 都显式为空，因此同样
  fail closed。历史版本不得新建、重封或被用于给当前结果降标；
- 每个 `(EVD,event)` 实现必须由该事件 placement 中至少一个同环境 affordance
  精确承载：该 affordance 必须包含该 EVD、允许事件发起行动且其前置条件全部进入
  事件前置条件。同线但属于其他 EVD 的 affordance 不能替代，未服务该事件任何 EVD
  的多余 affordance 也不得出现在 placement；
- `cross-line-state-test` 在写 P4 evidence 前，必须用已封 P1–P3 与 P4 候选组装完整
  provisional 模型并通过全量验证；P5 和公开包验证继续重算。

### 7.7 受控生成阶段

```text
event-demand-scan
  → global-timeline
  → event-and-causality-model
  → cross-line-state-test
  → final-event-model
```

## 8. C1：角色系统定义

### 8.1 目标

根据全部故事线、世界、环境和事件发现小说实际需要的人，使每项决定、信息、能力、对抗、行动、关系压力和后果都有具备动机、能力与权限的承担者。

### 8.2 职责

- 扫描七类人物需求：决定权、信息传递、能力形成、对抗执行、关系压力、行动执行和后果承担；
- 把 S1/T1 的角色槽解析为规范人物；
- 为核心与支持人物完成命名和档案；
- 定义目标、价值观、盲点、边界、信息限制、能力、权限和受压行为；
- 定义不可委托选择与能动性；
- 定义人物变化弧和不变边界；
- 建立全局人物关系边；
- 从每位核心人物出发重算至少三层最短路径人物网络；
- 反查每条故事线、每个事件和每个终局后果的承担者。

### 8.3 边界

- 不修改故事线、世界、环境或事件；
- 不为满足数量制造空壳人物；
- 不用组织、岗位或国家标签冒充具体人物；
- 不把价值选择写成现实操作权限；
- 不预写人物对白、动作清单或完整传记；
- 发现角色无法完成事件时生成 T1 或更早阶段 return。

C1 拥有人物心理、关系语义、关系杠杆和人物弧；不得改变 T1 已锁定的可观察事件
结果。T1 的槽级关系／目标变化是 C1 的需求输入，不与 C1 的人物定义形成双重所有权。

### 8.4 输入硬准入

- S1、W1、E1、T1 当前 completion 和 manifest；
- 当前 B0 completion、manifest 和完整作者控制基线；
- 四个 canonical 模型重新验证为 `ready`；
- 角色槽、事件参与、环境准入和世界权限引用集合完整；
- B0 与四个生成包绑定同一 baseline manifest；
- 同一 run，且输入门通过 3.9 的 forward／return-resolution 互斥校验。

### 8.5 canonical 交付

`character-system.json` 的必需业务字段：

- `character_demands`
- `slot_resolution`
- `profiles`
- `responsibility_matrix`
- `agency_matrix`
- `information_matrix`
- `character_arcs`
- `relationships`
- `three_layer_networks`
- `storyline_cast_coverage`
- `event_cast_coverage`
- `aftermath_responsibility`
- `development_freedoms`
- `open_items`

每个结构或支持人物必须定义：姓名、故事职责、目标、价值观、边界、能力、权限、信息限制、受压行为、能动选择、不可委托选择、关系杠杆、变化方向和禁止写法。

每个 `development_freedoms` 条目必须使用唯一 `DEV-` ID，绑定真实 canonical
`subject_ids` 和 `source_ids`，明确允许变化、禁止改变及验收条件。其 ID 只属于
`authority_partition.downstream_freedom`，不得同时进入 `autonomous_owned`；人物档案、
关系、人物弧和设计决定仍是 C1 权威控制信息，不能作为开发自由 ID。

### 8.6 ready 硬门

- 七类人物需求精确覆盖；
- 所有结构性角色槽解析为唯一人物；
- 所有故事线、主要事件和终局后果都有规范承担者；
- 发起者和反制者具备动机、能力、权限和可达环境；
- 信息只能由拥有信息且存在传递路径的人获得；
- 核心与支持人物均完成命名；
- 每位核心人物具有真实三层人物关系网络；
- 每个外延人物都有职责、目标、边界、信息限制、受压行为和能动选择；
- 没有人物仅为传递信息、解决技术问题或承担后果而存在却没有自己的选择逻辑；
- 不含对前四阶段模型的静默修改。

### 8.7 受控生成阶段

```text
character-demand-scan
  → slot-resolution-and-profiles
  → agency-and-relationships
  → cross-model-cast-test
  → final-character-model
```

## 9. Q1：完整性与一致性审查

### 9.1 目标

独立证明 S1–C1 共同形成一部完整、逻辑一致、真实可发生、能够支撑主题且可进入开发的小说构思。

### 9.2 职责

- 重新验证全部五个包和来源链；
- 检查故事线完整性与线间一致性；
- 检查世界对全部故事线的承载；
- 检查环境对全部事件行为的承载；
- 检查事件因果、时间和状态连续；
- 检查人物动机、能力、权限、信息与行动匹配；
- 检查主题是否通过选择和后果被检验；
- 分别检查外部事实依据和虚拟世界内部一致性；
- 检查开放项、作者边界和开发自由；
- 检查便捷解法、巧合推进、工具人和无承担者结果；
- 为每条 finding 指定唯一拥有者和最小重跑范围；
- 给出 `ready / revise / blocked`。

### 9.3 边界

- 不修改任何 S1–C1 模型；
- 不提出新的故事答案；
- 不组装正式构思交付物；
- 不写人审摘要或小说片段；
- 不按个人审美、市场偏好或固定结构模板制造问题；
- 不用平均分掩盖硬门失败。

### 9.4 输入硬准入

- S1–C1 五个 completion、manifest 和 canonical 模型；
- 当前 B0 completion、manifest 和完整作者控制基线；
- 五个包同一 run，来源链连续；
- 五个权威验证器只读重验结果与存储结果完全一致；
- B0 与五个生成包绑定同一 baseline manifest；
- Q1 语义审查任务 ID 不同于 S1–C1 的生成任务；
- Q1 交接测试任务 ID 不同于 S1–C1 和 Q1 语义审查任务；
- 输入门通过 3.9 的 forward／return-resolution 互斥校验。

### 9.5 canonical 交付

`conception-review.json` 的必需业务字段：

- `input_gate`
- `domain_reviews`
- `cross_domain_checks`
- `reality_claim_review`
- `coverage_recalculation`
- `consistency_matrix`
- `causal_challenges`
- `easy_solution_challenges`
- `development_usability_test`
- `quality_coverage`
- `handoff_test_evidence`
- `findings`
- `return_request`
- `verdict`

每条 finding 必须包含：严重度、问题、故事专属证据、受影响对象、违反的契约、唯一拥有者、所需修订和最小重跑范围。

### 9.6 ready 硬门

- 五域对象集合和所有跨域引用重新计算一致；
- 故事线、世界、环境、事件和角色覆盖无缺口；
- 没有 contradictory、revise 或 blocked finding；
- `review-plan` 精确登记全部 S1/T1 带 ID canonical 对象，不得抽样；
- T1 `2.2+` 的 planned event/proposition/causal edge 只有在与对应 canonical registry
  按正式投影契约完全闭合时才折叠为一个审查对象；指纹绑定 canonical 完整对象与
  canonical pointer，任何缺失 counterpart、字段漂移或第三来源均拒绝；
- 独立开发者只凭 B0 和五个 `ready` 包，能够复述主体、追踪任一故事线、定位任一事件条件、解释任一核心人物选择、识别开发自由，并完成 chronology reconstruction、causal precondition trace、information release trace 与 author control trace；
- 后四项 trace 的 assertion binding 证据并集覆盖全部 S1 obligation 与 T1 realization；`quality_coverage.required_objects` 与 `covered_objects` 逐项一致，且未解决阻断质量记录为空；
- 审查证据引用对象中的故事专属内容，不是字段存在性或模板化结论。

Q1 必须分成两个上下文隔离的任务：

1. `semantic-reviewer`：可读取 B0、五个模型和其生成证据，负责领域及跨域审查；
2. `handoff-evaluator`：只能读取 B0、五个 canonical ready 包及 manifest，禁止读取
   聊天、访谈报告、生成 evidence、semantic reviewer finding 和预期答案。

`handoff-evaluator` 先生成独立 `handoff-test-evidence.json`；semantic reviewer 只能在
测试封存后读取该证据并形成最终 verdict。两者的允许文件清单、任务 ID 和读取范围
必须写入 execution record。仅改变角色字符串或在同一任务内声称“已清空上下文”
不构成隔离。

Q1 controller 还必须在冻结输入时封存 current runtime、schema、SKILL 与审查协议的
完整 implementation catalog 和 canonical digest。五阶段每个状态机入口及最终 package
构建都在首次写入前重算并要求 exact；实现发生变化后，旧 controller、partial semantic
或 handoff 证据不得继续。public validator 对包内 catalog 的集合、路径身份、artifact
哈希、current source 哈希与封存 digest 做同一重放，不能只验证包内文件自洽。

### 9.7 受控审查阶段

```text
review-plan
  → domain-challenges
  → cross-domain-challenges
  → development-handoff-test
  → final-review
```

## 10. P1：机器构思交付物组装

### 10.1 目标

把通过 Q1 的作者控制基线和五个 canonical 模型组装成一个机器可消费、版本明确、无内容漂移的小说构思交付包。

### 10.2 职责

- 重新验证 S1–Q1；
- 直接收录 B0 的六份权威设计产物、控制点索引和已采用事实依据；
- 合并而不改写 canonical 内容；
- 建立跨模型索引和追溯关系；
- 明确作者锁定、自主决定、开放项和开发自由；
- 生成面向 AI 开发者的完整构思规格；
- 生成不可变 manifest 和技术交接 completion。

### 10.3 边界

- 不做任何生成式构思；
- 不修复上游内容；
- 不新增摘要性结论成为权威事实；
- 不写小说片段；
- 不生成 HTML；
- 不代替作者批准。

### 10.4 输入硬准入

- B0、S1–C1 和 Q1 当前 completion、manifest；
- Q1 verdict 为 `ready`；
- 所有包同一 run、绑定同一 baseline manifest 且重新验证一致；
- 输入门通过 3.9 的 forward／return-resolution 互斥校验。

### 10.5 canonical 交付

P1 包必须包含：

```text
novel-conception-package.json
author-control-baseline.json
authoritative-design-artifacts/
novel-conception-spec.md
cross-model-index.json
traceability-matrix.md
development-handoff.json
assembly-execution.json
validation.json
package-manifest.json
stage-completion.json
```

`novel-conception-package.json` 直接嵌入或哈希引用作者控制基线与五个模型的完整
权威值，不重新概括为另一套事实。`authoritative-design-artifacts/` 保存 B0 manifest
绑定的六份权威原文；故事承诺、主体定义和叙述契约不能只以来源路径存在。
为避免 canonical package 与 `development-handoff.json` 形成不可构造的双向哈希环，
canonical package 只用严格 `pathReference` 定位 handoff；handoff 用完整
`artifactReference` 强绑定 canonical package，manifest 再分别强绑定两份最终文件。

P1 聚合的 `authority_partition.downstream_freedom` 保留 WR、END、EVD、CHD、SLOT
等阶段交接 ID 和 C1 `DEV-` ID，供追溯阶段授权历史；但
`development-handoff.json.development_freedoms` 只能精确投影 C1
`development_freedoms[].id`。已由后续构思阶段解析的需求或角色槽不得作为小说开发
自由重新开放。旧 C1 缺少 `development_freedoms`、旧 E1 缺少
`storyline_environment_requirements` 时必须 schema 失败并重新生成，不提供静默兼容。

### 10.6 ready 硬门

- B0、五个模型和 Q1 精确绑定；
- P1 独立重算当前 S1/T1 全部带 ID 对象，并确认 Q1 `quality_coverage` 全量、逐哈希一致且无未解决阻断质量记录；
- `novel-conception-package.json.quality_admission` 绑定当前 Q1 review、覆盖口径、应审／已审数量和零阻断记录；
- 所有 ID、引用和开放项保持不变；
- 机器包可反解析回作者控制基线、六份权威设计产物和五个 canonical 模型的等价值；
- Markdown 与 canonical 包确定性一致；
- 交接清楚区分必须遵守、可以开发和必须回问；
- manifest 完整绑定全部交付物和当前实现；
- 相同输入重复运行得到字节一致的 canonical 包与 Markdown。

P1 是确定性技能，只需一次受控执行记录，不得伪造生成式阶段。

### 10.7 已发布 P1 的崩溃恢复

P1 采用 exact existing recovery，处理已经完整发布且与当前调用精确一致的既有包。
若目标目录存在，runtime 必须在任何 staging、删除或写入之前只读执行以下检查：

1. 用正式 P1 validator 重验既有包的全部文件、validation、manifest、completion、
   输入快照、执行记录和实现快照；
2. coordinator 精确满足下列一种状态：
   - 仍处于 completion 绑定的执行前状态，current completion 集合尚未包含 P1；
   - 仅对 forward 模式，已持久化 successor 的 `previous_state` 等于上述执行前状态
     引用、current P1 completion 等于既有 completion，且 successor reference path
     等于本次 `next_state_path`；
3. 本次 sealed input gate 与包内记录逐值相同，包括模式、上游顺序和完整 return
   binding；
4. 当前 B0–Q1 正式来源包全部重验通过，且其 completion、manifest、canonical、
   baseline、lineage、文件清单和 SHA-256 与既有包的来源绑定完全相同；
5. 调用 coordinator 前再次比较来源清单，关闭恢复路径的 TOCTOU 窗口。

全部成立时，runtime 必须原样使用既有 `stage-completion.json` 调用 coordinator，
不能改动 P1 目录中的任何字节。执行前状态中的 valid non-current orphan 由
coordinator 首次接纳，返回 `P1RunReceipt.replayed=true` 和
`transition.replayed=false`；精确 forward successor 走 persistent replay，两个
`replayed` 都为 `true`。

return-resolution completion 已进入 `resolved_returns` 后严格 one-shot：runtime
必须原样抛出 `COORD_RETURN_ALREADY_RESOLVED`，不产生新的 receipt。

partial、无效、被篡改、stale、绑定其他 gate、其他执行前状态或其他来源集合的目录必须
fail closed，原地保留取证，不得覆盖、删除、合并或自动修复。实现快照不等于当前实现
同样属于 stale；旧实现生成的包（包括 A4 旧快照）不可复用，必须在新目标目录重新执行。
该恢复协议是 runtime 行为，不改变现有 JSON Schema。

## 11. H1：人审报告内部技能链

### 11.1 顶层目标

让作者在十分钟内只通过四个内容维度判断当前构思是否是他想要的：世界设定（含故事运行所需环境控制）、故事线设计（含主要事件架构）、角色定义、样章。明确决定是四维内容之后的操作，不构成第五个评审维度。

H1 的内容权威只能来自当前 P1 包。

### 11.2 H1-A 报告设计与组装

技能：`novel-conception-human-review-assembler`

职责：

- `plan`：设计报告信息架构、阅读预算、可视语义模型和片段 briefs；
- `assemble`：确定性合并通过验收的片段；
- 保证报告与 P1 内容一致；
- 保证所有关键控制信息在默认可见路径中出现。

报告的三个构思主板块固定为：

1. 小说世界设定：世界模型与具体环境；
2. 小说故事线设定：全部故事线、连接架构、时间线与主要事件；
3. 小说人物设定：人物职责、选择、弧线和关系网络。

小说片段和作者判断分别作为验证与决策区，不得拆散三个构思主板块或另造一套事实。

输入：

- P1 completion、manifest 和完整包；
- P1 权威验证器重验为 `ready`。
- 当前 H1 workspace 处于 `initialized`，且绑定上述 P1 completion。

`plan` 交付：

```text
source-inventory.json
review-plan.json
fragment-briefs.json
generation-session.json
generation-evidence/*.json
execution-record.json
validation.json
package-manifest.json
```

报告设计属于生成式工作，必须至少经过：

```text
review-task-analysis
  → information-architecture
  → visual-and-fragment-plan
  → ten-minute-budget-test
  → final-review-plan
```

`visual-and-fragment-plan` 必须显式提交并由 final plan 原样绑定：

- `decision_prompts`；
- `assembly_projection`：为报告标题及世界、故事线、角色的每个报告字段
  指定同板块 module id，控制数组无重叠地覆盖该板块全部 module；
- `presentation_bindings`：精确覆盖全部 module、visual、brief、prompt，
  记录完整元素内容哈希、按原顺序绑定的 P1 source anchor/value 哈希、
  `must_not_imply` 与 challenge 结果。

每个 fragment brief 还必须由 Agent 显式给出固定
`zh-Hans-review-v1`、`restrained-concrete-scene-v1`、
`third_person_limited`、信息可知与禁知边界、允许感知通道、完整
before/goal/pressure/obstacle/choice/consequence/after 场景契约、
`process-only-no-unresolved-decision-disclosure` 和
`fragment-local-non-authoritative-v1`。这些是 H1-B 控制信息，纳入 brief
完整内容哈希与 P1 value bindings，但不属于作者默认可见阅读文本。

运行时只重算并核验上述绑定，不替 Agent 推断报告分类、生成内容或选择
source anchor。缺项、多项、旧哈希、跨板块投影及最终阶段临时注入均拒绝。

全部默认可见 module、所属板块 visual、全部 fragment slot 与全部 decision
prompt 构成唯一有序 registry。五步 `review_path` 必须按 kind 精确覆盖该
registry；`control_coverage` 只能指向路径中真实存在且实际绑定该 anchor 的
元素；五个 `budget_items` 必须按路径顺序逐项绑定 PATH id 与相同秒数。
ghost、漏项、重复、跨 kind、错误 anchor 映射和预算漂移一律拒绝。

阅读时长固定采用 `review-reading-baseline-v1`：中文 400 字/分钟、Latin
200 词/分钟，混合文本两项相加；每个 visual 固定增加 10 秒理解开销，每个
decision prompt 固定增加 15 秒判断开销。片段按对外可见 brief 文本加
`target_words_max`，并以 Latin 词速保守计量。运行时从 registry 实际文本
重算各 kind 最低秒数，PATH 不得低报，调用方不得配置阅读速率。

`assemble` 交付：

```text
human-review-report.json
human-review-report.md
assembly-execution.json
validation.json
package-manifest.json
```

plan 与 assemble 的 manifest 都必须绑定同一 `h1_session_id` 和
`h1-workspace-state.json` 前态哈希。assemble 只能在 `fragments_ready` 状态消费
当前 plan 和 fragment manifest。

assemble 还必须接收 H1-B 实际消费的 `planned` workspace，要求
`fragments_ready.previous_state_sha256` 精确指向它；通过函数内动态调用正式
H1-B validator 完整重验 fragment 包后，H1-A 只核对 brief 投影并逐字复制正文，
不得保留测试适配依赖或复制 H1-B 领域验收逻辑。

`fragment-package.json` 必须直接携带完整片段记录，并复用
`human-review-report.schema.json#/$defs/fragment`；只有片段 id 而没有标题、
评审用途、正文和来源的包不得进入 assemble。

边界：

- 不修改构思；
- 不直接写小说片段；
- 不生成 HTML；
- 不记录作者决定。

### 11.3 H1-B 小说片段

技能：`novel-conception-fragment-writer`

输入：

- 验证通过的 review plan；
- 当前 P1 包；
- 由 plan 确定性导出的 fragment briefs。
- 当前 H1 workspace 为 `planned`，且 plan、briefs 与 P1 均属于同一 session。

交付：

- 三阶段生成证据；
- `fragment-package.json`
- `fragments.md`
- `execution-record.json`
- `validation.json`
- `package-manifest.json`

约束：

- 片段只验证阅读体验，不成为设定权威；
- 不新增世界事实、事件结果、人物历史或开放项答案；
- 固定使用版本化评审基准文风；
- 必须满足 POV、信息、选择、状态变化、长度和 brief 证据；
- 不写最终章节。

fragment manifest 必须绑定 H1 session、plan manifest、P1 completion、三阶段证据和
当前片段技能实现；通过后 harness 才能把 workspace 提升为 `fragments_ready`。

### 11.4 H1-C HTML

技能：`novel-conception-review-html-generator`

输入：

- assembly、plan、fragment 和 P1 四个包；
- 四包全部重新验证为 `ready`。
- 四包属于同一 H1 session，workspace 当前状态为 `assembled`。

交付：

```text
human-review-report.html
render-record.json
validation.json
package-manifest.json
```

约束：

- 只做确定性呈现；
- 不改写、摘要或删减内容；
- 单文件、离线、可打印、可访问；
- 图形必须有文字等价信息；
- 不加载外部资源；
- 不预选、保存或提交作者决定。

HTML manifest 必须绑定 plan、fragment、assembly、P1 和 H1 workspace 前态哈希。
HTML 验证通过后先提升为 `rendered`；harness 再统一重验四包，生成 H1
`stage-completion.json`。`ready` 只属于顶层 H1 completion；workspace 保持
`rendered`，不写入不存在的 ready 状态。

### 11.5 已发布 H1 的崩溃恢复

正式 H1 completion 采用只读、精确的 existing-package recovery，但不把 H1-A、
H1-B、assemble 或 H1-C 提升为新的顶层阶段。若 `H1/stage` 已存在，publisher
必须先用当前正式 validator 完整重验 package manifest、validation、execution
record、canonical completion 与当前实现快照，并逐值绑定当前 rendered workspace、
P1、plan、fragments、assembly、HTML、plan input gate、执行前状态及其文件清单。
恢复验证期间，既有目录与全部当前输入的 inventory 必须保持不变。

只允许两种 coordinator 状态：

1. coordinator 仍在 completion 记录的精确执行前状态，H1 尚未 current；接纳该
   orphan 后 `H1CompletionReceipt.replayed=true`，
   `transition.replayed=false`；
2. 仅限 forward 模式，coordinator 是精确持久化的 `waiting_author` successor，
   其 `previous_state`、current H1 completion、rendered H1 workspace 和
   successor reference path 均与本次调用一致；此时两个 `replayed` 都为 `true`。

partial、tampered、stale、foreign、绑定不同 gate、来源、实现或 next-state path
的目录全部 fail closed，原地保留且不得覆盖或修复；正式 `CoordinatorError` 原样
传播。原子发布竞态仅可恢复一个独立通过上述全部校验的精确赢家。

公开 `run_from_rendered_h1` 的新执行仍要求 `output_root` 不存在或为空。崩溃重试
唯一允许的非空形态是精确的 `H1/stage` 目录，且必须先完成上述恢复，再消费外部作者
决定。预置 D1、R1、author-decision、completion/final/terminal 或任何额外残留
必须在调用 H1 publisher 前拒绝。该能力不覆盖已消费作者决定或 approved、revise、
rejected、final 的部分事务，也不新增作者决定 basename 约束。

## 12. 最终作者决定与构思 completion

作者决定由工作流层接收，不属于 HTML 技能，也不需要新增创作技能。

正式文件改名为 `author-decision.json`，避免用 approval 表示 revise 或 rejected。
其唯一权威契约是
[`author-decision.schema.json`](contracts/autonomous-v2/author-decision.schema.json)，
使用 `oneOf` 定义三个互斥分支并设置 `additionalProperties: false`。

三个分支共同绑定当前 P1 manifest、H1 completion 和 HTML：

```json
{
  "schema_version": "2.0",
  "run_id": "RUN-ID",
  "approval_scope": "conception",
  "decision": "approved",
  "machine_package": {
    "completion_path": "...",
    "completion_sha256": "...",
    "manifest_path": "...",
    "manifest_sha256": "..."
  },
  "human_review_package": {
    "completion_path": "...",
    "completion_sha256": "...",
    "manifest_path": "...",
    "manifest_sha256": "...",
    "html_path": "...",
    "html_sha256": "..."
  },
  "approval_record": {
    "event_seq": 1,
    "text": "作者明确决定的原文"
  },
  "unresolved_items": []
}
```

只允许 `approved / revise / rejected`。

- `approved`：包含明确批准原文；生成最终 `conception-completion.json`；
- `revise`：包含 `revision_targets[]`。作者只需指出 `target_scope`、可见报告元素或
  artifact ID、相关 source ID（若问题属于构思内容）和修改要求；workflow 根据
  source ID、artifact 类型与 14.1 所有权表计算唯一 owner，作者不填写 owner；
- `rejected`：包含明确拒绝原文，关闭当前构思 run，不产生开发准入。

纯报告、片段或 HTML 问题可以没有 P1 source ID，但必须引用当前 H1 artifact element；
构思内容问题必须至少引用一个 P1 source ID。workflow 生成的 return request 记录
计算出的 owner 和依据。

最终 `conception-completion.json` 必须绑定：

- 批准后的最新 autonomous run-state；该状态必须没有 active return，且 current
  completion 集合与下列引用完全相等；
- B0 completion、manifest 和 validation；
- P1 manifest 和 validation；
- P1 `stage-completion.json`；
- H1 `stage-completion.json`、HTML manifest 和 validation；
- 当前 author decision；
- S1–Q1 completion 链；
- `development-handoff.json` 的路径和哈希。

主 harness 重新验证全部内容后，才允许进入小说开发。

## 13. 正式调用链

```text
I0–I5 + V1 + V2 + V2 author approval
  │
  ▼
B0 immutable author-control baseline
  │ ready
  ▼
S1 storyline architecture
  │ ready
  ▼
W1 world model
  │ ready
  ▼
E1 environment system
  │ ready
  ▼
T1 event timeline
  │ ready
  ▼
C1 character system
  │ ready
  ▼
Q1 semantic review ◄── sealed handoff-evaluator evidence
  │ ready
  ▼
P1 deterministic conception package
  │ ready
  ▼
H1-A plan
  │
  ├──► H1-B fragments ──┐
  │                     ▼
  └──────────────► H1-A assemble
                        │
                        ▼
                     H1-C HTML
                        │
                        ▼
                  H1 stage completion
                        │
                        ▼
                   author decision
                        │ approved
                        ▼
             conception-completion.json
                        │
                        ▼
                  novel development
```

不得跳过顶层 B0、S1–P1、H1 completion，不得让后序顶层阶段读取未封包工作区，
不得用当前聊天替代任何输入包。H1 内部只允许按 3.8 状态机消费同一 session 的
sealed manifest，不能把内部 manifest 冒充顶层 completion。

### 13.1 唯一生产调度入口

新构思必须由 `novel-conception-autonomous` 调度技能启动。运行时入口为
`runtime.production_orchestrator.initialize_production_run`；任何后续进程或 Agent
只能通过 `resume_production_run` 从最新的持久状态继续。调度器必须：

1. 以 `dependency-spec.json` 作为 S1–H1-C 唯一 owner 注册表；
2. 在每个动作前签发一个绑定当前 state、input gate、owner 和输入引用的不可变工作单；
3. 执行与孤儿恢复必须携带工作单中的精确 actor；不匹配时在调用语义 executor 前拒绝，
   只接收该 owner 正式 runtime 返回的 receipt，不允许手写 completion 或语义备用 owner；
4. 将每个顶层 state 和 H1 workspace 以 append-only 哈希链持久化；
5. 将 H1 publish、外部作者决定和 approved-only final 分成可独立恢复的事务；
6. P1 就绪后通过 `initialize_h1_workspace` 建立唯一 H1 session：同 session 重试幂等，
   活跃 workspace 不得被另一 session 替换；仅 P1 绑定改变或密封 H1 返工允许新 session；
7. 仅在 owner validator 证明现有包完全有效后恢复崩溃产生的包孤儿。

每个 successor 落盘前还必须先写不可变 commit-intent；调度器须从持久 predecessor、
精确 gate 与 owner completion/manifest 重建 fresh coordinator 并重算完整 successor，
只有 data 与 reference 全量相等才可准备 intent。作者返工还须绑定本轮 sealed
return-request 与唯一 `return_id`；恢复不得依据“字段形状相似”推断成功。

旧 `runtime.harness.run_from_rendered_h1` 只保留给已经拥有完整 rendered H1 的兼容
调用，不能作为“访谈结果 → 小说构思”的生产入口。旧 D1/R1 及
`novel-development-map-designer` 不得出现在生产 owner 集合或正式发布依赖中。

## 14. 回退与失效规则

### 14.1 唯一拥有者

| 问题 | 唯一拥有者 |
| --- | --- |
| 故事线缺失、职责重复、连接或主干错误 | S1 |
| 世界规则、系统、历史、机构、资源、权限或信息机制错误 | W1 |
| 环境、功能区、拓扑、准入、资源或承载能力错误 | E1 |
| 时间、事件、因果、状态变化或线—事件投影错误 | T1 |
| 人物、动机、能力、权限、信息、关系或责任错误 | C1 |
| 漏审、错判、finding 或责任路由错误 | Q1 |
| 组装、索引、渲染或 manifest 漂移 | P1 |
| 报告信息架构、覆盖或预算错误 | H1-A plan |
| 报告组装与已验收 plan／fragment 不一致 | H1-A assemble |
| 片段语义、POV、风格或 brief 对齐错误 | H1-B |
| HTML 忠实性、可访问性、安全或确定性错误 | H1-C |
| 作者锁定项本身需要改变 | 对应 I0–I5 |
| 作者控制基线封装、事实采用绑定或控制点索引错误 | B0／对应 I0–I5 |
| 自主阶段发现未登记的结构性现实事实依赖 | I2；完成条件研究与重新批准后从 B0 恢复 |

### 14.2 定向 return

后序技能不能修改前序产物。发现问题时，由 workflow router 确定性生成：

```text
return-request.json
next-run-state.json
blocked-report.md
validation.json
```

return 必须包含：

- 问题及故事专属证据；
- 受影响对象 ID；
- 违反的契约；
- 唯一拥有者；
- `local_revision / upstream_reentry / author_revision` 类型；
- 实际 `target_stage`、自主链恢复阶段 `resume_stage` 和内部 `resume_point`；
- 所需修订；
- 失效的下游阶段；
- H1 内部失效 artifact；
- 是否撤销当前作者决定；
- 是否撤销最终 conception completion。

同一 run 同时只能有一个活动 return。return 协议固定为：

1. router 根据 14.1 所有权表和受影响 source ID 生成 return，技能或作者不得填写 owner；
2. coordinator 生成新 run-state，移除 `invalidated_stages` 的 current completion，
   把旧引用加入 superseded，并登记 active return；
3. 只有 `resume_stage` 可以用 `return_resolution` 输入门进入；其他阶段全部阻塞；
4. 恢复阶段的新 completion 必须复制输入门的完整 `return_binding`；
5. coordinator 重验 return、输入门、新 completion 和失效集合后，生成下一状态：
   active return 变为 `null`，resolved return 增加解析记录，恢复阶段 completion 成为 current；
6. 从恢复阶段之后按正常 forward 模式重跑；不得恢复旧下游 completion；
7. 作者决定与最终 completion 只有在新的 H1 再次批准后才能重新产生。

若 owner 属于 I0–I5，`target_stage` 是对应访谈阶段，但自主链
`resume_stage=resume_point=B0`；必须完成访谈 return、V1/V2 和作者重新批准后，
B0 才能解析该 return。若 owner 属于 H1-A/B/C，顶层 `resume_stage=H1`，
内部恢复点固定为：

| owner／问题 | 恢复点 | H1 恢复状态 | 失效内部包 |
| --- | --- | --- | --- |
| H1-A plan／信息架构、覆盖、预算 | `H1-A-plan` | `initialized` | plan、fragment、assembly、HTML、H1 completion |
| H1-B | `H1-B` | `planned` | fragment、assembly、HTML、H1 completion |
| H1-A assemble／组装漂移 | `H1-A-assemble` | `fragments_ready` | assembly、HTML、H1 completion |
| H1-C | `H1-C` | `assembled` | HTML、H1 completion |

当 `fragments_ready` 已形成且当前唯一工作单为 `H1-A-assemble` 时，独立呈现一致性
审查若以 `revise` 证明错误属于 H1-A plan，唯一入口是公开的
`apply_internal_h1_plan_return`。事务必须逐字绑定候选报告、当前 P1、plan／fragment
manifest、两位生产者身份和待组装工作单；审查者 task/thread 均不得与生产者复用。
候选报告与审查必须在回退事务前由独立任务封存；orchestrator 不得代审查者创建或
落盘审查证据。调度器先以 `assign_internal_h1_plan_fidelity_review` 锁定真实 reviewer
task/thread、候选、workspace、manifest 与 assemble 工作单；该 reviewer 再以专属 actor
调用 `record_internal_h1_plan_fidelity_failure`，回退入口只消费其受保护 completion。
普通 `persist_document` 不得创建 assignment、review 或 completion，调用方临时构造或
预先落盘的伪身份文件均不得被入口接纳。
成功后旧 plan、fragment、候选报告、失败审查和 assemble 工作单全部保留为不可变证据，
旧工作单被拒绝，创建新 initialized workspace，并只签发新的 H1-A-plan gate/order。
缺审查、伪造独立身份、跨内部 owner、旧状态或重复使用同一失败证据均须零写入拒绝。

正式结构由
[`return-request.schema.json`](contracts/autonomous-v2/return-request.schema.json)
约束；run-state 解析记录由
[`autonomous-run-state.schema.json`](contracts/autonomous-v2/autonomous-run-state.schema.json)
约束。schema 之外，router validator 必须证明 owner、失效后缀和恢复点是确定性计算结果。

### 14.3 下游失效

某阶段 canonical 模型发生变化后，该阶段之后的全部 completion 自动失效：

| 修订阶段 | 必须重跑 |
| --- | --- |
| I0–I5 任一权威产物 | B0、S1–H1；撤销作者决定与最终 completion |
| V1、V2 或 V2 批准 | B0、S1–H1；撤销作者决定与最终 completion |
| B0 | S1–H1；撤销作者决定与最终 completion |
| S1 | W1–H1 |
| W1 | E1–H1 |
| E1 | T1–H1 |
| T1 | C1–H1 |
| C1 | Q1–H1 |
| Q1 | P1–H1 |
| P1 | H1 |

E1 `2.4` 是能力与 readiness 语义升级，不是 2.3 包的标签迁移。启用 2.4 后，旧
E1 completion 及其 T1–H1 后缀失去 current 资格；旧包保持只读不改写。只有新的
2.4 E1 通过两类语义评审、五阶段 evidence 与 public replay 后，coordinator 才能
重新为当前 T1 颁发输入门。T1 的生产版本升级同理使 C1–H1 后缀失效。

E1 2.4 的 direct obligation 通过 `obligation_occurrence_bindings` 逐条绑定
obligation、selected anchor support、capability step 与 occurrence requirement。
共享 capability step 不会把全局所有 occurrence 强行归给每条 obligation；两条义务可
各自拥有独立 occurrence。漏绑、串绑、错 step/support 或多报均在 P4 evidence 写入前拒绝。

生产迁移由 `apply_contract_upgrade()` 执行，不允许只修改版本常量。它先密封一个
全新且未解析过的 local-revision return，再写 append-only prepared plan，绑定前态、
完整后态、旧/新 contract digest、生产版本表与失效后缀。active E1/T1 session、全部
未消费 work order 及 current completion 必须由协调器从密封运行目录自动扫描、逐项
校验真实路径和 SHA；调用者给出的引用只可作为与扫描结果完全相等的断言，不能扩张或
缩小失效范围。升级目标也不能由调用者决定：协调器按 E1→T1 顺序读取真实 current
completion 的 canonical 版本与 identity，选择第一个 stale contract；伪造的 T1 目标
不能越过仍为 2.3 的 E1。session inventory 只含尚未 completion 且尚未 invalidated 的
session，避免把历史终态重复失效。随后追加 state revision，并密封 complete、session invalidated、
work-order rejected、completion invalidated 与 commit-intent abandoned 收据。恢复器只完成同一个
prepared plan，不生成第二个后态。迁移后的 E1/T1 work order 必须绑定当前 upgrade
receipt、owner schema version 和 upstream schema versions；T1 在 executor 启动前重读
当前 E1 canonical，版本不是 `2.4` 即拒绝。上述事务只改变 current 资格和调度状态，
不会改写旧 E1/T1 包。新运行初始化时即密封 current contract qualification；resume、
reconcile、E1/T1 签发和执行都重放该资格及全部失效收据，缺失或过期时不得继续。
唯一例外是正式 stale-run 迁移入口：它可在 qualification 缺失或过期时进入
`apply_contract_upgrade()`，但在升级完成前仍不能普通 resume 或签发 E1/T1。连续升级
必须在前一次收据生效后重新从真实 completion 计算下一目标，并使用互不冲突的不可变
收据；重复同一升级则幂等恢复原事务，而不是制造第二条状态链。
这里的 identity 不是版本字符串：它包含 completion、manifest、validation、canonical
引用，runtime/schema/protocol implementation bindings 及 semantic-review protocol
集合，并要求 stage public validator 完整重放。qualification 在每次 resume、reconcile、
issue 与 execute 前从 current completion 重新计算该身份；即使 canonical 仍标 current
版本，只要任一实现、协议或包链引用漂移也会判为 stale。
| H1-A plan | H1-B、assemble、HTML、H1 completion |
| H1-B | assemble、HTML、H1 completion |
| H1-A assemble | HTML、H1 completion |
| H1-C | HTML、H1 completion |
| P1、H1 completion 或 HTML 发生任何变化 | 撤销作者决定与最终 completion |
| author decision 失效或被替换 | 撤销最终 completion 和开发准入 |

旧包保持不可变，只取消“当前”资格；不得覆盖旧包制造看似连续的哈希链。
开发已经开始后若最终 completion 失效，既有开发产物不删除，但全部标记
`stale_input`，在新 conception completion 产生并完成影响分析前不得继续交付。

## 15. 全局硬验收

工作流级 validator 必须检查：

1. 同一 run 和唯一当前版本；
2. 最新 autonomous run-state 通过 schema 与语义重验，current completion 是合法前缀；
3. B0、S1–P1、H1 completion 链符合 3.9 的精确阶段拓扑；
4. 没有未解析 active return；所有 resolved return 都绑定恢复输入门和修正 completion；
5. 所有 manifest、文件和实现哈希有效，package profile 的必需角色全部在 files 中；
6. B0 可无损还原六份权威设计产物，事实依赖全部合法处置；
7. S1–C1 与 B0 绑定同一 baseline manifest；
8. S1 需求到故事线全覆盖；
9. 故事线到世界需求、系统和环境需求全覆盖；
10. 环境到事件承载全覆盖；
11. 故事线状态变化到事件全覆盖；
12. 事件角色槽到人物全覆盖；
13. 所有跨模型 ID 有效；
14. 所有开放项保持开放；
15. 所有作者锁定项值不变；
16. 所有自主决定只有唯一拥有者；
17. 所有状态、信息、资源、权限和关系变化连续；
18. Q1 semantic reviewer 与 handoff evaluator 任务隔离、读取范围和故事专属证据有效；
19. W1 外部事实主张与 B0 fact dependency 逐条闭合；
20. P1 可无损还原作者基线、六份权威设计产物和五个 canonical 模型；
21. H1 四包属于同一 session，状态转换连续；
22. 人审报告与 P1 内容一致；
23. HTML 与人审报告确定性一致；
24. 作者决定通过对应 oneOf 分支并同时绑定机器包、H1 completion 和 HTML；
25. 最终 completion 指向当前 `development-handoff.json`；
26. 最终 completion、author decision、P1 和 H1 均为当前版本。

任一失败都不得进入小说开发。

## 16. 实现顺序

重构必须按依赖顺序进行：

1. 实现并验证 `contracts/autonomous-v2` 公共 schema；
2. 实现 autonomous run-state coordinator、阶段拓扑 validator 和 return router／resolver；
3. 实现 B0 基线封装、事实依赖门和 completion；
4. 实现 S1；
5. 实现 W1；
6. 实现 E1；
7. 实现 T1；
8. 实现 C1；
9. 重构 Q1，分离 semantic reviewer 与 handoff evaluator；
10. 实现 P1 和 `development-handoff.json`；
11. 把 H1-A 输入改为 P1，补齐受控 plan 生成链和 H1 workspace；
12. 把 H1-B 输入从 R1 改为 P1；
13. 把 H1-C 输入从 R1 改为 P1，并只推进到 rendered workspace；
14. 实现统一 H1 completion、author decision 2.0 和最终 completion；
15. 更新主 harness、全局编排文档和端到端回归；
16. 用通用样例和《断线》各完成一次 forward test。

在 S1–P1 和最终 approval 契约完成前，不得把旧 D1/R1 包自动迁移为 V2 `ready`。

## 17. 必须通过的端到端契约场景

实现不能只验证 happy path。正式准入前必须通过：

| 场景 | 必须结果 |
| --- | --- |
| 正常批准 | B0、S1–P1、H1 连续 ready；approved decision 生成最终 completion |
| Q1 定向退回 W1 | 状态移除 W1–H1；只有 W1 可带 active return 进入；新 W1 completion 绑定 return 后清空 active return，再从 E1 前进 |
| 作者要求修改构思 | revise target 引用 P1 source ID；workflow 计算 S1–C1/I0–I5 owner，撤销相应下游 |
| 作者只要求修改报告或 HTML | revise target 引用 H1 可见元素，不强迫伪造 P1 source ID，只重跑 H1 对应内部阶段 |
| 结构性现实事实未研究或未采用 | B0 blocked；不得进入 S1，W1 不得以“常识”补写 |
| 任一 I0–I5 权威产物变化 | baseline hash 改变；S1–H1、作者决定和最终 completion 全部失去当前资格 |
| 混用两个 H1 session 的 plan 与 fragment | parent state/session 校验失败；不得组装或生成 H1 completion |
| 非恢复阶段尝试消费 active return | input gate 的 `resume_stage` 校验失败；不得生成候选模型 |
| Q1 handoff evaluator 读取 semantic finding 或生成 evidence | evidence scope 校验失败；Q1 不得 ready |
| author decision 分支夹带其他分支字段 | `oneOf` 与 `additionalProperties: false` 校验失败 |
| 最终 completion 缺任一 B0/S1–P1/H1 completion | conception completion 校验失败，不得进入开发 |
| 开发开始后构思 completion 失效 | 开发产物标记 `stale_input`，完成新基线影响分析前停止交付 |

每个反例只改变被测缺陷，避免用多重错误掩盖 validator 漏检。
