# 小说 HLD 自主工作流 V1：Harness、技能与硬契约设计

> 规范状态：V1 设计已冻结。本文件只定义目标与流程；当前实现、Agentic 验证和发布资格只能以 Harness `manifest.yaml`、机器验收记录及发布清单三者一致的状态为准。
>
> 上游唯一正式入口：`novel-development-baseline-preparer` 生成且重新验证通过的 ready 包。
>
> 下游目标：生成经过作者批准、可直接启动 LLD 的正式 HLD 交付包。
>
> 14 个技能的逐项定义、输入和输出硬契约见 [`hld-skill-contract-catalog-v1.md`](hld-skill-contract-catalog-v1.md)。

规范性规则：本文件定义目标、边界、阶段关系和人类可读流程；技能目录是技能名、artifact role、字段、输入顺序、source access、verdict 代数和包 profile 的唯一实现契约。两者若出现同义词、字段或权限不一致，不得自行选择其一，也不得由 prompt 临时解释；实现前必须先修订技能目录，再同步本文件并通过跨文档一致性检查。

## 1. 设计结论

HLD 不是一份“构思总结”，也不是一份提前写细节的 LLD。它负责把已经批准的小说构思，组织成一套可执行的宏观叙事架构：小说按什么结构推进，多条故事线如何编排，人物弧线如何落位，信息和悬念如何释放，时空、节奏、张力和 POV 如何协同，以及哪些关键场景功能必须存在。

完整生产形态必须是 `novel-hld-autonomous` harness，而不是一个包办所有工作的 `novel-hld-writer`。Harness 负责状态、门禁、唯一 owner、定向退回、作者决定和最终准入；领域技能只负责一个边界明确的判断或确定性处理。

技能组合分为四组：

| 组别 | 数量 | 作用 |
| --- | ---: | --- |
| 设计技能 | 6 | 构建 HLD 的六个相互依赖的设计模型 |
| 独立评审技能 | 2 | 分别检查语义质量和 LLD 可消费性 |
| 交付与呈现技能 | 4 | 组装机器包、人审报告、忠实性审查和 HTML |
| 确定性门禁技能 | 2 | 准入正式基线、封闭最终交付 |

合计 14 个边界明确的 bounded skill；它们由一个 harness 编排，不得互相替代。

## 2. HLD 的目标、职责、边界与约束

### 2.1 目标

把一份冻结、作者批准且可追溯的小说构思，转换为：

1. 完整的宏观叙事结构；
2. 覆盖全部必要故事线的编排方案；
3. 与事件一致的人物弧线落位；
4. 可执行的 POV、读者信息、悬念与揭示控制；
5. 连续的时空、节奏与张力架构；
6. 足以由 LLD 展开的关键场景功能集合；
7. 无需 LLD 猜测高层结构的正式交接包。

### 2.2 HLD 必须完成

- 决定小说的结构层级、叙事阶段、幕／部／章推进关系和高层转折位置；
- 将构思中的主线、支线、背景线、人物线、情感线、主题线及可选旋律线映射到叙事单元；
- 定义故事线的进入、并行、交叉、接力、汇合、退出和回收关系；
- 将既有人物弧线、关系变化、关键选择与既有事件落到叙事单元；
- 定义 POV 权限、角色知识、读者知识、隐藏信息、误判、探针、揭示和回收顺序；
- 定义故事时间、叙事顺序、压缩／展开、空间迁移、节奏、张力和恢复窗口；
- 定义关键场景的叙事功能、进入条件、必须完成的状态变化和退出条件；
- 证明所有 HLD 决定都来自作者控制或明确的开发自由；
- 形成机器可消费 HLD、人类可审 HLD 和 LLD 交接包。

### 2.3 HLD 不得完成

- 不修改或补写构思阶段的世界规则、环境定义、主要事件、人物档案、关系事实、主题和结局；
- 不把新的主要人物、主要环境、主要事件或世界事实偷偷写成 HLD 决定；
- 不裁决 `must_ask` 或作者有意保留的开放问题；
- 不定义逐场景动作、对白、感官材料、摆设、镜头、行为微表征或具体叙事段落；
- 不写小说正文或样章；
- 不以固定幕数、固定章节数、固定故事线数或固定关键场景数代替故事需要；
- 不把人审报告、Markdown 或 HTML 当作内容权威；
- 不让后序技能直接修改前序 canonical 模型。

### 2.4 HLD 与构思、LLD 的判界

| 问题 | 所属阶段 |
| --- | --- |
| 故事世界、人物、事件、故事线“是什么” | 构思 |
| 这些既有内容“怎样组成一部完整小说” | HLD |
| 每个场景“具体发生什么、如何被写出来” | LLD |
| 最终叙事文字 | Writing |

边界测试：

- 若内容改变了故事事实，退回构思 owner；
- 若内容决定了宏观位置、关系、顺序、功能或信息边界，属于 HLD；
- 若内容已经能直接回答人物做了什么、说了什么、看见了什么，属于 LLD；
- 若内容是可发表的叙事文本，属于 Writing。

### 2.5 V1 scope freeze

| 项目 | 冻结决定 |
| --- | --- |
| Mission | 从正式 development baseline 生成作者批准、可进入 LLD 的 HLD |
| Canonical upstream | `novel-development-baseline-preparer` ready package；不接受其他内容入口 |
| Canonical downstream | `lld-handoff.json` 与 `hld-completion.json` |
| Human gate | 必需；V1 不提供无人批准直通 LLD 的模式 |
| Portable core | runtime-independent harness 语义、schema、规则、eval 和 validator |
| 首个 runtime | Codex；其他 runtime 在有独立 adapter、eval 和 release validation 前均标记 unsupported |
| Required tools | 只读源文件访问、JSON Schema、SHA-256、受控生成会话、离线 HTML/SVG 渲染 |
| Release target | source package + Codex runtime package；不得仅交付 prompt 或 `SKILL.md` |
| Non-goals | LLD 设计、正文写作、市场评估、事实研究、构思修订和发布小说 |

低风险假设只有：上游 preparation 契约保持兼容、构思源在 HLD run 内不可变、作者可在最终门或 `required_now` 问题处给出外部事件。任何会改变上述三项的情况都不能由 Agent 自行假设。

## 3. Harness 形态与固定调用图

本工作流采用“review-gated self-improving generation harness”。设计阶段按固定顺序前进，HQ1 语义审查、HQ2 正式 handoff 消费验收和作者决定都是硬门；失败只能携带结构化 return 回到最早责任 owner，禁止无边界重试。

```text
正式 development baseline
        │
        ▼
HB0 基线准入与 HLD 控制面封装
        │ ready
        ▼
HA1 总体叙事架构
        │ ready
        ▼
HS1 多故事线编排
        │ ready
        ▼
HC1 人物弧线落位
        │ ready
        ▼
HI1 POV、信息与悬念架构
        │ ready
        ▼
HR1 时空、节奏、张力与连续性架构
        │ ready
        ▼
HK1 关键场景功能综合
        │ ready
        ▼
HQ1 HLD 语义与开发可用性审查
        │ ready
        ▼
HP1 机器 HLD 与 LLD handoff 组装
        │ ready
        ▼
HQ2 consumer task（只读 handoff）
        │ sealed pass
        ▼
HQ2 fidelity task（新上下文对照机器包）
        │ sealed pass
        ▼
HQ2 composite publisher（非 skill）
                │ ready
                ▼
HH1-A 人审报告组装
                │
                ▼
HH1-B 独立呈现忠实性审查
                │ pass
                ▼
HH1-C HTML 渲染与确定性校验
                │ sealed ready
                ▼
HH1 composite publisher（非 skill）
                │ ready
                ▼
           外部作者决定
                │ approved / revise / rejected
                ▼
HF1 决定消费、最终封闭与结果投影
                │ stage-result
                ▼
Harness ─ approved→ lld_ready
        ├ revise  → 定向 return
        └ rejected→ 终止态
```

HA1–HK1 不允许并行。虽然部分工作表面可并行，但每一步都改变下一步所依赖的叙事单元、位置和状态边界；并行会造成两个技能各自建立不兼容的结构假设。HQ1 的产品语义 verdict 读取 baseline control、catalog 2.13 明确授权且经 locator/hash 重验的原始权威对象、canonical、manifest、completion 和 deterministic validation；它不得读取 producer generation evidence、execution 或 self-review。这样既能独立核对构思继承，又不会被生产者理由污染。HQ2 先在 handoff-only 上下文完成并密封消费测试，再以新的隔离上下文对照 HP1 正式机器包；两次 task 均不读取独立工作区、generation evidence、HQ1 finding 或聊天。

## 4. 全局权威与决定分类

### 4.1 唯一内容入口

HLD 的唯一权威内容入口是 ready `development-baseline.json`。但为了证明它当前仍有效，生产调用还必须提供：

- `preparation-request.json`；
- ready baseline 四文件目录；
- preparation skill 的正式 schema、validator 和版本锁；
- baseline 引用的不可变 conception source root；
- HLD 输出根目录。

领域技能不得绕过 HB0 直接读取“最新构思”、聊天、HTML、旧 HLD、旧开发地图或手工摘要。

### 4.2 输入权威类别保持不变

Baseline 中的下列分类必须原样继承：

| 分类 | HLD 行为 |
| --- | --- |
| `mandatory` | 必须应用或明确保留，不得改值、缩窄、扩大或省略 |
| `freedom` | 只能在该项授权边界内作 HLD 决定 |
| `must_ask` | 若当前决定依赖答案，阻塞该决定并进入作者门；不得代答 |
| `open` | 主分类保持开放；只有不依赖裁决的结构才能继续 |

`open_item=true|false` 是与上述主分类正交的未决状态标志，可以与 `must_ask` 等主分类重叠；它不得被升级为新的竞争性权威类别，也不得由 HLD 静默清除。上游 `authority_class=author_locked|autonomous_owned|downstream_freedom|author_open` 只说明相对构思阶段的权威来源，不直接决定 HLD 的 `ownership_class`。特别是 `downstream_freedom` 进入 development baseline 后通常对应 HLD 的 `classification=freedom`，不能自动解释成留给 LLD。

### 4.3 HLD 新增决定

HLD 新增内容只能属于：

- `hld_owned`：当前 HLD 技能在明确 freedom 内拥有的结构决定；
- `lld_freedom`：HLD 有意留给 LLD 的实现空间；
- `preserved_open`：原作者开放项在 HLD 中的无损保留。

每项 `hld_owned` 决定必须记录：

- 稳定 ID；
- 唯一 owner stage；
- 所解决的结构缺口；
- 依据的 baseline control、canonical object 和上游 HLD 决定 ID；
- 至少两个真实候选或唯一可行证据；
- 选择与排除理由；
- 影响的叙事单元、故事线、事件、人物、环境和信息链；
- 代价、可逆性和下游自由；
- 实际投影到的 canonical 对象。

只写“建议”而没有选择，或作出选择却没有投影到 canonical 模型，均不得 ready。

Canonical 元素不得复用上游 `authority_class` 来表示 HLD 归属。它必须同时保存：

- `source_authority_refs[]`：原样指向 baseline classification、authority class 和 value hash；
- `ownership_class=source_projection|hld_owned|preserved_open|lld_freedom`：表示 HLD 如何处理该元素；
- 已解决 must-ask 的外部 `resolution_ref`，否则为 `null`。

上游权威永不因 HLD 投影而改名或降级。完整映射代数以逐技能 catalog 第 2.14 节为唯一实现契约。

开放问题是否影响 HLD 不能由 HB0 或 Harness 预先猜测。HB0 只建立 unresolved register；HA1–HK1 分别在形成本 stage 候选之前，对投影的 non-quality unresolved source 生成 `HDD-`；quality-domain unresolved source 只由 HQ1 在 review verdict 前评估。`required_now` 必须在 candidate／verdict 产生前阻塞并进入作者问题事务；“整个 HLD 不需要答案”只能由 HP1 在 HQ1 证明全部投影 stage 均完成 assessment 后确定性聚合。精确 disposition、字段和覆盖规则见 catalog 2.12。

### 4.4 不得以 inventory 数量冒充故事对象数量

Baseline 的 `design_inventory` 是来源导航项，不等于语义对象数量。例如 `storylines` inventory 可以包含故事线需求、连接、角色需求和其他嵌套定义。HB0 必须通过 locator 与 hash 读取权威值，再按 schema 中的实际对象类型建立语义索引；不得把 inventory 条目数直接当作故事线数。

## 5. 公共调用与包契约

### 5.1 唯一调用请求

Harness 只接受 `hld-run-request.json`：

```json
{
  "schema_version": "1.0",
  "harness": "novel-hld-autonomous",
  "project_id": "stable-project-id",
  "hld_run_id": "unique-run-id",
  "hld_version": "semver",
  "preparation_request_path": "path/to/preparation-request.json",
  "baseline_package_dir": "path/to/ready-baseline",
  "output_root": "new/disjoint/path",
  "author_gate": "required",
  "replace": false
}
```

硬规则：

- `project_id` 必须与 baseline 相等；
- `hld_run_id` 不得复用其他输入或项目；
- `output_root` 与 conception source、baseline package 完全分离；
- 生产目录默认不可覆盖；崩溃恢复只接受字节完全一致的已发布包；
- `author_gate` V1 固定为 `required`，不得由调用者关闭；
- 不接受独立 Markdown、HTML、P1 目录或口头批准。

### 5.2 每个正式 stage 的输入门

每个 stage 只能读取一份 sealed `input-gate.json`。公共必需字段：

- `schema_version / hld_run_id / stage / mode`；
- HB0 completion 和 manifest 引用；
- 严格有序的 `upstream_completions`；
- 执行前 `hld-run-state` 引用；
- baseline manifest、validation 和 source lineage；
- exact owner skill、版本和实现 hash；
- `return_binding`，forward 时必须为 `null`；
- HA1–HK1 的 non-quality `unresolved_projection[]`、HQ1 的 quality-domain `unresolved_projection[]`，其他 stage 必须为空；
- current `revision_plan_ref / revision_plan_state_ref`，无返工事务时都为 `null`；
- 允许读取的文件白名单。

技能不得自行发现上游、改变顺序、扩大读取范围或接受“等价文档”。

Harness 签发的 `work-order.json` 还必须包含单调 `event_sequence` 和固定 `result_timestamp`；`stage-result.json` 逐值复制它们，skill 不得读取本机时钟生成 `produced_at`。真实接收时间只由 harness 写入下一份 run-state，因此确定性 script 和 publisher 在同一 work order 下可以保持字节一致。

### 5.3 生成式设计阶段 ready 包

HA1–HK1 每个 ready 包固定包含：

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

Markdown 只供阅读；下游只消费 canonical JSON。Completion 只绑定 package manifest，不绑定聊天。

`stage-result.json` 不属于上述内容包。每个 work order 都在内容包目录之外、同一 sealed workspace 内生成一个结果信封；top-level ready 信封引用 completion，HQ2/HH1 内部 task 的 `composite_internal` ready 信封只引用 internal manifest。精确 reviewer、hybrid、internal-task profile 和信封条件字段以 catalog 2.4–2.6 为准。

### 5.4 状态与失败包

阶段 verdict 只有：

- `ready`：硬准入、结构、语义、覆盖、来源和封包全部通过；
- `revise`：上游有效，当前 owner 可以局部修正；
- `blocked`：输入无效、需要上游改变或需要作者裁决。

每个 work order 无论成功与否都必须产生一个被 harness 消费的 `stage-result.json`：

- `ready` 引用 ready manifest、validation 和 completion；
- `revise` 带 `revision_class`：`local_candidate` 引用 candidate/evidence，`external_author_request` 引用密封 author event；两者都引用 revision report 和 result manifest；
- `blocked` 引用 gate data、blocked report 和 result manifest；
- `runtime_error` 只记录运行失败，不得被解释为语义 verdict。

Local-candidate revise 内容包固定为 candidate/evidence/execution、`revision-report.json`、validation 和 `result-manifest.json`；external-author-request revise 内容包以密封 author event 引用替代 candidate/evidence；blocked 内容包固定为 `gate-data.json`、`blocked-report.json`、validation 和 `result-manifest.json`。唯一 `stage-result.json` 是包外结果信封。这些内容包均不得生成 stage completion，但下一份 run-state 必须强绑定 result manifest 与 stage result，形成不可变结果证据。

`external_author_request` 只允许 HF1 无损投影最终 `author-decision.json` 中的 `revise`；中途 `must_ask` 不使用 revise 包，而使用 `blocked/author_required → author-question → author-answer-event → author-resolution` 事务。两个作者事件类型不得互换。

硬准入失败时不得产生 candidate canonical model。`revise` 和 `blocked` 包不得伪装成 ready 包。Harness 是唯一 parent consumer，也是唯一 run-state writer：它根据固定 owner matrix 把结果确定性转换为 forward、local return、upstream return、author question、reality reentry 或 runtime stop；skill、reviewer、publisher 和 finalizer 都不得自行写状态或指定最终 owner。

### 5.5 稳定 ID

| 对象 | 前缀 |
| --- | --- |
| HLD 结构阶段／叙事单元 | `HST-` / `HNU-` |
| 章节壳 | `HCH-` |
| 故事线编排段／连接 | `HTS-` / `HTC-` |
| 人物弧线落点／关系落点 | `HAS-` / `HRS-` |
| POV 与知识状态 | `HPV-` / `HKS-` |
| 悬念链与信息节点 | `HSP-` / `HIN-` |
| 时空、节奏、张力区段 | `HTM-` / `HPC-` / `HTN-` |
| 关键场景功能 | `HKF-` |
| HLD finding | `HFN-` |
| LLD 工作单元 | `LWK-` |
| Stage-scoped decision dependency | `HDD-` |
| 人审报告结论／控制元素 | `HRE-` |
| 人审 visual model | `HVG-` |
| HTML／SVG 渲染容器 | `HUI-` |

### 5.6 Thinking skill 公共决策契约

HA1–HK1 的 generation evidence 必须依次包含：

1. `dependency-assessment`：逐项形成当前 stage 的 `HDD-`；出现 `required_now` 时在此结束并生成 blocked result；
2. `obligation-analysis`：当前 stage 的全部义务、开放项和禁止项；
3. `option-analysis`：真实 freedom 的可区分方案，或唯一方案的排除证据；
4. `projection-analysis`：选择如何进入 canonical 对象；
5. `adversarial-self-review`：主动挑战因果、覆盖、权限、信息、边界和下游消费。

两个候选必须在至少一个实际 canonical 决策字段上不同，并带来不同代价或下游影响；同义改写不算候选。每个 thinking skill 必须拥有专属 SOP、pass/revise/fail anchors、正例类型、边界反例类型和 agentic eval。结构 validator 不能代替语义判断。

所有跨模型引用只能使用稳定 ID；标题、人名、章节名和路径不能代替对象引用。

### 5.7 Reviewer verdict 与复合 stage

Reviewer 内部使用 `pass / revise / fail`，stage result 使用 `ready / revise / blocked / runtime_error`。固定映射为：pass→ready；reviewer 自身证据错误的 revise→local revise；上游内容、作者问题或现实依赖导致的 fail→带相应 defect origin 的 blocked；运行失败→runtime error。Skill 只提交证据与 affected IDs，router 决定最终 owner。任何其他组合 fail closed。

HQ2 和 HH1 是复合 stage。内部 skill 不生成 top-level completion；harness core 的确定性 `composite-stage-publisher` 只在内部包全部密封、通过且 hash/binding 一致时复制既有字节并生成 validation、manifest、completion 和 stage result。Publisher 不计入14个技能，不拥有内容判断，也不得写 run-state。精确 profile 见 catalog 第 2.16 节。

内部 task non-ready 时，后续 internal task 不得启动；publisher 使用独立 non-ready profile，把第一个 non-ready internal 内容包和结果信封逐字节复制进 publisher 包，再绑定此前 pass 包和“后续未签发”状态，生成 top-level non-ready stage result。Router 只能消费 publisher 的顶层结果，不能直接消费 internal result。这样 consumer fail 时不需要伪造 fidelity task，HH1-A/B fail 时也不需要伪造后续 B/C 包或跨 workspace 引用。

## 6. 精确输入拓扑

| 目标 stage | `upstream_completions` 精确顺序 | 唯一内容增量 owner |
| --- | --- | --- |
| HB0 | `[]` | 基线准入与控制面，不创作 |
| HA1 | `[HB0]` | 总体结构与章节壳 |
| HS1 | `[HB0,HA1]` | 故事线编排 |
| HC1 | `[HB0,HA1,HS1]` | 人物弧线落位 |
| HI1 | `[HB0,HA1,HS1,HC1]` | POV、知识与悬念 |
| HR1 | `[HB0,HA1,HS1,HC1,HI1]` | 时空、节奏、张力与连续性 |
| HK1 | `[HB0,HA1,HS1,HC1,HI1,HR1]` | 关键场景功能综合 |
| HQ1 | `[HB0,HA1,HS1,HC1,HI1,HR1,HK1]` | 只审查 |
| HP1 | `[HB0,HA1,HS1,HC1,HI1,HR1,HK1,HQ1]` | 只组装 |
| HQ2 | `[HB0,HP1]` | 只验收正式 handoff |
| HH1 | `[HB0,HP1,HQ2]` | 只呈现；内容输入仍只有 HP1 |
| HF1 | `[HB0,HA1,HS1,HC1,HI1,HR1,HK1,HQ1,HP1,HQ2,HH1]` | 只封闭 |

HH1 只以 HP1 为内容输入，并以 HQ2 pass 作为准入证据；禁止重新读取 HA1–HK1 后另作解释。这条规则保证人审报告与机器 HLD 使用同一结论层。

## 7. 逐技能设计

### 7.1 `novel-hld-baseline-admitter`（HB0，script）

**目标**：证明正式开发基线当前有效，并建立 HLD 的不可变控制面。

**职责**：

- 重新运行 preparation validator；
- 验证四文件 ready 包、source root、release identity、hash 和 HLD assignment；
- 解析 root-aware locator，建立对象类型正确的只读语义索引；
- 冻结 authority partition、unresolved register、source whitelist 和 HLD run revision 0；
- 生成后续阶段的公共控制规则。

**边界**：不摘要、推断、补写或选择任何 HLD 答案。

**输入**：唯一 `hld-run-request.json` 及其精确引用。

**交付**：

- `hld-control-baseline.json`；
- `hld-source-index.json`；
- `validation.json / package-manifest.json / stage-completion.json`。

`revision-000` 在 HB0 work order 之前由 harness 创建；HB0 只引用它。Harness 接纳 HB0 completion 后才创建 `revision-001`。

**ready 硬门**：baseline 独立重验为 ready；baseline 声明的全部控制绑定逐 ID 无损闭合；六域 inventory 的每个 locator 与 hash 可解析；HLD assignment 与固定责任表完全相等；不得出现 HLD 决定。

### 7.2 `novel-hld-narrative-architect`（HA1，thinking）

**目标**：建立一部小说的总体叙事骨架和章节级容器，使后续编排有唯一坐标系。

**职责**：

- 选择适合该故事的结构形态，不预设固定三幕；
- 定义结构阶段、叙事单元层级、章节壳和顺序；
- 为每个单元定义进入状态、核心任务、必须变化、退出状态和承接条件；
- 将构思中的重大事件、汇合点、高潮、结局边界落到结构锚点；
- 定义篇幅区间、章节密度和结构弹性，而非提前定死正文长度。

**不负责**：不重新设计故事线内容，不安排具体 POV，不写关键场景细节，不创建新事件或人物。

**canonical 交付**：`narrative-architecture.json`，至少包含：

- `architecture_choice`；
- `structural_phases[]`；
- `narrative_units[]`；
- `chapter_shells[]`；
- `turning_point_anchors[]`；
- `entry_exit_state_contracts[]`；
- `downstream_obligations`；
- `design_decisions / derivation_claims / open_items`。

**ready 硬门**：所有章节壳只属于一个父结构且顺序无环；每一阶段有可验证变化；重大事件和结局控制均有合法锚点；没有构思改写或 LLD 细节。

### 7.3 `novel-hld-storyline-choreographer`（HS1，thinking）

**目标**：把构思中的多维故事线编排为共同还原故事主体的完整叙事网络。

**职责**：

- 按权威对象识别主干、支线、背景线、人物线、情感线、主题线和可选旋律线；
- 将每条实际故事线分段映射到 HA1 叙事单元；
- 定义进入、并行、交叉、接力、汇合、退出、回收和未展开策略；
- 定义线间因果依赖、信息依赖、情绪反差和主题互证；
- 映射构思事件在线中的作用和高层位置；
- 证明各线逻辑一致且共同支撑主体，而非互相重复或各讲各的。

**不负责**：不新增故事事实，不决定人物内在弧线细节，不决定 POV，不把可选旋律线强制扩写成主要篇幅。

**canonical 交付**：`storyline-choreography.json`，至少包含：

- `semantic_storyline_register[]`；
- `storyline_segments[]`；
- `unit_storyline_matrix[]`；
- `storyline_connections[]`；
- `convergence_and_split_points[]`；
- `event_storyline_placement[]`；
- `activation_disposition[]`；
- `subject_reconstruction_test`。

**ready 硬门**：每条权威故事线必须处于 `placed / background-carried / optional-not-activated / preserved-open` 之一且有授权依据；所有连接引用有效；主干从起点到终点连续；所有强制线有建立、发展、转折和回收或明确开放。

### 7.4 `novel-hld-character-arc-placer`（HC1，thinking）

**目标**：把构思中已经定义的人物、关系和弧线，转换为与故事线、事件和叙事单元一致的变化路径。

**职责**：

- 为核心和重要人物定义弧线落点；
- 映射目标、认知、价值、关系、责任和选择在各阶段的状态变化；
- 把改变与既有事件、线间连接、代价和后果绑定；
- 定义人物在各故事线中的参与职责和缺席理由；
- 检查能力、权限、信息和行动是否匹配；
- 为关系弧线定义双方可观察的变化落点。

**不负责**：不补写外貌、生活背景、社交圈或新人物；不改变构思中的动机和关系事实；不写逐场景行为。

**canonical 交付**：`character-arc-placement.json`，至少包含：

- `character_participation_register[]`；
- `arc_state_models[]`；
- `arc_steps[]`；
- `relationship_steps[]`；
- `choice_cost_consequence_links[]`；
- `event_character_alignment[]`；
- `capability_information_permission_checks[]`。

**ready 硬门**：所有核心人物均有完整起点—压力—选择—代价—结果路径；弧线变化由已存在的事件和关系触发；没有作者不存在的感情、能力或信息被补入；关键结果有承担者。

### 7.5 `novel-hld-information-architect`（HI1，thinking）

**目标**：控制小说在何时通过谁让角色与读者知道什么，使悬念、误判和揭示成为可执行结构。

**职责**：

- 定义 POV 体系、人称、权限和切换层级；
- 定义各结构单元的 POV 候选／唯一归属和禁止归属；
- 维护角色知识状态与读者知识状态；
- 设计 setup—probe—reveal—payoff 链；
- 定义隐瞒、暗示、误判、回看验证和悬念保持规则；
- 应用构思叙述契约，例如只展示可见的过程性心理，不提前公开决定性答案；
- 保留作者开放的终局问题，不通过叙事安排偷偷裁决。

**不负责**：不写线索材料、回忆文本、对白或具体信息呈现句；不决定场景内动作。

**canonical 交付**：`narrative-information-architecture.json`，至少包含：

- `pov_policy`；
- `unit_pov_assignments[]`；
- `knowledge_states[]`；
- `reader_information_states[]`；
- `suspense_chains[]`；
- `information_nodes[]`；
- `reveal_payoff_matrix[]`；
- `concealment_and_inference_rules[]`。

**ready 硬门**：每个 reveal 有合法 setup，每个必须回收的 setup 有 payoff；任何知识变化都有来源；POV 不泄露无权感知的信息；开放结局和身份疑问没有被无意裁决。

### 7.6 `novel-hld-rhythm-continuity-architect`（HR1，thinking）

**目标**：把前述结构变成时空连续、节奏有起伏、张力可累积且可阅读的推进方案。

**职责**：

- 区分故事时间、叙事顺序和角色感知时间；
- 映射顺叙、回忆、插叙、并行和时间跳跃；
- 定义各叙事单元的时间跨度、压缩／展开和同步关系；
- 验证环境进入条件、资源、权限、距离和迁移时间；
- 定义节奏、张力、情绪压力、恢复窗口和高潮前后落差；
- 协调多线切换频率、章节负载和信息密度；
- 证明状态、人物位置、知识、资源和关系连续。

**不负责**：不增加环境摆设或感官细节，不改写事件因果，不生成逐场景日程或具体过场动作。

**canonical 交付**：`rhythm-continuity-architecture.json`，至少包含：

- `story_time_model`；
- `narrative_order_map[]`；
- `unit_duration_density[]`；
- `space_transition_map[]`；
- `parallel_synchronization[]`；
- `pacing_curve[]`；
- `tension_curve[]`；
- `recovery_windows[]`；
- `continuity_ledger[]`。

**ready 硬门**：没有不可能的迁移或时间倒置；所有回忆和插叙有触发与返回点；张力并非单调上升；高潮前有充分累积；章间切换不会破坏因果、知识或人物状态。

### 7.7 `novel-hld-key-scene-function-planner`（HK1，thinking）

**目标**：综合 HA1–HR1，定义 LLD 必须展开的最小充分关键场景功能集合。

**职责**：

- 为结构转折、故事线连接、人物选择、信息揭示和高潮结果定义关键场景功能；
- 合并可以由同一场景承担且逻辑兼容的功能；
- 拆分职责过载、时空冲突或 POV 冲突的功能；
- 定义前置条件、叙事功能、必须状态变化、退出条件和下游自由；
- 建立 key-function 与章节、事件、人物、环境、故事线、POV、知识状态和张力的完整索引；
- 验证不是靠一句信息、巧合、越权或工具人解决关键矛盾。

**不负责**：不定义场景动作顺序、对白、画面、感官、物件、具体记忆片段或正文。

**canonical 交付**：`key-scene-function-map.json`。每个 `HKF-` 必须包含：

- 所属章节壳和结构位置；
- 前置状态与触发条件；
- 唯一主要功能及允许的次要功能；
- 涉及的权威故事线、事件、人物和环境 ID；
- POV 约束和进入前／退出后的知识状态；
- 必须发生的状态变化、选择、代价或结果；
- 张力目标和节奏角色；
- 完成判据、禁止解法和 `lld_freedom`。

HK1 同时拥有 `lld_work_requirements[]`：每个 `LWR-` 明确关联一个或多个 HKF、分组依据、进入／退出状态、LLD 必须细化项、LLD freedom 和验收条件。合并或拆分属于 HK1 的 HLD 语义决定；HP1 只能把每个 `LWR-<suffix>` 一对一投影为 `LWK-<suffix>`，不得让 HK1 提前生产 `LWK-`。

**ready 硬门**：所有结构转折、强制故事线连接、核心人物关键选择、必须揭示／回收和高潮结果均被覆盖；每个 HKF 有必要性；每个 HKF 被至少一个 LWR 消费且每个 LWR 有分组依据；不得用固定数量凑表；不得出现 LLD 泄漏。

### 7.8 `novel-hld-semantic-reviewer`（HQ1，thinking）

**目标**：独立检查 HLD 是否自洽、真实可发生、逻辑正确、完整、忠于构思并具备开发可用性。

**职责**：重新验证 HA1–HK1；检查权威继承、结构、故事线、人物弧线、因果、信息、时空、节奏、主题支撑、关键功能、开发可用性和边界；为每条 finding 记录 defect origin、受影响稳定 ID 和纠正后必须满足的条件。最终 owner 与最小重跑范围只能由 harness router 按 ID—producer 矩阵计算。

**边界**：只审查，不修稿，不给出替代故事答案，不按个人审美或固定模板制造问题。

**交付**：`hld-semantic-review.json`，每个 pass 维度必须包含一次反证挑战和故事对象证据；finding 必须包含对象 ID、违反契约、严重度、defect origin 和纠正条件，不得写最终 owner、return target 或失效后缀。HQ1 pass 允许 HP1 组装，但不等于最终 handoff 已被消费者验收。

### 7.9 `novel-hld-package-assembler`（HP1，script）

**目标**：把通过 HQ1 的 canonical 模型无损组装为正式机器 HLD 和 LLD handoff。

**职责**：只重验、索引、封装、渲染确定性 Markdown、把 HK1 `lld_work_requirements[]` 一对一投影为 handoff LWK、把 HQ1 已通过的各 stage HDD 确定性聚合为 `unresolved_dependency_summary[]`，并计算 hash；不产生新 HLD 决定或开放问题答案。

**交付**：

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

`lld-handoff.json` 必须把 HK1 每个 `LWR-<suffix>` 逐值投影为 `LWK-<suffix>`，并保存 `source_lwr_id`；其 HKF、章节壳、进入／退出状态、角色、环境、故事线、事件、POV、知识边界、禁止项、LLD 必须细化项、LLD 自由和验收条件不得漂移。顶层还必须复制 `unresolved_dependency_summary[]`、preserved open items 与 resolution refs，并显式交付：HA1 的完整世界／城市／季节／威胁机理、HR1 的跨城转场、HB0 全部角色的去向、HB0 全部环境的覆盖位置，以及终局的全部状态变化。HP1 不得重新分组、补写、删减 LWR/LWK 或解释未决项。

**ready 硬门**：可无损反解析 HA1–HK1；`set(LWK.source_lwr_id)` 与 HK1 的 LWR 集合精确相等且同后缀映射唯一；每个 baseline 角色都有章节／LWK 去向或有明确且合法的缺席理由，每个 baseline 环境至少被一个 LWK 使用；三座及以上城市必须有跨城路线和 HR1 转场，四座及以上城市至少有四条路线且城市图连通；终局同时保留所有 required state changes，不能只留一个总结句；所有索引只引用当前 ID；Markdown 与 canonical package 一致；handoff 的硬约束／开放项／自由三者互斥；相同输入重复运行得到字节一致的确定性产物。

### 7.10 `novel-hld-lld-readiness-evaluator`（HQ2，thinking）

**目标**：先证明未来 LLD 只凭 `lld-handoff.json` 就能启动，再证明该 handoff 忠实覆盖 HP1 机器 HLD。

**隔离执行**：同一 skill 由 harness 用两个不同 task/context 调用，不增加技能数量。

1. `consumer_test` 只读 `lld-handoff.json`、schema 和非内容 identity/hash 元数据。它独立重建 LLD 工作顺序、边界、全部 LWK、强制故事线、核心人物变化、关键结果、约束和自由，输出并密封 `handoff-consumption-test.json`。严禁读取 package、canonical、spec、cross-index 或 traceability。
2. 只有 consumer pass 后，harness 才以新上下文签发 `fidelity_test`。它读取密封的 consumer 结果和 HP1 正式包，检查 LWR↔LWK 双射、义务覆盖、分类忠实以及遗漏／增强／弱化；不得改写或补做 consumer reconstruction。
3. 两项均 pass 后，composite publisher 确定性生成 `lld-handoff-acceptance.json` 和 HQ2 completion。

**测试问题**：

- 能否仅凭正式 handoff 重建 LLD 工作顺序和边界；
- 每个 LWK 能否追溯到 HKF、章节、故事线、事件、人物、环境、POV 和状态；
- 能否区分 HLD 硬约束、作者开放项和 LLD 自由；
- required elaboration 和 acceptance criteria 是否足以开始 LLD；
- 是否存在必须猜测或新增的高层结构、主要事实或关键功能；
- HP1 是否遗漏、弱化、增强或错分了 HLD package 中的必要义务。

**内部交付**：`handoff-consumption-test.json` 与 `handoff-fidelity-test.json`；顶层 `lld-handoff-acceptance.json` 只能由 publisher 聚合，包含两个密封结果的引用、全量追踪、约束分类、覆盖／双射检查、`missing_guesswork[]`、findings 和最终 verdict。

**ready 硬门**：两个 task 与 producer/HQ1 及彼此身份隔离；consumer 实际读取集不含任何 package 内容；其结果先密封；全部 LWK 和强制对象通过 handoff-only 消费测试；fidelity 无漂移；无 missing guesswork、blocker 或 actionable finding。HQ2 completion 是 HH1 和 HF1 的必需准入证据。

### 7.11 `novel-hld-review-report-assembler`（HH1-A，hybrid，thinking-dominant）

**目标**：把 HP1 的结论层转成作者可快速理解的 HLD 评审内容。

**固定内容**：总体结构、故事线编排、人物弧线落位、POV 与信息悬念、时空节奏张力、关键场景功能、开放项与 LLD 边界。只呈现结论、关系和控制信息，不呈现 Agent 推理过程。

**边界**：唯一内容输入为 HP1；不重读原始构思，不新增解释性事实，不改写关键功能。

**交付**：`hld-human-review-report.json`，每个可见结论／控制元素使用 `HRE-`，每个 visual model 使用 `HVG-`，并绑定 HP1 source ID 和 locator；按 catalog 固定公式声明不超过十分钟的 `review_budget`。不得使用 `element_id` 同义字段，也不得靠删除 material control 满足预算。

### 7.12 `novel-hld-presentation-fidelity-reviewer`（HH1-B，thinking）

**目标**：独立证明人审内容既忠于机器 HLD，又能在十分钟决策层内支持作者理解和判断。

**交付**：`presentation-fidelity-review.json`，至少逐项检查事实一致、结构覆盖、开放项保持、自由边界、图表数据、阅读预算、固定决策检索问题和认知过载。任何 material drift、关键控制不可定位、预算超限或过程噪音掩埋结论都阻塞 HTML；纯表达风格差异不得形成 finding。

### 7.13 `novel-hld-html-renderer`（HH1-C，script）

**目标**：把已通过忠实性审查的报告 JSON 确定性渲染成可离线阅读的 HTML。

**硬要求**：

- 固定标题、目录和状态说明；
- SVG 展示结构、故事线汇合、人物弧线、信息链和节奏曲线；
- 所有图形数据只来自 report JSON；
- 每个确定性 HTML/SVG 容器使用 `HUI-`，并通过 `data-report-element-id` 回指 `HRE-/HVG-`；
- 生成 `render-target-registry.json`，使 Router 无需解析自然语言即可把作者的 `HUI-` target 唯一映射到当前 DOM 容器和报告来源；
- 无外部 CDN、无网络依赖、无脚本注入；
- 键盘可访问、打印可读、常用视口无横向溢出；
- renderer 不得生成或摘要故事内容。

**交付**：内部 HTML 包、render execution、validation 和 manifest。HH1-C 不生成 top-level completion；只有 catalog 第 2.16 节的 HH1 composite publisher 可以在 A/B/C 全部通过后复制密封字节并生成 HH1 validation、manifest、completion 和 stage result。

### 7.14 `novel-hld-finalizer`（HF1，script）

**目标**：只在当前 HP1、HQ2、HH1 和外部作者决定完全闭合后，授予 LLD 准入。

**输入**：当前 run-state、完整 completion 链、HP1、HQ2 handoff acceptance、HH1、`author-decision.json`。

Revise 决定中的每个 target 必须由 HF1 通过 HP1 cross-index 或 HH1 `render-target-registry.json` 确定性验证；HF1 只验证引用和 target kind，不解释 requested change 的故事意义。

**交付**：

- `hld-completion.json`；
- `final-validation.json`；
- 对当前 `lld-handoff.json` 的强绑定；
- 包外唯一 `stage-result.json`：approved 为 ready；revise 为标准 revise 包；rejected 为 `author_rejected` blocked 包。

HF1 不写 run-state、return 或终止状态。Harness 验收 HF1 stage result 后，才生成唯一的最终 run-state revision；approved 转为 `lld_ready`，revise 定向返工，rejected 进入终止态。

**硬门**：决定只能是 `approved / revise / rejected`；只有 `approved`、HQ2 当前 pass、无 active return 且无 pending/superseded revision target group 才生成 completion；任一上游包、handoff acceptance、报告、HTML 或作者决定变化都会使旧 completion 和 LLD 准入失效。

### 7.15 生产者—消费者契约闭合矩阵

| 唯一生产者 | Catalog artifact role／实际字段 | 声明消费者 | 消费用途 | 禁止的替代来源 |
| --- | --- | --- | --- | --- |
| HB0 | `control_baseline / source_index`；`authority_partition / control_registry / unresolved_register / hld_assignment` | HA1–HQ1、HP1 | 权威、对象、边界和追溯 | 原始聊天、HTML、旧 HLD |
| HA1 | `structural_phases / narrative_units / chapter_shells / turning_point_anchors / entry_exit_state_contracts` | HS1、HC1、HI1、HR1、HK1、HQ1、HP1 | 全链唯一叙事坐标系 | 下游自建章节或幕结构 |
| HS1 | `semantic_storyline_register / storyline_segments / unit_storyline_matrix / storyline_connections / event_storyline_placement` | HC1、HI1、HR1、HK1、HQ1、HP1 | 线的参与、连接、事件位置和切换义务 | 从构思文本重新猜故事线编排 |
| HC1 | `arc_state_models / arc_steps / relationship_steps / choice_cost_consequence_links / event_character_alignment` | HI1、HR1、HK1、HQ1、HP1 | POV 候选、知识持有人、状态连续和关键选择 | 下游重写人物动机或关系 |
| HI1 | `pov_policy / unit_pov_assignments / knowledge_states / suspense_chains / reveal_payoff_matrix` | HR1、HK1、HQ1、HP1 | 叙事顺序、切换密度、揭示条件和信息边界 | 下游临时决定谁知道什么 |
| HR1 | `narrative_order_map / unit_duration_density / space_transition_map / pacing_curve / tension_curve / continuity_ledger` | HK1、HQ1、HP1 | 关键功能的合法时空位置、张力和连续状态 | HK1 自行修改时间或空间规则 |
| HK1 | `key_scene_functions / coverage_matrix / lld_work_requirements / lld_freedoms` | HQ1、HP1 | 审查对象与确定性 LWK 来源 | HP1 或 LLD 自行分组／补关键功能 |
| HQ1 | `semantic_review`；`findings / pass_claims / coverage_summary / decision_dependency_review / verdict` | HP1 | 是否允许组装及 HDD 是否完整 | producer 自评或手工批准 |
| HP1 | `novel_hld_package / hld_spec / cross_index / traceability / unresolved_dependency_summary / lld_handoff` | HQ2、HH1、HF1 | 唯一正式机器内容、开放问题聚合与 handoff | HA1–HK1 工作区、旧 Markdown |
| HQ2 consumer/fidelity | `handoff_consumption_test / handoff_fidelity_test` | HQ2 publisher | handoff-only 可用性与机器包忠实性 | 用 package 补 consumer 答案 |
| HQ2 composite publisher | `lld_handoff_acceptance / verdict` | HH1、HF1 | 确定性聚合两项密封验收 | 任一 reviewer 自行发布 completion |
| HH1-A | `human_review_report` | HH1-B、HH1-C、HH1 publisher | 忠实性审查、可视化渲染与密封发布 | renderer 直接摘要 HP1 |
| HH1-B | `presentation_fidelity_review`；`reading_budget_validation / decision_retrieval_tests / cognitive_overload_findings / verdict` | HH1-C、HH1 publisher | 证明报告忠实且可在十分钟决策 | assembler 自证忠实／可读 |
| HH1-C | `human_review_html / render_target_registry` | HH1 publisher | 生成内部确定性界面并提供 HUI 路由索引 | 临时网页、未封包 HTML 或自然语言 DOM 定位 |
| HH1 composite publisher | `HH1 completion / sealed human package` | 作者门、HF1 | 作者唯一可见评审包 | 未定义 publisher 或 HH1-C 越权 completion |
| 外部作者门 | `author_decision` | HF1 | 批准、返工或拒绝 | Agent 代签、聊天推断 |
| HF1 | `hld_completion / final_validation` | harness、LLD admission | 产生唯一最终封闭证据；harness 再写 `lld_ready` | router 绕过 HF1 或旧 completion |

闭合规则：

1. 表中每个字段只能由“唯一生产者”新增或改变；
2. 间接消费者必须通过 completion 链读取同一字段，不能复制后另行解释；
3. 任一消费者需要但矩阵中没有生产者的字段，属于契约设计缺口，不能靠提示词临时补足；
4. 任一生产字段没有消费者和验收用途，默认删除，除非是明确的审计证据；
5. `source_id + locator + canonical value hash` 是跨阶段语义绑定，文件名或自然语言相似不构成绑定。
6. Non-quality `HDD-` disposition 只能由被投影 source 的当前 HA1–HK1 产生；quality-domain HDD 只能由 HQ1 产生。HQ1 审查全链覆盖，HP1 聚合；HB0 与 Harness 只投影和路由。
7. `revision-plan.json` 是 Router 唯一拥有的控制面 artifact，不是第15个技能的交付，也不得进入机器故事内容权威包。

### 7.16 上游 HLD assignment 覆盖矩阵

| Baseline 要求 | 字段域 owner | 共同证明者 |
| --- | --- | --- |
| `overall-narrative-architecture` | HA1 | HQ1 |
| `multi-thread-choreography` | HS1 | HA1、HQ1 |
| `character-arc-placement` | HC1 | HS1、HK1、HQ1 |
| `act-and-chapter-progression` | HA1 | HR1、HK1 |
| `key-scene-functions` | HK1 | HA1–HR1、HQ1 |
| `suspense-setup-probe-reveal-payoff` | HI1 | HK1、HQ1 |
| `time-space-pacing-tension-pov-information-architecture` | HI1（POV／信息）与 HR1（时空／节奏／张力） | HK1、HQ1 |
| `hld-to-lld-handoff-and-acceptance` | HP1（handoff）／HQ2（acceptance） | HF1 |
| `traceable-conception-inheritance` | HB0 | 全阶段、HP1 |
| `complete-multi-thread-architecture` | HS1 | HQ1、HQ2 |
| `character-arc-and-event-alignment` | HC1 | HK1、HQ1 |
| `key-scene-function-coverage` | HK1 | HQ1 |
| `lld-ready-handoff-with-acceptance` | HP1 / HQ2 | HF1 |

Baseline 的四项 prohibition 由所有 stage 共同执行：改变构思权威、裁决作者问题、生产 LLD 材料或写正文，任一发生即为 blocker。

同一 baseline 要求可以横跨多个互斥字段域，例如 POV／信息属于 HI1、时空／节奏／张力属于 HR1；这不是共同拥有同一字段。每个实际 canonical 字段仍必须只有一个 producer，具体字段名与 producer 以 catalog 2.10、17、18 节为准。

## 8. 运行状态与作者门

### 8.1 状态机

```text
initialized
→ baseline_ready
→ architecture_ready
→ storylines_ready
→ character_arcs_ready
→ information_ready
→ rhythm_ready
→ key_functions_ready
→ reviewed
→ packaged
→ handoff_accepted
→ presented
→ waiting_author
→ author_decision_received
→ finalizing
→ lld_ready | revising | rejected

任一设计／审查 stage ─required_now→ waiting_author_answer
waiting_author_answer ─hld_local_resolution→ 原 stage 的新 revision
waiting_author_answer ─revision_target_resolution→ revision_plan_active
waiting_author_answer ─conception_authority_change→ exited_for_conception_reentry

任一 stage ─structural reality dependency→ exited_for_conception_reentry

任一 finding/author revise ─router→ revision_plan_active
revision_plan_active ─group resolved→ next_group_active | forward_rerun
revision_plan_active ─target superseded→ waiting_author_answer
revision_plan_active ─all groups resolved→ 从 earliest invalidated stage 重跑其后续硬门
```

每次转换生成不可覆盖的 `hld-run-state/revision-NNN.json`，绑定前态路径和 hash。Completion 绑定执行前状态；协调器接纳后生成后态，避免自引用。

### 8.2 作者开放问题处理

HB0 对每个 `must_ask` 或 `open_item=true` 只生成 unresolved register，不生成语义处置。被投影 non-quality source 的 HA1–HK1 必须在候选前分别生成 stage-scoped `HDD-`；quality-domain source 由 HQ1 在 review verdict 前生成 HDD：

- `not_needed_for_current_stage`：当前 stage 不依赖答案，原样保留；
- `conditional_structure_preserves_open`：允许建立不选分支的条件结构；
- `required_now`：不产生 candidate，生成作者问题并阻塞当前 stage；
- `resolved_by_external_author_event`：只接受密封 author resolution，不接受 Agent 代答。

同一 non-quality source 可以被多个设计 stage 分别评估；任何单一 stage 都不得把自己的“不需要”扩大成“整个 HLD 不需要”。HQ1 负责生成仅限 quality-domain 的 HDD，并检查全链 assessment 覆盖和开放项保持；HP1 只在 HQ1 pass 后确定性聚合 HLD 层状态。

`required_now` 必须进入 `question_kind=source_resolution` 的独立 author-question transaction：router 生成绑定 source control、HDD、受影响 obligation、owner、允许回答范围和 resume stage 的 `author-question.json`，状态进入 `waiting_author_answer`；外部作者用 `author-answer-event.json` 绑定问题 hash 和原文；harness 再生成 `author-resolution.json`。Revision plan 的 target 因上游变化失效时，使用独立的 `question_kind=revision_retarget` 条件字段，只允许作者重新定位 target，不得借此改变 source authority。

- `hld_local_resolution` 只解释现有 must-ask，不改变 mandatory/open 构思事实；同 stage 以 return-resolution 重跑；
- `revision_target_resolution` 只把 superseded group 重新绑定到作者选择的当前合法 target，并生成新 revision-plan-state；不改变请求意义或故事事实；
- `conception_authority_change` 关闭当前 HLD 准入，返回构思 owner，重新批准和 preparation 后启动新 HLD run。

中途 author answer 与最终 `author-decision.json` 是两个不同事务，不得混用、推断或重复消费。

若 HLD 暴露构思未登记的结构性现实事实依赖，发现 skill 只在 `stage-result.json` 中提交 `blocked/reality_dependency`、claim、证据和 affected IDs，不得自行生成 request、研究或写入事实。Harness router 验证 defect origin 后唯一生成 `reality-dependency-request.json`，返回构思事实研究 owner；重新批准和 preparation 后启动新 HLD run。纯 HLD 的时间、权限、资源和迁移矛盾仍返回相应 HLD owner。

### 8.3 作者最终决定

作者决定同时绑定 HP1 completion、HQ2 handoff acceptance、HH1 completion 和 HTML hash。三个决定都由 harness 签发 HF1 work order 消费，不能由 router 绕过 HF1 直接解释：

- `approved`：HF1 重验完整链并产生 ready result 和 HLD completion；
- `revise`：新决定使用 schema `1.1`。每个 target 必须声明 `target_kind + target_id + requested_change + author_text_locator + change_scope + target_field_paths`；语义修改另需 `semantic_target_ids[]`，由 HP1 cross-index 解析到唯一 canonical owner。`report_content` 只允许改表达，不得承载城市、角色、环境、事件、关系、因果或终态事实；`render_expression` 引用 `HUI-`；改变构思权威使用 `conception_authority`。HF1 无损投影为 external-author-request revise result，router 再按 catalog 2.17 生成 revision plan，并把密封作者决定作为最早 canonical owner 的补充输入；
- `rejected`：HF1 投影为 `author_rejected` blocked result，router 再关闭当前 run，不产生 LLD 准入。

### 8.4 修订轮次与耗尽规则

- 每个 work order 只允许一次语义执行和一次正式提交；失败后必须生成新的 return 和 revision，禁止在原包内反复覆盖；
- 同一 owner、同一 root-cause fingerprint 最多允许 2 次自动 local revision；fingerprint 必须由 router 按 catalog 2.17 的规范 JSON 算法生成，skill 不得自行书写；
- 第 3 次仍出现同一根因时，harness 进入 `blocked`，交付完整证据并要求人工检查技能实现、输入契约或上游事实；
- 作者主动发起的不同 revision target 不计入自动耗尽；
- 崩溃恢复、字节完全一致的 orphan admission 和 validator 重验不计为语义修订轮；
- 耗尽不得被解释为降低验收标准或跳过 stage 的许可。

## 9. 唯一 owner 与定向退回

| 问题 | 唯一 owner |
| --- | --- |
| baseline、source、authority、locator 或准入错误 | HB0／preparation owner |
| 总体结构、章节壳、阶段变化或转折锚点错误 | HA1 |
| 故事线遗漏、重复、连接、汇合、退出或回收错误 | HS1 |
| 人物弧线、关系变化、选择、代价、能力／信息／权限错配 | HC1 |
| POV、角色知识、读者知识、悬念、探针、揭示或回收错误 | HI1 |
| 时间、空间迁移、顺序、节奏、张力或连续性错误 | HR1 |
| 关键场景功能缺失、过载、重复、越界或覆盖错误 | HK1 |
| HLD 语义漏审、错判、defect origin 或 affected IDs 错误 | HQ1 |
| 组装、索引、Markdown、handoff 或 manifest 漂移 | HP1 |
| 正式 handoff 消费测试、missing guesswork 或 HQ2 finding 错误 | HQ2；若根因来自 handoff 则返 HP1，来自 HLD 内容则按 source ID 返原 owner |
| 人审报告选择、组织或源绑定错误 | HH1-A |
| 忠实性误判 | HH1-B |
| HTML、SVG、可访问性或确定性错误 | HH1-C |
| 最终 binding、决定消费或 completion 封闭错误 | HF1 |
| stage-result 消费、owner 计算、状态转换或 return 错误 | harness/router |
| 作者锁定的构思事实本身需要改变 | 对应构思／访谈 owner；重新完成批准和 preparation |

每个 work order 的 `stage-result.json` 是 router 唯一结果输入。Router 根据固定 owner matrix 将其转换为 forward、local return、upstream return、author question、reality reentry 或 runtime stop；skill 提供问题事实和受影响 ID，但不得指定最终 owner。

Finding 集合或作者 local-HLD targets 不能直接变成一个临时 return。Router 必须先生成不可变 `revision-plan.json`：每个 finding/author target 独立成组，由 ID 唯一求 owner，再按固定拓扑和原 source order 排序；即使 owner 相同也不做语义合并。含 `conception_authority` 的作者事件直接退出当前 HLD，不建立本地 plan。Plan 始终绑定触发它的 stage result，作者返工时再强绑定该 result 引用的 author event。Plan 固定保存 target groups、失效后缀、作者重新批准要求和规范 root-cause fingerprints。Active/pending/resolved/superseded 状态只写入不可覆盖的 `revision-plan-state/revision-NNN.json`，HLD run-state 同时绑定 plan 和 current plan-state；精确 schema 和算法以 catalog 2.17 为准。

每个 target group 固定包含：问题、故事专属证据、受影响 ID、违反契约、确定性 owner、`target_stage`、`resume_stage`、所需修订、完成条件和失效后缀。同一 run 同时仍只允许一个 active return，但可以有多个持久化 pending groups。只有 active group 的 `resume_stage` 可带该组 `return_binding` 进入；当前组完成后 router 激活下一组，从最早 owner 起按正常拓扑重跑。下游要求不得交给上游 skill，也不得因旧作者决定失效而丢失。

若上游修改使后续 target ID 不再存在或意义改变，该组必须标记 `superseded` 并请求外部重新定位，不能静默视为完成。全部 groups resolved 后，从拓扑最早 group 对应的 `invalidated_suffix` 起重跑：仅 HTML 表达返工时 HP1/HQ2 保持 current，故事线返工则 HS1 及其后 HQ1/HP1/HQ2/HH1 全部失效。无论 suffix 起点在哪里，当前 HH1 binding、作者门和 HF1 都必须重新通过；旧 completion 保留取证但不再 current。

## 10. 最终交付物

### 10.1 机器内容权威包

- `novel-hld-package.json`：唯一机器内容权威；
- `canonical-models/`：HA1–HK1 的当前模型快照；
- `novel-hld-spec.md`：面向 AI 开发者的完整可读投影；
- `hld-cross-index.json`：跨模型 ID 索引；
- `hld-traceability-matrix.json/.md`：构思控制到 HLD 决定到 LLD 工作单的追溯；
- `lld-handoff.json`：LLD 唯一正式入口。

### 10.2 验收与审计证据

- `hld-semantic-review.json`：HQ1 的独立语义审查；
- `handoff-consumption-test.json`：handoff-only 消费者在看不到机器包内容时形成并密封的重建证据；
- `handoff-fidelity-test.json`：另一个隔离任务对密封重建结果和机器包的一致性证据；
- `lld-handoff-acceptance.json`：HQ2 composite publisher 对前两项证据的确定性聚合结论；
- 发生返工时的 `revision-plan.json`、各 target group 结果及 superseded/retarget 证据；
- 各 stage 的 validation、manifest、completion、execution 与当前 hash 链。

这些文件证明机器内容可发布，但不是新的故事内容权威；任何审查结论都不得覆盖 10.1 的 canonical 值。

### 10.3 人审包

- `hld-human-review-report.json`；
- `hld-human-review-report.html`；
- `render-target-registry.json`；
- `presentation-fidelity-review.json`；
- `hh1-publish-execution.json` 及对应 validation、manifest 和 completion。

### 10.4 最终闭合包

- `author-decision.json`；
- `hld-completion.json`；
- `final-validation.json`；
- 当前 run-state 与所有 completion 的 hash 链。

## 11. 合格 HLD 的交付标准

正式 HLD 只有同时满足以下条件才合格：

1. baseline 当前重新验证为 ready，且所有权威值和开放项保持不变；
2. 总体结构从开端到结局边界连续，每个单元都有进入—变化—退出合同；
3. 所有强制故事线被编排，可选线有明确处置，线间连接与主体一致；
4. 所有核心人物弧线与事件、关系、选择、代价和结果一致；
5. 所有知识变化有来源，POV 不越权，setup—probe—reveal—payoff 无断链；
6. 时间、位置、资源、权限、知识和关系状态连续；
7. 节奏、张力与情绪存在累积、转折、恢复和高潮，不是机械等距或单调上升；
8. 关键场景功能覆盖全部高层义务，且没有动作、对白、感官和正文泄漏；
9. HQ1 独立语义审查通过，并为每个 pass 维度提供反证挑战与对象证据；
10. HP1 可无损还原所有 canonical 模型；HQ2 的 handoff-only 消费任务无需猜高层结构，且其密封结果经独立 fidelity task 证明与机器包一致；
11. `source_authority_refs[]` 与 `ownership_class` 分层成立，不存在权威来源和 HLD 归属混写；
12. HQ2、HH1 的顶层 completion 只由固定 composite publisher 在全部内部包通过后产生；
13. 人审包与机器包没有 material drift，独立 HH1-B 证明作者能在十分钟内回答固定决策问题；
14. 作者明确批准当前机器包与人审包；
15. finalizer 重验通过，`hld-completion.json` 绑定当前 `lld-handoff.json`。

不得用总分抵消任一硬失败；不得用固定对象数量代替覆盖和必要性。

## 12. 验收方法

### 12.1 确定性验收

- 所有 JSON 通过版本化 schema，`additionalProperties: false`；
- 所有引用具有 path、SHA-256、run ID、owner 和 current completion；
- manifest 文件集合与包 profile 精确相等；
- validator 只读重算结果与 stored validation 字节一致；
- ID 集合、跨模型引用、章节父子关系、顺序、覆盖和 authority partition 做集合相等检查；
- `source_authority_refs[]` 到 `ownership_class` 必须满足 catalog 2.14 的全映射，review verdict 到 stage result 必须满足 2.15 的全映射；
- HQ2、HH1 的顶层 ready completion 与 non-ready stage result producer 必须是 catalog 2.16 的固定 publisher profile；内部 task 不得直接驱动 router，早停时后续 internal task 必须证明未签发；
- `stage-result.json` 必须位于内容包外且唯一；top-level/composite-internal ready 的 completion/internal-manifest 条件字段互斥；
- 每个被投影 non-quality unresolved source 的 HA1–HK1、每个 quality unresolved source 的 HQ1 都有 `HDD-`，HB0/Harness 没有语义 disposition，HQ1/HP1 的审查与聚合边界成立；
- 多 owner finding/author targets 全部进入一个 current revision plan，active/pending/resolved/superseded 集合互斥且并集等于全部 target groups；
- `HRE-/HVG-/HUI-` 可从作者 target 唯一路由到 HH1-A/HH1-C 或原 canonical owner，不存在 `element_id` 同义字段；
- 相同输入、实现和版本重复运行，所有确定性产物字节一致；
- 上游变化、实现变化、错 owner、错顺序、旧 return 或额外文件均 fail closed。

### 12.2 语义验收

HQ1 逐项给出 `pass / revise / fail`：

- 构思继承；
- 总体叙事结构；
- 多故事线完整性；
- 人物弧线与事件对齐；
- POV、信息与悬念；
- 时空连续、节奏与张力；
- 关键场景功能充分性；
- 主题通过人物选择与后果得到支撑；
- 组装前的开发义务完整性；
- HLD／LLD 边界纪律。

任何 HQ1 维度 `fail`、任何 blocker 或 HQ2 handoff acceptance 不通过，均不得进入后续准入。

每个 HQ1 pass 维度必须包含已执行的反证挑战、对象证据和为何未形成 finding；只写结论无效。HQ2 必须先在禁止读取机器包内容的上下文中重建、全量追踪强制对象、检查约束分类和缺失猜测；该结果密封后，另一个上下文才能读取机器包做 fidelity 对照。`missing_guesswork` 非空、任一越界读取或 fidelity 漂移均 fail。

### 12.3 人审验收

作者只审当前 HH1 HTML，但决定必须同时绑定 HP1、HQ2 acceptance 与 HH1。报告必须让作者直接看见结论和结构关系，而不是 Agent 推理过程；作者可从任一图表或结论追溯到 HP1 source ID。独立 HH1-B 必须证明估算阅读时间不超过十分钟，且作者无需访问机器包即可从报告回答 catalog 14.5 的固定结构、故事线、人物弧线、POV／知识、时空、关键功能和边界问题。

### 12.4 两层 agentic eval

- **Bounded-skill 层**：catalog 第 20 节的 14 个技能分别执行固定 ID 的 positive、negative、boundary case；`scope_fidelity / input_gate_obedience / output_contract_correctness / semantic_or_deterministic_correctness / boundary_discipline / parent_consumability` 六维全部必须 2/2 且无 blocker，技能之间不得用总分相互抵消。
- **Harness 层**：catalog 第 21 节用 P01/N01/B01 及 HDD/多目标返工事务回归 R01/R02，独立验证整链编排、门禁、return、作者事务、adapter 忠实性和 release 可移植性；七维各 0–2，总分至少 12/14 且无 blocker 才是 `pass`，10–11 为 `pass_with_risks`，低于 10 或有 blocker 为 `fail`。

两层不能互相替代：技能全过不证明调用链正确，整链总分也不能掩盖某个技能越权或漏检。

## 13. 必须通过的端到端契约场景

| 场景 | 预期结果 |
| --- | --- |
| 正常批准 | HB0–HK1、HQ1、HP1、HQ2、HH1 连续 ready，approved 后生成 HLD completion |
| 输入独立 Markdown 或旧 HLD | HB0 blocked，不启动 HA1 |
| baseline 任何文件漂移 | preparation 重验失败，HB0 blocked |
| `must_ask` 被 Agent 自动回答 | 当前 stage fail，生成 author return |
| `authority_class=downstream_freedom` 被直接写成 `lld_freedom` | 映射验收失败；必须先依据 baseline `classification` 和当前 HLD 是否需要决定来分类 |
| `open_item=true` 与 `must_ask` 重叠却在 HLD 中被清除 | 权威继承失败；无外部 resolution 不得继续 |
| HS1 遗漏强制故事线 | HS1 不得 ready；若 HQ1 发现，定向退回 HS1 |
| HC1 给既有人物新增未授权感情 | 语义 blocker，退回 HC1；若构思本身需改，退回构思 owner |
| HI1 让 POV 泄露无权信息 | HI1 revise/fail，HI1–HH1 失效 |
| HR1 出现不可能的迁移或时间顺序 | HR1 revise/fail，HR1–HH1 失效 |
| HK1 写出具体对白或动作 | LLD leakage blocker，退回 HK1 |
| HQ1 无法读取 source index 授权的原始权威对象，或读取 producer rationale | 审查隔离契约失败；不得形成产品语义 verdict |
| HQ2 消费正式 handoff 仍需猜结构或新增主要事实 | HQ2 fail，按来源退回 HP1 或原设计 owner，不进入 HH1 |
| HQ2 consumer task 读取机器包、spec 或 canonical | 隔离违规，整个 HQ2 无效；不得以 fidelity 结果补救 |
| HQ2 fidelity task 在 consumer 结果密封前启动，或改写 reconstruction | HQ2 fail closed，不发布顶层 completion |
| HQ2／HH1 内部 task 自行生成顶层 completion | publisher 身份校验失败，复合 stage 不得 ready |
| 上游 authority class 被写入 HLD ownership 字段 | schema／映射验收失败，退回产生该 canonical 的唯一 owner |
| reviewer verdict 与 stage result 不符合固定代数 | router 拒绝消费，保持前一 current state |
| 中途 must-ask 需要作者回答 | 生成密封 question、外部 answer 和 resolution；HLD 局部回答从原 stage 恢复，改变构思则退出并重做 baseline |
| HB0 或 Harness 预先替 unresolved source 生成“当前 HLD 不需要”结论 | 权限失败；只有实际消费该 source 的 HA1–HK1 可生成 stage-scoped HDD，HP1 只能在 HQ1 pass 后聚合 |
| 任一 stage revise／blocked | 生成 stage result 与 result manifest；router 产生唯一 revision plan、question 或 stop；plan 内可有多组目标但只有一个 active group，旧下游不得继续 current |
| HLD 暴露新的结构性现实事实依赖 | 不自行研究；返回构思研究 owner，重新批准和 preparation 后新建 HLD run |
| 人审报告增强或改写机器结论 | HH1-B fail，不生成正式 HTML |
| 人审报告忠实但超过十分钟或固定问题无法检索 | HH1-B fail，退回 HH1-A 压缩与重组；不得删除 material control |
| 作者只改 HTML 表达 | 只退回 HH1-C，不重跑 HLD 内容 |
| 作者修改故事线编排 | router 退回 HS1，HS1 之后全部失效 |
| 作者同时修改 HS1 编排与 HH1-C 表达 | router 生成两个有序 target groups；先解决 HS1，重跑后在 HH1-C 消费第二组；两项均不丢失并重新进入作者门 |
| 上游返工后某个待处理报告／HTML target 消失 | target group 标记 superseded 并请求重新定位；不得静默完成或丢弃 |
| 作者要求改变构思事实 | 退出 HLD，回构思 owner；重新批准和 preparation 后新建 HLD run |
| 复用旧 completion 或跨 run 混包 | hash、run-state、input-gate 校验失败 |

## 14. 实现边界与顺序

未来实现必须只有一个 portable source root，至少包含 `manifest.yaml / agent.md / workflow.md / rules.md / schemas/ / validators/ / evals/cases/ / adapters/codex/ / tools/`。Portable core 拥有本文与 catalog 的全部语义；Codex adapter 只映射启动方式、工具权限、隔离 task 和作者事件，不得改变阶段顺序、字段、verdict、Pass Bar 或 unsupported 行为。其他 runtime 在独立 adapter、eval 和 build validation 完成前必须显式标记 unsupported。

Release contract 固定要求 source package、Codex runtime package、相对路径 release manifest 和 checksums；build 必须重新执行 source validation、bounded-skill eval 声明检查、harness-level eval 声明检查和 runtime package validation。含机器本地绝对路径、缺 adapter mapping、缺 eval evidence 或未验证的包不得发布。

本设计确认后，开发必须按以下顺序进行：

1. 建立 `harnesses/novel-hld-autonomous/` portable core；
2. 实现公共 schema、run-state、input-gate、内容包／结果信封分层、completion、stage-scoped HDD、revision plan、author decision、authority 双层字段和 verdict-to-result 代数；
3. 实现 HB0 及 preparation compatibility lock；
4. 按 HA1 → HS1 → HC1 → HI1 → HR1 → HK1 顺序开发并逐个验收；
5. 实现 HQ1 anchored semantic review；
6. 实现 HP1 和从 HK1 `lld_work_requirements` 一对一投影的 `lld-handoff.json`；
7. 实现 HQ2 的 handoff-only consumer task、密封、独立 fidelity task 和固定 composite publisher；
8. 实现 HH1-A / HH1-B / HH1-C、十分钟决策可用性验收和固定 composite publisher；
9. 实现 stage-result、author-question、reality reentry、final author gate、HF1、崩溃恢复和定向 return；
10. 按 catalog 第 20 节通过 14 个技能的 bounded-skill eval，再按第 21 节通过 harness-level eval，并通过本文件第 13 节全部 E2E 契约场景；
11. 用《断线》完成一次真实全链运行并由作者验收。

每个 eval case 必须包含 Prompt、预先密封的 fixture/manifest/hash、唯一缺陷注入、Expected Behavior、Forbidden Behavior、逐维 0–2 评分规则和 Pass Bar。Bounded skill 遵守“固定六维全部 2/2”；整条 harness 的 P01/N01/B01/R01/R02 均遵守“无 blocker 且至少 12/14”。生产 E2E 还必须同时通过本文件第 11、12 节的领域验收，不能只凭任一层 agentic eval 发布。

旧 `novel-hld-writer` 可以拆取方法论素材，但不得作为新 harness 的生产 owner、备用 owner 或跳过中间阶段的兼容入口。旧 `novel-lld-writer` 也不能反向定义本 HLD 的契约；未来 LLD 链必须以 `lld-handoff.json` 为唯一正式输入重新设计。

## 15. 设计完成定义

本设计只有在以下事实都成立后，才可进入实现：

- HLD 目标、非目标和四层边界没有重叠；
- 14 个技能均有唯一 owner、明确输入、canonical 输出和 blocker；
- HA1–HK1 的依赖只向前，且每个上游输出都是下一阶段所需字段的唯一来源；
- 输入拓扑、state、stage-scoped unresolved assessment、revision plan、单 active／多 pending return、失效后缀和最终 author gate 都有确定规则；
- 上游权威继承、HLD 归属、review verdict、stage result 和复合 stage 发布各自只有一个明确语义与 owner；
- Catalog 是字段、artifact role、访问权限、内容包／结果信封和 package profile 的唯一规范源；主设计中的每个实现名都能回指 catalog，不存在同义字段漂移；
- HP1 只组装，HH1 只呈现，HF1 只封闭，HQ2 与 HH1 的内部 task 均不能越权发布顶层 completion；
- 14 个技能均具有 positive、negative、boundary eval 槽位、固定六维和不可抵消的 bounded-skill Pass Bar，整条 harness 另有 P01/N01/B01 与 R01/R02、七维评分和 12/14 Pass Bar；
- 人审验收既证明机器包忠实性，也独立证明十分钟内的作者决策可用性；
- 最终交付物与验收方法能证明“输入构思访谈结果，经正式构思与准备包，输出合格 HLD”；
- LLD 可以只依赖正式 handoff 启动，而不需要聊天、旧稿或隐含上下文。
