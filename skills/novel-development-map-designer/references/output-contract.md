# 小说开发地图交付契约

## 1. 契约目的

D1 将作者已批准的构思骨架发展为可供后续小说开发使用的完整构思与功能地图。它不改写作者锁定项，但必须为进入章节开发前的必要缺口执行受控创作。`map-data.json` 是唯一内容模型；地图与覆盖矩阵由确定性渲染器生成，`map-check.md` 只能由权威验证器根据实际 verdict 生成；`package-manifest.json` 是 D1 completion 唯一允许绑定的设计产物。

## 2. 输入权威与硬准入

`input_gate` 必须哈希绑定：

- 当前 `run-state`，且 `active_return` 为 `null`；
- 当前 I0–I5 completion；
- 通过主 harness 校验且 semantic verdict 为 `pass` 的 V1 completion；
- 当前 V2 completion；
- 明确批准当前 V2 HTML 的 `author-approval.json`。

所有记录必须属于同一 run。聊天、旧稿、旧地图、访谈报告、V1/V2 说明和 HTML 都不能提供新故事事实。

唯一内容输入是 I0–I5 completion 各自哈希绑定的六份设计产物：

| area | stage | 权威产物 |
| --- | --- | --- |
| `intent` | I0 | `intent-card.md` |
| `subject` | I1 | `subject-definition.md` |
| `world` | I2 | `world-operating-contract.md` |
| `character` | I3 | `core-character-design.md` |
| `causality` | I4 | `causal-storyline.md` |
| `narrative` | I5 | `narrative-contract.md` |

## 3. 两种合法运行模式

### 3.1 地图模式

目录包含 `map-data.json`，其 `schema_version` 必须为 `4.0`。候选状态可以是 `ready`、`revise` 或 `blocked`；只有所有门通过且状态为 `ready` 才能产生 ready verdict。

### 3.2 准入阻塞模式

硬准入失败时不得制造半成品地图。目录只提供 `gate-data.json`：

```json
{
  "schema_version": "1.0",
  "harness": "novel-conception-interview",
  "run_id": "RUN-ID",
  "status": "blocked",
  "input_gate": {},
  "declared_failures": [
    {
      "id": "GATE-001",
      "problem": "可复核的准入失败",
      "evidence": "缺失或失效的具体引用",
      "owner": "I0|I1|I2|I3|I4|I5|V1|V2|AUTHOR",
      "required_action": "恢复准入所需的唯一动作"
    }
  ]
}
```

验证器据此生成 `blocked-map-report.md`。阻塞包不得含 ready 三件套或 package manifest。

## 4. `map-data.json` 4.0

### 4.1 顶层

```json
{
  "schema_version": "4.0",
  "harness": "novel-conception-interview",
  "run_id": "RUN-ID",
  "status": "ready",
  "input_gate": {},
  "source_artifacts": [],
  "allowed_povs": [],
  "control_points": [],
  "authority_partition": {},
  "development_gaps": [],
  "design_decisions": [],
  "units": [],
  "conception": {
    "world": {
      "event_environment_requirements": []
    },
    "story": {
      "phases": [],
      "major_events": [],
      "storylines": [],
      "storyline_demands": [],
      "storyline_architecture": {}
    },
    "characters": {
      "demand_register": [],
      "profiles": [],
      "relationships": []
    }
  },
  "information_obligations": [],
  "derivation_claims": [],
  "terminal_threads": [],
  "coverage": [],
  "open_items": [],
  "semantic_checks": {},
  "handoff_self_test": {},
  "declared_blockers": []
}
```

### 4.2 `source_artifacts`

必须恰好六条且每个 area 一条：

```json
{
  "id": "SRC-I0",
  "area": "intent",
  "stage": "I0",
  "path": "../../interviews/I0/intent-card.md",
  "sha256": "64位SHA-256"
}
```

路径和哈希必须与对应 completion 的 `design_artifact` 完全一致。任意复制件、摘要或手填路径均不构成来源。

### 4.3 `control_points`

每条控制点只表达一个可判断要求：

```json
{
  "id": "INT-001",
  "area": "intent",
  "kind": "promise",
  "text": "来源设计稿中逐字存在的权威原子陈述",
  "hardness": "hard",
  "owner_stage": "I0",
  "sources": [
    {
      "artifact_id": "SRC-I0",
      "section": "精确 Markdown 标题",
      "evidence": "该标题正文内逐字存在的短证据",
      "evidence_sha256": "证据文本的SHA-256"
    }
  ]
}
```

约束：

- `area` 为 `intent / subject / world / character / causality / narrative`；
- `hardness` 为 `hard / delegated / open`；
- `owner_stage` 必须与 area 一致；
- `sources` 至少一条，且至少一条来自本控制区；
- `text` 必须与本控制区一条已验证 `evidence` 完全相同；不得把解释或推断伪装成上游事实；
- 控制点不得含自由解释字段；其开发含义只能出现在单元字段及对应的哈希绑定 `derivation_claims` 中；
- 标题必须在来源文档中唯一，证据必须逐字位于该节正文且哈希匹配；
- 来源只证明上游确实说过什么，不授权 D1 扩张其含义。

### 4.4 自主权限、开发缺口与设计决定

`authority_partition` 必须把全部控制点按 hardness 精确分为三组，并声明工作边界：

```json
{
  "author_locked": ["INT-001"],
  "delegated": ["CAU-004"],
  "open": ["INT-009"],
  "autonomous_mandate": "在不改变控制点的前提下补足进入章节开发所需的运行、因果、阻力、策略、代价和信息设计。",
  "downstream_reserved": "章节、场景、对白、动作、意象、文风和非结构性实现留给后续开发。",
  "prohibitions": "不得改写作者锁定项，不得裁决开放项，不得把新增决定伪装成上游事实。"
}
```

`development_gaps` 记录从访谈骨架到可开发构思之间的真实缺口：

```json
{
  "id": "GAP-001",
  "domain": "world|story|character|cross",
  "kind": "causal_bridge|opposition|world_operation|character_tactic|choice_cost|relationship_change|information_design|thematic_test|supporting_function|ending_setup",
  "question": "若不回答，章节开发者必须临时发明的核心问题",
  "why_needed": "该问题阻碍了什么开发判断",
  "source_controls": ["CAU-001"],
  "resolution": "autonomous_decision|downstream_freedom|author_open",
  "decision_ids": ["DEC-001"],
  "downstream_reservation": null
}
```

- `autonomous_decision` 必须具有一条或多条反向一致的设计决定，不得同时保留下游；
- `downstream_freedom` 不得创建决定，必须说明为何不影响核心逻辑；
- `author_open` 必须引用至少一个 open 控制点并说明如何保持开放；
- ready 包不得含未分类、无去向或需要上游裁决却伪装成下游自由的缺口。

`design_decisions` 是 D1 新增故事内容的唯一合法入口：

```json
{
  "id": "DEC-001",
  "domain": "cross",
  "kind": "causal_bridge",
  "statement": "D1 选择并承诺的新设计",
  "function": "它在故事中完成什么",
  "gap_ids": ["GAP-001"],
  "source_controls": ["CAU-001", "CHR-003"],
  "novelty": "inference|concretization|invention",
  "authority_basis": "为何属于 D1 受控创作而非作者专属决定",
  "necessity": "缺少它会怎样破坏开发",
  "compatibility": "怎样同时遵守相关控制点",
  "alternatives": [
    {
      "id": "ALT-001",
      "proposal": "候选方案",
      "benefit": "该方案的真实收益",
      "cost": "该方案的真实代价",
      "status": "selected|rejected"
    }
  ],
  "impact": "local|structural",
  "reversibility": "local|cross_unit|whole_design",
  "projected_subjects": ["WORLD-001", "U03"],
  "downstream_freedom": ["下游仍可自主决定的实现"]
}
```

约束：

- 每项决定至少比较两个真实方案且恰好一个 `selected`；
- 决定陈述不得逐字重复控制点，必须产生新的、可执行的开发判断；
- 每项决定至少投影到一个功能单元，并投影到世界／故事／人物／阶段／信息义务之一；
- 投影必须与单元的 `development_decisions` 双向一致；
- 决定只能解决已登记的自主缺口，不能绕过作者开放项；
- 决定可以引用 hard 控制点作为边界，也可引用 delegated 控制点作为授权；引用不等于改写；
- 只列方案而不作选择、只写建议而不进入模型、或新增内容没有影响对象，均不能 ready。

### 4.5 `conception`

`conception` 是完整小说构思的正面设计层，必须且只能包含 `world`、`story`、`characters`：

- 构思内部的生产依赖固定为：`story.storyline_demands / storylines / storyline_architecture / major_events → world.event_environment_requirements / systems / environments → characters.demand_register / profiles / relationships`。这是生产顺序和证据顺序，不改变最终交付仍以世界、故事、人物三板块呈现；
- `world`：定义故事实际运行的总体世界、时空范围、运行逻辑、权力与资源、行动权限、硬约束、压力来源、代价与后果、结局后的世界状态及明确不开发的范围；还必须包含 `facets`、`systems`、`environments` 与 `event_environment_requirements`；
- `world.facets`：恰好覆盖 `ontology_and_nature / time_and_history / space_and_geography / society_and_culture / institutions_and_power / economy_and_resources / law_ethics_and_norms / daily_life` 八个世界信息域。每域标记 `defined / not_applicable`，说明定义、故事关联、自主决定和下游自由；不得以“与故事无关”无理由省略；
- `world.systems`：至少一个真正控制事件的运行系统。每个系统明确领域、行动者、资源、规则、权限、成本、限制、失败方式、故事作用、故事内状态变化、来源控制点、自主决定和下游自由；
- `world.environments`：覆盖全部开发单元所使用的主要环境。主要环境是承载核心行动、持续塑造人物感知，或决定关键许可、资源与风险的有边界物理、数字、记忆、制度、社会或混合场域。每个环境明确名称、类型、定义、范围、鲜明特征、基本要素、感知条件、进入者与访问、资源设施、可行动作与规则、危险压力、故事功能、状态变化、故事线与单元投影、自主决定和下游自由；还必须包含 `topology` 与 `event_hosting`。不得以偶发地点、工作流程、规则清单或信息生命周期冒充环境设计；
- `world.environments[].topology`：包含非空 `boundaries`、非空 `zones` 和 `connections`。每个功能区具有稳定 ID、名称、功能、当前状态、规范人物 ID 数组和可用资源；无人设备区、隔离危险区或当前不可进入区允许人物数组为空，但事件的在场人物仍必须位于至少一个使用区。多区环境必须全部连通，每条连接说明通道、准入条件与阻断后果。单区环境允许空连接；数字、记忆和制度环境允许逻辑区或权限区；
- `world.environments[].event_hosting`：与该环境 `unit_ids` 精确一一对应。每项说明单元、使用功能区、在场规范人物、事件功能、进入状态、可行动作、被阻断动作、环境压力和离开状态；进入与离开必须不同，可做与不可做不得重合。在场人物必须承担该单元并位于至少一个使用功能区；
- `world.event_environment_requirements`：在故事线架构和全局主要事件完成后，为每个主要事件恰好登记一条环境需求。每条说明主要／次要承载环境、事件所需的环境能力、功能区、资源、权限、信息通道、风险约束、跨环境转场要求及充分性理由；其环境集合必须与事件 `environment_ids` 完全一致，全部需求共同覆盖全部主要环境。该台账用于证明环境由故事需要反推，而不是先造地点再硬塞事件；
- `story`：定义核心承诺、故事归属、中心冲突、戏剧问题、风险、起点、触发、递进逻辑、高潮、结局、开放线程及范围排除；还必须包含 `event_span`、`event_source_coverage`、`major_events` 与 `storylines`；
- `story.event_span`：界定从本书最早的因果变化到最终余波的完整事件跨度，登记开篇事件、主行动入口与余波事件。不得把主角或核心载体启动误当成故事的天然起点；若上游确认了此前发生且本书需要呈现、核验或承担后果的死亡、失败尝试、任务交接、批准、抵达、承诺或其他变化，它们必须进入跨度；
- `story.event_source_coverage`：逐项登记从六份权威访谈成果中扫描出的因果前提、因果转变、叙述必须呈现事实、人物转变、世界状态变化、行动步骤和静态背景。每项保存权威原文摘录、来源位置、候选类型、处置和对应主要事件。除真正静态背景外，事件候选不得以“前提”“背景”名义排除；引用的主要事件必须在标题、发起行动、决定性变化或直接结果中实际实现该来源变化，不能只把它写入 `preconditions`；
- `world.systems`：每个系统必须同时给出输入条件、转换规则、可观察输出、覆盖环境与覆盖主要事件，并说明行动者、资源、权限、成本、限制、失败方式和状态变化。全部系统必须合计覆盖全部主要环境和主要事件；仅有概念名称、零散规则或“技术存在”的描述不构成可运行世界机制；
- `story.major_events`：是主要事件的全局唯一事实源，按故事世界因果顺序登记，不按章节或叙述顺序排列。每个事件具有稳定 ID、标题、事件角色、可观察定义、所属故事线、承载单元、承载环境、参与人物、发起行动者、对抗行动者、前提、发起行动、对抗或复杂化、决定性变化、直接结果、前后状态、下一压力、信息变化、因果前驱、自主决定和下游自由。发起行动者与对抗行动者必须属于参与人物，其规范姓名必须实际出现在对应行动文本中；任何承担 `opposition_execution` 需求的人物，必须至少在一个主要事件中实施可观察的反制。一个主要事件只承担同一时空压力下的一项主导状态变化；若死亡、失败尝试、批准／接受任务、救援、证词、硬件控制、授权核验等步骤分别改变可用人物、信息、资源、权限或目标，就必须拆成独立事件。事件必须引用真实单元、规范人物和实际承载该单元的主要环境；除每条线的首个事件外，后续事件必须引用该线更早的主要事件作为因果前驱；
- `story.storyline_demands`：先扫描本书需要独立推进、合并推进或作为背景持续施压的故事义务。每项说明需求、故事功能、遗漏后果、处置、对应故事线和理由；处置为 `dedicated_line / integrated_into_lines / not_applicable`。全部因果控制点必须被扫描，全部实际故事线必须由至少一项需求证明必要性。不得用预设的三条线代替发现工作；
- `story.storylines`：恰好一条 `main`，并按实际需要包含任意数量的 `precursor / subplot / background`。`precursor` 用于主行动形成前彼此独立推进、随后汇流的前置线。每条说明功能、承载者、核心问题、起点、驱动力、升级、按因果顺序排列的 `major_event_ids`、结局状态、闭合方式、承载单元、自主决定和下游自由；`protagonists` 必须是规范人物 ID，不得保存自由文本、抽象团队、机构或国家；主线至少三个主要事件，其他线至少两个；全部故事线共同覆盖所有功能单元并引用全部主要事件。每条线至少由一名规范人物和一个主要环境承载；每个事件—故事线组合至少有一名承担该线的参与人物及一个承担该线的事件环境，明确连接点允许进入线在责任移交事件中由离开线人物接手。多承载者必须在该线关系子图中连通。`subplot` 还必须通过至少一个主要事件实质改变主干选择、代价、信息、资源、权限、关系状态或结局条件；只有假设性风险而没有状态变化的内容不得独立成线；
- `story.storyline_architecture`：明确入口故事线、唯一主干故事线、终点故事线和连接点。连接点类型为 `merge / split / handoff / collision / reveal / synchronization`，必须锚定一项全局主要事件，列出进入线、离开线、成立前提、转移的目标／信息／责任／压力及结果状态。多线故事的每条非主线必须参与至少一个连接点，并沿有向连接路径进入主干；汇流、分叉和交接不能只靠文字声称；
- `story.melody_lines`：可选的情绪、意象、称谓、日常或认知变奏层，不属于结构故事线，也不进入 `storyline_architecture`。每条必须包含稳定 ID、标题、功能、三个至七个按因果顺序排列的既有事件锚点、递进变奏、可扩展方式、删除影响、边界、系列潜力、来源、设计决定和下游自由；`required_for_causality / required_for_resolution / new_pov_allowed / carries_decisive_information` 必须全部为 `false`。删除整条旋律线后，主因果、结局、POV 和决定性信息必须仍然完整；
- `story.phases`：按开发顺序完整且不重复地覆盖全部功能单元。每阶段只写进入状态、驱动目标、压力、决定性变化和退出状态，不得写成章节或场景；
- `characters`：先发现故事运行必需的人物职责，再覆盖推动主线所必需的核心、支持与外围人物，明确角色职责、故事功能、起点、表层目标、深层需要、回避、价值与边界、信息限制、受压行为、能动选择、关系、变化阶段、终态和不变量；
- `characters.demand_register` 必须精确覆盖 `decision_authority / information_transfer / expertise_formation / opposition_execution / relationship_pressure / operational_execution / aftermath_responsibility` 七类职责。每项说明触发条件、故事职责、遗漏后果、结构重要度、来源对象与处置：要么解析到唯一规范人物档案，要么仅在确属非结构性语境时以 `contextual + not_applicable` 留下可审计理由。结构性或支持性职责不得标成不适用，也不得解析到外围人物或抽象组织。
- `characters.profiles` 是全部核心、支持和外围人物的唯一事实源。每个人物只出现一次，并在同一档案中给出 `importance`、命名状态、职责、故事功能、起点、表层目标、深层需要、回避、价值与边界、信息限制、受压行为、能动选择、人物弧、终态、不变量、故事线、单元和下游自由。
- `characters.relationships` 是全部人物—人物关系边的唯一事实源。每个无向人物对只能有一条边；两端必须引用 `profiles` 中的真实人物。关系边只记录共同历史、关系类型、立场、冲突、筹码、信息差、变化、故事线、单元、来源、自主决定和下游自由，不得重复保存任一人物的目标、需要或档案。凡直接完成关键交接、承诺、拒绝、救援、胁迫、告别或关系变化的人物对，都必须判断并登记其直接关系，不得以人物图中的间接可达性代替现实关系；关系的故事线投影必须覆盖其实际改变选择、代价、信息或末态的全部线路。
- 多机构或多国家结果若使用“同意、授权、拒绝、承诺、联合复盘、接受核验”等决定性表述，每一方必须由主要事件中的规范人物，或 `event_environment_requirements` 中有来源、权限和回执的受控通道承载。单方记录不得被写成多方共同决定。环境中的实际进入者、远程受控参与者与外部权利／风险边界必须分开表述；外部人物不得因被环境文字提及而获得未登记的知情、访问或行动权限。
- 每个非核心人物都必须能从至少一个核心人物到达。对每个核心人物，验证器依据全局关系边重算最短人物路径；最大深度至少为 3，且第 1、2、3 层必须连续存在。层级是派生视图，不得以 `relationship_layers`、`via_character_id` 或人工层号再次存储。
- 机构、组织、项目、群体、历史力量和抽象概念可以构成世界压力，但不能冒充人物节点。承担选择或影响关系路径的角色必须成为具有完整定义的 `profiles` 记录。
- 核心与支持人物必须使用 `confirmed` 或 `autonomous` 完成具体姓名；不得把“领导、老师、接头人、队长、专家”等功能标签伪装成姓名。只有确属语境性外围人物且没有结构职责时可以保留 `functional`。同一核心人物网络中，同一人物不能在多层重复出现，至少存在一条连续人物路径到达第 3 层。

每个世界、故事、阶段和人物记录都有稳定 ID 与 `source_controls`。世界至少覆盖 world 控制区；故事至少覆盖 intent 与 causality；每个阶段覆盖 causality 且其来源属于故事来源；每个人物至少覆盖 subject 与 character。人物 `arc_stages` 只能引用该人物承担的单元，同一人物的阶段不得重复覆盖单元。

完整意味着：后续开发者无需发明新的世界规则、主线因果、核心人物动机或关键选择，就能进入章节设计。完整不意味着：提前规定章节数、场景、对白、动作、意象、文风，或扩写与本故事无关的百科资料。

### 4.5 `units`

每个功能单元必须包含：

| 字段 | 约束 |
| --- | --- |
| `id`、`title` | 全包唯一、稳定 |
| `purpose` | 单元不可删除的开发作用 |
| `source_controls` | 非空，全部为已知控制点 |
| `causal_nodes` | 非空，只引用 area 为 `causality` 且已列入本单元 `source_controls` 的控制点 ID |
| `pov` | 引用 `allowed_povs` 中的控制点 ID；该控制点必须属于 `narrative` 且列入本单元 `source_controls` |
| `preconditions` | 非空，开场已成立状态 |
| `objective` | 谁追求什么 |
| `obstacle` | 什么阻碍目标 |
| `opposition` | `{force,goal,tactic,leverage,adaptation}`；对抗可来自人物、机构、环境、规则或内部冲突，但必须会回应行动 |
| `choice` | 谁作出什么不可替代选择 |
| `choice_options` | 至少两个包含 `{id,option,attraction,cost,status}` 的真实选项，恰好一个 selected |
| `choice_cost` | 被选择方案支付什么，并永久或暂时放弃什么 |
| `consequence` | 选择直接造成的可观察结果 |
| `next_pressure` | 该结果怎样制造下一问题；终点也须说明剩余压力或关闭理由 |
| `development_decisions` | 投影到本单元的 D1 新增设计决定 ID，可为空但必须与决定反向链接一致 |
| `value_shift` | `{axis,before,after,turning_cause}`，前后不得相同 |
| `information` | `{establish,hint,withhold,payoff}` 四个信息义务 ID 数组 |
| `world_constraints` | world 控制点 ID 数组，可为空，但关键行动没有规则依据时语义检查失败 |
| `exit_state` | 非空，供下游消费的末态 |
| `depends_on` | 只指向更早单元，形成 DAG |
| `creative_freedom` | 非空，说明下游可自主实现什么 |
| `prohibitions` | 控制点 ID 数组，可为空，且必须列入本单元 `source_controls` |
| `scale` | `short / medium / long / unspecified` |

`allowed_povs` 自身也是 narrative 控制点 ID 数组，不是自由命名的视角标签。信息四组允许为空；不能为了填字段而伪造信息职责。空数组表示该单元没有这一类责任，不等于豁免 POV、公平性和回收检查。

### 4.6 `information_obligations`

仅为需要跨单元管理铺设、暂缓或回收的信息登记稳定 ID：

```json
{
  "id": "INFO-001",
  "statement": "需要管理的已确认信息职责",
  "source_controls": ["NAR-003"],
  "audience": "reader",
  "knowledge_holder_controls": [],
  "resolution": "within_book",
  "series_interface": null
}
```

- `source_controls` 必须非空且全部存在；
- `audience` 为 `reader / pov_character / story_characters / mixed`；
- `knowledge_holder_controls` 指向能证明具体角色知情边界的控制点；`story_characters / mixed` 时不能为空且必须属于本义务的 `source_controls`；
- `resolution` 为 `within_book / series`；
- 每项义务必须先在某一更早单元 `establish` 或 `hint`；
- 任一 `payoff` 必须晚于该义务的首次铺设；
- `within_book` 必须在本部更晚单元回收；
- `series` 可以不在本部回收，但必须写明 `series_interface`，且地图存在登记为 `series` 的终点；
- 单元信息数组只能引用这些 ID，不接受自由字符串。

### 4.7 `derivation_claims`

任何会改变下游开发判断、但不是上游逐字事实的业务字段都必须登记。4.0 覆盖：

- 控制点：`kind`、`hardness`；
- 单元：`title`、`purpose`、`preconditions`、`objective`、`obstacle`、`opposition`、`choice`、`choice_options`、`choice_cost`、`consequence`、`next_pressure`、`value_shift`、`information`、`exit_state`、`depends_on`、`creative_freedom`、`scale`；
- 信息义务：`statement`、`audience`、`knowledge_holder_controls`、`resolution`，以及 series 义务的 `series_interface`；
- 开放项：`allowed_handling`、`forbidden_resolution`；
- 终点线程：`label`、`role`。
- 完整构思：世界、世界信息域、世界运行系统、主要环境、逐事件环境需求、故事、故事阶段、主要事件、故事线需求、全部故事线、故事线架构、故事线连接点、人物职责需求、人物档案和具体关系记录中除 ID、来源控制点及决定链接外的全部业务字段。

每个主体字段必须恰好登记一条：

```json
{
  "id": "DRV-U01-OBJECTIVE",
  "subject_type": "unit",
  "subject_id": "U01",
  "field": "objective",
  "value_sha256": "该字段规范 JSON 值的 SHA-256",
  "source_controls": ["SUB-002", "CHR-004"],
  "source_decisions": ["DEC-003"],
  "rationale": "为何该开发表达没有扩张所引控制点"
}
```

`subject_type` 为 `control_point / unit / information_obligation / open_item / terminal_thread / world_conception / world_facet / world_system / world_environment / event_environment_requirement / story_conception / story_phase / major_event / storyline / storyline_demand / storyline_architecture / storyline_connection / melody_line / character_demand / character_conception / relationship_layer / character_relationship`。`value_sha256` 使用 UTF-8 编码、键排序且无多余空白的规范 JSON 值计算。`source_controls` 与 `source_decisions` 至少一组非空；控制点必须属于主体声明的来源，设计决定必须明确投影到该主体。新增世界域、系统、环境、逐事件环境需求、主要事件、故事线需求、故事线、故事线架构、连接点、旋律线、人物职责需求、关系层和关系记录的 `development_decisions` 必须与决定投影双向一致。`opposition / choice_options / choice_cost / consequence / next_pressure` 必须引用至少一条设计决定。控制点分类只能引用自身，开放项只能引用其 `source_control`。字段变更后旧 claim 自动失效；R1 必须逐条独立复核这些声明以及设计决定本身。

### 4.8 `terminal_threads`

开发地图可以有多个合法终点。必须为依赖图中的每个 terminal unit 恰好登记一条：

```json
{
  "id": "THREAD-MAIN",
  "label": "主线",
  "role": "main",
  "terminal_unit": "U12",
  "source_controls": ["CAU-010"]
}
```

`role` 为 `main / subplot / series`；至少一条为 `main`。登记集合必须与图中所有无下游单元完全一致。终局完成条件直接由 `source_controls` 的权威文本和终端单元定义，不另写自由解释字段。不得用“恰好一个最终单元”强迫通用小说结构。

### 4.9 `coverage`

每个控制点恰好一条记录：

```json
{
  "control_id": "CAU-001",
  "unit_ids": ["U01"],
  "status": "covered",
  "evidence": "指出单元怎样承担该控制点"
}
```

hard/delegated 必须 `covered` 且有承载单元；open 可为 `open / deferred / covered`。每个单元至少被一条覆盖记录反向引用。

### 4.9 `open_items`

每个 open 控制点恰好一条：

```json
{
  "id": "OPEN-001",
  "source_control": "INT-009",
  "owner_stage": "I0",
  "allowed_handling": "如何保持开放同时继续开发",
  "forbidden_resolution": "下游不得替作者决定什么"
}
```

### 4.10 `semantic_checks`

十三项地图设计者压力测试使用统一结构：

```json
{
  "status": "pass",
  "reviewer_id": "稳定执行者标识",
  "reviewer_role": "map_designer|independent_reviewer",
  "method": "实际采用的检查方法",
  "subject_ids": ["U01"],
  "assertions": [
    {
      "id": "ASSERT-CAUSAL-U01",
      "subject_id": "U01",
      "result": "pass",
      "failure_found": false,
      "test": "对当前字段执行的具体反证测试",
      "failure_condition": "出现什么现象即判失败",
      "counterexample": "实际尝试过的反例或旁路",
      "conclusion": "为什么当前字段组合没有触发失败",
      "field_evidence": [
        {
          "field": "objective",
          "value_sha256": "当前字段值的 SHA-256"
        }
      ]
    }
  ]
}
```

每个断言必须绑定当前单元的实际字段值，且覆盖该检查规定的必要字段；验证器重算字段值哈希，并要求测试、失败条件、反例和结论与所绑定值具有故事特异性重合。`status: pass`、`result: pass` 与 `failure_found: true` 不得并存。只有字段结构、当前值绑定、对象覆盖和失败结果一致时，语义检查才计为通过。

必需项为：

- `gap_resolution`
- `forward_causality`
- `reverse_ending`
- `character_agency`
- `opposition_adaptation`
- `choice_costs`
- `easy_solution`
- `world_permissions`
- `pov_information`
- `plant_payoff`
- `thematic_testing`
- `minimality`
- `downstream_sufficiency`

证据必须覆盖相应单元，不能以 `"pass"` 或空泛总结代替。`easy_solution` 必须实际提出更简单的替代方案并说明为何被人物、规则、信息或代价阻断；`downstream_sufficiency` 必须确认下游无需再发明核心动机、规则或主线因果。

`handoff_self_test` 由地图设计者执行，用于证明包具备可交接性，但不构成独立验收：

```json
{
  "status": "pass",
  "reviewer_id": "map-designer-id",
  "reviewer_role": "map_designer",
  "assurance": "self_test",
  "method": "仅以 D1 包内容作为证据完成八项任务",
  "evidence_scope": "d1_package_only",
  "subject_ids": ["全部单元ID"],
  "evidence": [{"claim": "总体结论", "control_ids": [], "unit_ids": ["U01"]}],
  "tasks": [
    {
      "id": "promise",
      "status": "pass",
      "response": "足以显示真实理解的回答",
      "evidence_ids": ["INT-001"]
    }
  ]
}
```

任务 ID 必须恰好为 `promise`、`autonomous_value`、`causal_chain`、`unit_contract`、`freedom_boundary`、`drift_detection`、`easy_solution`、`scene_plan`。其中 `autonomous_value` 必须指出 D1 相对访谈新增的关键决定及其作用；`easy_solution` 必须攻击构思中最可能的便捷解法。`evidence_scope` 只声明回答的证据边界，不虚构设计者与其上游上下文隔离。R1 必须由不同执行角色基于 D1 包重新执行八任务测试，并逐条复核派生声明和新增设计决定；D1 的自测字符串不能证明独立性。

### 4.11 `declared_blockers`

若必须改变上游控制点才能继续：

```json
{
  "id": "BLK-001",
  "owner_stage": "I4",
  "problem": "相互冲突的已确认因果顺序",
  "affected_controls": ["CAU-004", "CAU-007"],
  "required_decision": "由 I4 确定权威顺序"
}
```

存在任一声明 blocker 时 verdict 必须为 `blocked`。D1 自身的漏项、错链、渲染漂移属于 `revise`，不能滥用上游回退。

## 5. 确定性业务文档

先开始同一 Codex 任务绑定的受控会话，按 `control-model → gap-and-options → story-architecture → event-world-model → character-model → final-map` 提交六个阶段，再封包：

```powershell
python scripts/manage_generation.py begin <input-gate.json> <generation-workspace> ...
python scripts/manage_generation.py submit <generation-workspace> <phase> <phase-artifact.json> ...
python scripts/execute_autonomous.py <generation-workspace> <package-directory> --session-id <session-id>
```

生成：

- `development-map.md`：输入版本、控制摘要、依赖图、全部单元、终点线、开放项与开发授权；
- `coverage-matrix.md`：六区控制点、精确来源、承载单元与覆盖证据；
- `map-check.md`：七项语义证据、交接自测、实际错误／阻塞和权威 verdict；只能由验证器生成。

不得手写或局部修订这三份文件。渲染器只维护前两份，验证器写入并复核第三份；任何漂移均为 `revise`。

## 6. 交付与不可变绑定

地图模式的完整 ready 包恰好绑定：

1. `map-data.json`
2. `generation-session.json`
3. 六份 `generation-evidence/*.json`
4. `execution-record.json`
5. `development-map.md`
6. `coverage-matrix.md`
7. `map-check.md`
8. `validation.json`

`generation-session.json` 绑定真实 `CODEX_THREAD_ID`、输入门、执行者、方法、六阶段顺序、每阶段产物哈希和前向哈希链。故事阶段投影最终故事；事件—世界阶段投影最终故事与世界；人物阶段投影最终三域构思。`execute_autonomous.py` 不接受任意外部候选，只能封存已完成工作区。`execution-record.json` 由正式入口生成，绑定当前技能实现、生成会话、最终模型和 input gate；手写、缺失、阶段篡改、模型变化或技能实现变化都会使 ready 失效。该来源保证属于本地受控任务证明，不冒充密码学签名或执行者诚实证明。

## 7. 完成定义

`ready` 必须同时满足：

1. 同一 run 的当前 I0–I5、V1、V2 和作者批准全部通过硬准入；
2. 六份 `source_artifacts` 与 completion 权威产物逐一同路径、同哈希；
3. 每条控制点具有可复核的精确节证据；
4. 权限分区与控制点 hardness 完全一致；
5. 每个开发缺口都有合法归属；自主缺口全部由反向一致的设计决定解决；
6. 每条设计决定产生上游没有直接给出的开发判断，比较至少两个方案，并记录权限、必要性、兼容性、影响、可撤销性和下游自由；
7. 每条设计决定至少进入一个功能单元和一个世界／故事／人物／阶段／信息对象；
8. hard/delegated 覆盖率 100%，无孤立单元；
9. 每个单元有目标、适应性阻力、真实选项、选择成本、后果、下一压力、状态变化、前后依赖和开发边界；
10. 事件跨度从最早因果变化覆盖至最终余波；事件来源覆盖台账扫描全部权威输入并证明每个事件候选已实现或确为静态背景；不得用后续事件的前提代替先前事件，也不得用一个汇总节点吞并多项独立状态变化；
11. 主要事件是全局唯一、因果有序且可观察的事件定义；每项均连接真实故事线、单元、规范人物与事件承载环境，说明行动、对抗、变化、结果和下一压力；故事线需求覆盖全部因果控制点并证明每条线必要，故事线架构显式表达入口、主干、终点以及汇流／分叉／交接，每条非主线能沿连接路径进入主干；旋律线仅锚定既有事件，具备递进变奏和明确可省略边界，不承担因果、结局、POV 或决定性信息；
12. 每个主要事件具有唯一环境需求记录，需求与事件环境完全一致，环境功能区、资源、权限、信息通道和风险足以承载事件；环境不是与事件脱节的地点清单；
13. 依赖图无环，所有图终点均登记且至少一条主线；
14. 开放项没有被静默裁决；
15. POV、因果、世界权限与禁令引用权威控制点；业务派生字段有值哈希、控制点／设计决定来源和理由；
16. 信息义务具有稳定 ID、明确受众和知识持有者，回收晚于铺设，本部义务完成、系列义务具有合法接口；
17. 十三项压力测试和八项开发交接自测真实完成，且没有冒充独立验收；
18. 地图和覆盖矩阵与模型逐字一致，检查报告与权威验证结果逐字一致；
19. 无声明 blocker；
20. 同一 Codex 任务内六阶段生成链完整，正式自主入口和执行记录有效，manifest 完整绑定执行包，completion 由生成器构造并通过主 harness；
21. 关键构思和检查文本不存在占位语或高重复模板；
22. 同类型对象的功能、压力、选择、变化与退出职责可区分；核心人物的能力边界、受压行为和行动选择不互相冲突，八项自测回答不批量复用。
23. 每条作者锁定的核心承诺具有不可省略的结构事件证明，且能看到默认材料／策略、当前压力、重新判断或选择与可观察后果；旋律线、人物简介或抽象说明不构成唯一证据；
24. 每条独立支线具有实际状态变化；主角策略暴露后，对抗发生适应、可信退出或等价阻力升级；高潮闭合条件在世界系统、事件、人物权限和证据来源间一致；
25. 故事阶段给出足以检验长期关系、倒计时、调查／行动并发和余波真实性的近似时间尺度；若外部行动高潮与主题性不可逆选择不同，二者先后和各自结果均已定义。

## 8. Verdict

| Verdict | 含义 | 后续 |
| --- | --- | --- |
| `ready` | 准入、结构、语义、交接自测、权威重验和不可变包均通过 | 生成绑定 manifest 的 D1 completion，交 R1 做独立验收 |
| `revise` | 上游有效，但 D1 模型、证据、覆盖、依赖或渲染有错 | 只修 D1，重新渲染和验收 |
| `blocked` | 准入失败或必须改变上游决定 | 生成阻塞报告，回到唯一拥有者 |

D1 不发起创作访谈，不改写主题、主体、世界公理、人物根本动机、作者锁定因果、叙述边界或结局；但必须补足这些决定之间的开发逻辑，不能把自身职责伪装成上游缺失。
