# 小说构思交接审阅交付契约

## 1. 契约目的

R1 对 D1 4.0 已执行受控创作的小说构思进行最终技术审阅，证明交付不是访谈总结，而是具有必要、兼容、具体且可开发的新增设计。R1 必须验证生产依赖真实成立：故事线需求、全部故事线、连接拓扑和全局主要事件先完成；世界八域、运行系统与主要环境由逐事件环境需求反推；人物职责、规范人物档案、人物关系边和三层人物网络最后从已确定故事与世界中产生。R1 不创造故事事实。`review-data.json` 是唯一审阅模型；业务文档均由确定性渲染器生成，`independent-handoff.json` 只在 ready 时释放；`package-manifest.json` 是 R1 completion 唯一允许绑定的设计产物。

## 2. 输入权威与硬准入

`input_gate` 必须哈希绑定：

- 当前 run-state，且 `active_return` 为 `null`；
- 当前 V1 completion；
- 当前 V2 completion；
- 当前 D1 completion。

三份 completion 必须属于同一 run，并通过主 harness。D1 completion 必须绑定完整 manifest；D1 权威验证结果必须与包内 `validation.json` 一致。D1 已传递并绑定当前 I0–I5、V2 作者批准和六份权威设计稿，R1 不从聊天或旧稿另选版本。

## 3. 两种运行模式

验证目录必须恰好包含一个根模型：审阅模式使用 `review-data.json`，准入阻塞模式使用 `gate-data.json`。两者不得共存，也不得同时缺失；根模型共存、缺失、不可读取或不是对象均为 hard blocked，并撤销旧的 NDB、审阅报告、handoff、return 和 manifest。

### 3.1 审阅模式

目录包含 `review-data.json` 1.0。候选状态为 `ready / revise / blocked`。只有全部硬门、结构门、语义门、独立交接门和确定性门通过，验证 verdict 才能为 `ready`。

### 3.2 准入阻塞模式

硬准入失败时只提供 `gate-data.json`：

```json
{
  "schema_version": "1.0",
  "harness": "novel-conception-interview",
  "run_id": "RUN-ID",
  "stage": "R1",
  "status": "blocked",
  "input_gate": {},
  "declared_failures": [
    {
      "id": "GATE-001",
      "problem": "可复核的准入失败",
      "evidence": "失效引用或权威验证错误",
      "owner": "V1|V2|D1|AUTHOR|R1",
      "required_action": "恢复准入所需的唯一动作"
    }
  ]
}
```

阻塞模式不得含 NDB、ready 审阅报告、独立交接记录或 manifest。

## 4. `review-data.json` 1.0

### 4.1 顶层

```json
{
  "schema_version": "1.0",
  "harness": "novel-conception-interview",
  "run_id": "RUN-ID",
  "stage": "R1",
  "status": "ready",
  "input_gate": {},
  "reviewer": {},
  "control_area_reviews": [],
  "conception_reviews": [],
  "cross_domain_checks": {},
  "development_gap_reviews": [],
  "design_decision_reviews": [],
  "derivation_reviews": [],
  "world_model_reviews": [],
  "major_event_reviews": [],
  "storyline_reviews": [],
  "storyline_demand_reviews": [],
  "storyline_architecture_review": {},
  "storyline_connection_reviews": [],
  "melody_line_reviews": [],
  "character_demand_reviews": [],
  "character_profile_reviews": [],
  "relationship_edge_reviews": [],
  "relationship_network_reviews": [],
  "subject_ids": [],
  "tasks": [],
  "open_item_reviews": [],
  "findings": [],
  "return_request": null
}
```

`return_request` 在 `ready / revise` 时省略或为 `null`；只有语义 `blocked` 时为对象。顶层 `status` 不是独立裁决源，必须等于 findings 中最高严重度推导出的状态：存在 `blocked` 即 blocked，其次存在 `revise` 即 revise，否则 ready。

### 4.2 `reviewer`

```json
{
  "id": "stable-reviewer-id",
  "role": "independent_developer",
  "assurance": "role_separated_execution",
  "evidence_scope": "d1_package_only",
  "method": "可复核的实际审阅与八任务执行方法"
}
```

reviewer ID 不得等于 D1 `handoff_self_test.reviewer_id`；R1 `CODEX_THREAD_ID` 必须不同于 D1 execution record。该记录证明本地任务隔离，不声称密码学签名或执行者绝对诚实。

### 4.3 六区审阅

在六区审阅前，`conception_reviews` 必须恰好覆盖 `world / story / characters`。每项必须为 `pass`，给出不少于 20 字的可反驳结论、构思对象 ID 和来源控制点 ID：

```json
{
  "area": "story",
  "status": "pass",
  "finding": "故事承诺、中心冲突、递进、高潮、结局和全部阶段形成完整因果变化。",
  "subject_ids": ["STORY-001", "PHASE-001", "PHASE-002"],
  "control_ids": ["INT-001", "CAU-001"]
}
```

`world` 必须精确覆盖世界构思 ID；`story` 覆盖故事及全部阶段 ID；`characters` 覆盖全部人物职责需求、人物档案与关系边 ID。此门审的是构思是否正面完成且能支撑章节开发，不要求章节、场景或正文。

在总体三域审阅之外，还必须提交以下精确覆盖复核：

- `world_model_reviews`：逐一覆盖八类 `world.facets`、全部 `world.systems`、`world.environments` 与 `world.event_environment_requirements`。逐事件环境需求必须核对环境能力、功能区、资源、权限、信息通道、风险、转场与事件 `environment_ids` 是否一致；世界信息、系统和环境还须证明能够承载这些需求且不会提供便捷解法。
- `major_event_reviews`：逐一覆盖全部 `story.major_events`，核对事件不是抽象功能或章节占位，而是具有可观察发生、前提、发起行动、对抗或复杂化、决定性变化、直接结果、状态变化、下一压力与因果前驱；其故事线、开发单元、规范人物、主要环境和 `event_source_coverage` 来源覆盖 ID 必须与 D1 完全一致，人物须实际承担单元，环境须实际承载事件。R1 必须反向检查事件跨度是否从上游确认的最早因果变化覆盖至最终余波，尤其不能让死亡、失败尝试、批准／接受任务、救援、证词、硬件控制、授权核验只作为后续事件的前提或汇总词存在。
- `storyline_reviews`：逐一覆盖全部 `story.storylines`，确认恰有一条主线，其余 `precursor / subplot / background` 均由真实需求产生。每条线必须具有问题、驱动、升级、因果有序的主要事件序列、终态和处理方式，并引用实际开发单元；
- `storyline_demand_reviews`：逐一覆盖 `story.storyline_demands`，核对全部因果控制点已被扫描、每条实际故事线均有需求依据、独立成线／合并／不适用的处置与遗漏后果一致；
- `storyline_architecture_review`：复核入口线、唯一主干、终点线和覆盖说明是否与全部故事线一致；
- `storyline_connection_reviews`：逐一复核所有连接点。每个连接必须锚定真实主要事件，进入线、离开线、转移义务和结果状态一致；每条非主线必须参与连接并沿连接路径进入主干。
- `melody_line_reviews`：逐一复核全部可选旋律线，并精确回显其锚定事件、因果／结局必需性、POV 权限和决定性信息职责。旋律线只能调制节奏、意象、称谓、感知或主题回响：必须锚定 3–7 个已有主要事件，不得新增 POV、携带决定性信息、成为因果闭合或结局支付的必要条件；删去后主体故事仍须完整。
- `character_demand_reviews`：先于人物档案复核，逐一且无遗漏地覆盖 `characters.demand_register`。核对七类职责是否齐全，触发与遗漏后果是否来自实际故事线和单元，结构性／支持性需求是否解析到完成命名的核心或支持人物，抽象组织或功能标签是否被错误当作处置结果，以及需求与人物 `demand_ids` 是否双向一致。
- `character_profile_reviews`：逐一且无遗漏地覆盖 `characters.profiles`，核对重要度、人物定义完整性、故事线／单元职责、能动选择、人物弧、来源和自主决定。
- `relationship_edge_reviews`：逐一且无遗漏地覆盖 `characters.relationships`，核对两端人物、共同历史、立场、冲突、筹码、信息差、变化、故事线／单元职责、来源和自主决定。
- `relationship_network_reviews`：只覆盖每位核心角色，并由 R1 使用全局人物档案和关系边独立重算人物图。`max_depth` 必须等于实际计算值且不小于 3，`layer_character_ids` 必须精确记录全部连续最短路径层的人物，`profiled_character_ids` 必须精确覆盖可达的全部外延人物定义，`relationship_ids` 必须精确覆盖该连通分量中的全局关系边。第 1 层人物直接连接核心人物，第 2 层通过第 1 层连接，第 3 层通过第 2 层连接，更深层按相同规则继续；层是派生结果，不存在 `layer_ids`。
- 每个网络节点必须是人物，且具有足以支撑开发的角色职责、目标、边界、信息限制、受压行为和能动选择。机构、项目、群体、制度、历史力量或抽象概念不能被计为人物节点；核心与支持人物必须有 `confirmed` 或 `autonomous` 的具体姓名，只有无结构职责的语境性外围人物可以保留功能标签。

上述复核均须说明因果效用、完整性、边界保持与开发可用性；finding 必须包含来自所审对象的故事专属术语，不能用“存在字段”、对象 ID 或批量模板代替语义审阅。

`control_area_reviews` 必须恰好覆盖：

| area | owner_stage |
| --- | --- |
| `intent` | I0 |
| `subject` | I1 |
| `world` | I2 |
| `character` | I3 |
| `causality` | I4 |
| `narrative` | I5 |

每项结构：

```json
{
  "area": "world",
  "owner_stage": "I2",
  "status": "pass",
  "finding": "具体、可反驳的审阅结论",
  "control_ids": ["CTL-003"]
}
```

`control_ids` 必须非空且全部属于该 area。ready 时六项均为 `pass`。

### 4.4 十三项跨域检查

`cross_domain_checks` 必须恰好包含：

- `autonomous_value`
- `gap_closure`
- `promise_scope`
- `world_causality`
- `character_agency`
- `opposition_response`
- `choice_costs`
- `easy_solution`
- `causal_closure`
- `narrative_information`
- `thematic_testing`
- `open_boundaries`
- `development_usability`

每项包含 `status`、不少于 20 字的具体 `finding`、真实 `control_ids` 和 `unit_ids`；两个 ID 数组不能同时为空。此外，每项必须包含至少一条结构化 `assertions`：

```json
{
  "id": "R1-WORLD-CAUSALITY-A01",
  "result": "pass",
  "failure_found": false,
  "test": "对当前 D1 字段执行的具体反证测试",
  "failure_condition": "出现什么现象即判失败",
  "counterexample": "实际尝试过的旁路或反例",
  "conclusion": "为什么当前字段组合没有触发失败",
  "field_evidence": [
    {
      "subject_id": "U01",
      "field": "objective",
      "value_sha256": "当前 D1 字段值的 SHA-256"
    }
  ]
}
```

验证器必须重算字段哈希，确认断言文字与绑定值具有故事特异性重合，并要求七项有明确挑战对象的检查至少绑定一个规定对象。`status: pass`、`result: pass` 与 `failure_found: true` 不得并存；明确写出“相互矛盾、无法支撑、不一致、审查失败”等尚未解决失败的 finding 也不得标为 pass。ready 时十三项全部通过。

### 4.5 自主开发复核

`development_gap_reviews` 必须与 D1 `development_gaps` 一一对应：

```json
{
  "gap_id": "GAP-001",
  "status": "pass",
  "finding": "为什么这是真缺口，且当前解决权限与结果正确",
  "resolution": "autonomous_decision"
}
```

`design_decision_reviews` 必须与 D1 `design_decisions` 一一对应：

```json
{
  "decision_id": "DEC-001",
  "status": "pass",
  "finding": "具体语义结论",
  "gap_ids": ["GAP-001"],
  "source_control_ids": ["CAU-001"],
  "dimensions": {
    "necessity": "pass",
    "compatibility": "pass",
    "causal_utility": "pass",
    "specificity": "pass",
    "author_boundary": "pass",
    "downstream_freedom": "pass"
  }
}
```

R1 必须确认：

- 缺口不解决就会迫使下游临时发明核心逻辑；
- 决定不是控制点同义改写；
- 被选择方案与被拒绝方案都真实可行，比较不是造假；
- 决定至少进入一个功能单元和一个完整构思／信息对象；
- 决定产生因果、对抗、选择、代价、关系、信息或主题上的实质作用；
- 决定没有改写作者锁定项或裁决开放项；
- 章节、场景和正文仍有足够实现空间。

任一维失败时不得把该决定标记 `pass`。

### 4.6 派生复核

`derivation_reviews` 必须与 D1 `derivation_claims` 一一对应：

```json
{
  "derivation_id": "DRV-...",
  "status": "pass",
  "finding": "为何该字段的开发含义没有越过来源控制点",
  "source_control_ids": ["CTL-001"],
  "source_decision_ids": ["DEC-001"]
}
```

两个来源数组必须与 claim 完全一致。哈希匹配只证明值未变；R1 finding 必须表达实际语义判断。

### 4.7 八任务交接

`subject_ids` 必须恰好覆盖全部 D1 单元。`tasks` 必须恰好包含：

- `promise`
- `autonomous_value`
- `causal_chain`
- `unit_contract`
- `freedom_boundary`
- `drift_detection`
- `easy_solution`
- `scene_plan`

每项：

```json
{
  "id": "causal_chain",
  "status": "pass",
  "response": "仅凭 D1 包形成的具体回答",
  "evidence_ids": ["CTL-001", "U01"]
}
```

回答不少于 40 字；证据 ID 只能来自 D1 控制点、完整构思对象、单元、信息义务或派生声明。

### 4.7 开放项

每个 D1 open item 必须恰好一条 `open_item_reviews`：

```json
{
  "open_item_id": "OPEN-001",
  "status": "preserved",
  "finding": "说明开发可如何保持开放，以及不得预先决定什么"
}
```

ready 时全部为 `preserved`。

### 4.8 Findings 与责任

```json
{
  "id": "FND-001",
  "severity": "risk|revise|blocked",
  "owner": "R1|D1|I0|I1|I2|I3|I4|I5|V1|V2|AUTHOR",
  "problem": "具体问题",
  "evidence_ids": ["CTL-001"],
  "required_action": "唯一恢复动作"
}
```

`risk` 可在 ready 包中保留；`revise` 使 verdict 至少为 `revise`；`blocked` 使 verdict 为 `blocked`。D1 漏项归 D1，R1 文档或证据错误归 R1，只有改变已确认控制点才归 I0–I5。

验证器强制 severity 与责任边界：

| severity | 合法 owner | 处理 |
| --- | --- | --- |
| `risk` | findings owner 枚举中的真实责任方 | 保留风险，不触发 return |
| `revise` | `D1` 或 `R1` | 在当前自主阶段局部修复 |
| `blocked` | `I0`–`I5` | 必须生成指向唯一控制点拥有者的 return |

不得用 `revise + I0–I5` 绕过上游 return，也不得用 `blocked + D1/R1/V1/V2/AUTHOR` 制造无效控制点退回。

### 4.9 结构化回退

语义 blocked review 必须把全部 blocked findings 合并到同一个上游拥有者：

```json
{
  "return_request": {
    "finding_ids": ["FND-001"],
    "target_stage": "I4",
    "requested_decision": "由 I4 裁决互相冲突的权威因果顺序",
    "affected_artifacts": ["causal-storyline.md"]
  }
}
```

`finding_ids` 必须恰好覆盖 blocked findings；这些 findings 的 owner 必须为同一 I0–I5 stage，且等于 `target_stage`。验证器确定性生成：

- `return-package.json`：`origin_stage=R1`，包含缺陷、证据、请求裁决和受影响产物；
- `next-run-state.json`：复制当前不可变 run-state，只把 `active_return` 设置为上述 return 的相对路径和哈希。

`affected_artifacts` 必须无重复，并至少包含目标阶段的权威产物：

| target_stage | 必含权威产物 |
| --- | --- |
| `I0` | `intent-card.md` |
| `I1` | `subject-definition.md` |
| `I2` | `world-operating-contract.md` |
| `I3` | `core-character-design.md` |
| `I4` | `causal-storyline.md` |
| `I5` | `narrative-contract.md` |

编排器验证并提升下一 run-state；不得原地改写 R1 输入所绑定的当前 run-state。

## 5. 确定性交付物

### `novel-design-brief.md`

直接从已验证 D1 控制点、单元、信息义务、终点线程和开放项渲染：

1. 权威与交接状态；
2. 故事承诺和范围；
3. 主体与人物；
4. 世界运行边界；
5. 因果开发线；
6. 叙述与信息；
7. 开发自由、禁止项和开放问题。

每个开发单元至少显示职责、因果节点、POV、前置状态、目标、阻力、选择、价值变化、四类信息责任、世界约束、末态、依赖、规模和来源控制点。因果区同时显示权威因果控制点，不能只留下无法解释的 ID。

不允许加入无法追溯的新概括。

### `conception-review.md`

从 `review-data.json` 渲染：

1. 输入与 reviewer；
2. 六区审阅；
3. 十三项跨域检查；
4. 开发缺口与设计决定复核；
5. 派生复核覆盖；
6. 八任务结果；
6. 开放项；
7. findings、责任与候选 verdict。

### `independent-handoff.json`

从 reviewer、缺口复核、设计决定复核、派生复核、subject IDs 和八任务确定性生成，符合主 harness 的 `independent-handoff.schema.json`，并绑定经权威重验的 D1 manifest。

只有权威 verdict 为 ready 时才生成该文件；revise/blocked 不得留下声明 `pass` 的独立交接文件。

## 6. 验证、manifest 与批准

技术 ready 包绑定：

1. `review-data.json`
2. `generation-session.json`
3. 四份 `generation-evidence/*.json`
4. `execution-record.json`
5. `novel-design-brief.md`
6. `conception-review.md`
7. `independent-handoff.json`
8. `validation.json`

R1 先在不同于 D1 的 Codex 任务中建立受控会话，按 `review-plan → semantic-challenges → handoff-test → final-review` 提交阶段并形成哈希链。最终入口不接受任意外部审阅候选。`execution-record.json` 绑定当前 R1 技能、生成会话、review-data、input gate、独立 reviewer、D1-only 证据范围和实际方法。修改任一文件都会使 manifest 和 completion 失效。

作者最终批准必须：

- `approval_scope` 为 `R1`；
- `decision` 为 `approved`；
- `review_brief` 精确绑定 manifest 内当前 `conception-review.md`；
- 保存明确的作者决定记录。

R1 completion 的 `design_artifact` 绑定 manifest，`final_author_approval` 绑定作者决定，`independent_handoff` 绑定 manifest 内同一文件。主 harness 重新运行 R1 权威验证器后才接受 completion。

## 7. 完成标准

R1 技术 `ready` 必须同时满足：

1. V1、V2、D1 和 run-state 通过硬准入；
2. D1 权威重验结果与存储结果完全一致；
3. 六区审阅全部通过；
4. 十三项跨域检查全部通过；
5. 每个开发缺口恰好一次复核且权限分配成立；
6. 每条新增设计决定完成六维复核，证明具有实质增量并遵守作者边界；
7. 每条 D1 派生声明恰好一次语义复核，同时核对控制点与设计决定来源；
8. 全部 D1 单元由独立交接执行覆盖；
9. 八任务回答完整且引用真实 ID；
10. 每个开放项保持开放；
11. 没有 revise 或 blocked finding；
12. 三份渲染产物与模型逐字一致；
13. R1 与 D1 任务 ID 不同，四阶段审阅链完整，正式自主入口和执行记录有效，manifest 完整绑定执行包；
14. finding 具有故事专属性，不含占位语或同模板批量复述；
15. 七项重点语义挑战落到对应 D1 字段，阶段证据 ID 属于会话开始时绑定的允许集合，八项交接回答可区分。

进入开发还必须取得绑定当前审阅报告的作者最终批准，并生成通过主 harness 的 R1 completion。

## 8. Verdict

| Verdict | 含义 | 后续 |
| --- | --- | --- |
| `ready` | 技术审阅和不可变交付包全部通过 | 请求作者最终批准；批准后生成 completion |
| `revise` | 准入有效，但 D1/R1 存在局部可修问题 | 回到责任阶段，修订并重验 |
| `blocked` | 准入失效或必须改变上游决定 | 硬准入失败先恢复输入；语义阻塞生成 return package 和下一 run-state |
