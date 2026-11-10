# 小说构思人审报告交付契约

> Legacy 1.x only. 本文记录旧 R1/D1 交付结构，不是 V2 准入依据。
> V2 只使用 P1、H1 workspace、公共 schema 与
> [review-plan-contract.md](review-plan-contract.md)；不得把本文字段适配进
> `run_v2.py`。

## 1. 上游硬准入

R1 包必须同时满足：

- `review-data.json.status == "ready"`；
- `validation.json.verdict == "ready"`，且 `errors`、`blockers` 为空；
- `independent-handoff.json.verdict == "pass"`；
- `package-manifest.json` 中所有列出的文件哈希正确；
- `independent-handoff.json.d1_package` 可解析且哈希正确；
- D1 manifest 中的 `map-data.json` 存在、哈希正确且状态可交付；
- 不要求 `author-approval.json` 或 R1 `stage-completion.json`，因为本报告正是作者批准前的输入。

## 2. `source-inventory.json`

由 `prepare_source_inventory.py` 唯一生成，至少包含：

```json
{
  "schema_version": "1.0",
  "skill": "novel-conception-human-review-assembler",
  "run_id": "RUN-ID",
  "status": "ready",
  "source_package": {
    "r1_directory": "...",
    "r1_manifest_sha256": "...",
    "review_data_sha256": "...",
    "d1_manifest_path": "...",
    "d1_manifest_sha256": "...",
    "map_data_path": "...",
    "map_data_sha256": "..."
  },
  "known_source_ids": [],
  "fragment_eligible_source_ids": [],
  "source_id_groups": {},
  "review_subjects": [
    {
      "source_id": "ID",
      "domain": "world|story|characters|units|open_items",
      "path": "conception.world.systems[0]",
      "label": "..."
    }
  ]
}
```

`review_subjects` 是覆盖账本的全集。不得手工删除对象来让报告通过。
`fragment_eligible_source_ids` 只包含构思对象、开发单元、控制点、设计决定、
信息义务和终端线索；片段不得用低层派生声明 ID 冒充正文依据。
`source_id_groups` 还明确列出世界系统、主要环境、故事阶段、故事线、核心人物
和关系层，验证器据此阻止把某类对象映射到一个不承担其语义的泛化段落。

## 3. `review-plan.json`

顶层：

```json
{
  "schema_version": "1.0",
  "skill": "novel-conception-human-review-assembler",
  "run_id": "RUN-ID",
  "status": "ready",
  "source_inventory_sha256": "...",
  "review_contract": {},
  "reading_budget": {},
  "report_blueprint": {},
  "coverage_ledger": [],
  "review_tasks": []
}
```

### 3.1 `review_contract`

必须包含：

- `work_title`：作品正式工作标题，不得用梗概、run id 或目录名代替；
- `audience`：作者/构思决策人；
- `decision`：判断是否进入小说开发；
- `target_minutes: 10`；
- `main_sections: ["world", "story", "characters", "fragments"]`；
- `out_of_scope`：至少声明不代替机器开发包、不产生最终小说正文、不产生 HTML、不批准自身。

### 3.2 `reading_budget`

必须包含：

- `profile.id == "review-reading-baseline-v1"`；
- `profile.cjk_chars_per_minute == 400`；
- `profile.latin_words_per_minute == 200`；
- `navigation_minutes`；
- `sections`：`orientation/world/story/characters/fragments/decision` 六项及各自 `minutes`；
- 六项分钟数与导航预留之和精确等于 10。

### 3.3 `report_blueprint`

#### `orientation`

- `story_identity`
- `this_is`
- `this_is_not`
- `review_instruction`
- `logic_spine[]`：固定按
  `worldview → world_rules → event_space → story_architecture →
  character_agency → terminal_contract` 六层排列；每层必须给出
  `claim/therefore/controls/must_hold/boundary/source_ids`。

所有内容元素都必须有唯一的 `HR-*` ID、可见文本和 `source_ids`。

#### `world`

- `definition`
- `systems[]`：名称、定义、规则、权限、资源、代价或失败方式、控制对象、
  禁止解释和人审可见的 `control_summary`；
- `environments[]`：特征、基本要素、进入条件／危险、允许动作、禁止捷径、
  承载的主要事件、控制对象、必须成立项、故事功能、状态变化和
  `control_summary`；
- `boundaries[]`
- `open_interfaces[]`
- `visual_model`：`type == "world-system-map"`，含节点与边；
- `review_question`

系统和环境不得被合并成无法判断其运行方式的一句话。
`control_summary` 至少表达一个关系、转移或边界，不得只是名词标签。

#### `story`

- `definition`：承诺、戏剧问题、起点、终点、赌注；
- `lines[]`：至少一条 `main`，并保留 D1 已定义的 `subplot/background`；每条必须
  提供 `name/kind/function/start/objective/driver/intersections/
  connection_points/end/exit_condition/must_hold/optional_scope/
  control_summary/source_ids`，与 HTML
  消费契约完全一致；
- `timeline[]`：3–8 个阶段，每项有压力、选择、后果、代价、新状态、`unit_ids` 和 `line_ids`；
- `event_controls[]`：逐一覆盖 D1 的全部 `major_events`；每项明确事件职责、
  “前提 → 决定性变化 → 结果”、它控制的后续事实，以及所属故事线、环境和参与人物；
- `narrative_constraints[]`
- `open_interfaces[]`
- `visual_model.type == "multi-line-timeline"`
- `review_question`

全部 D1 unit 必须映射到时间线阶段；不得以一句主题总结代替事件因果。
主要事件不得仅作为 `source_ids` 藏在阶段中。

#### `characters`

- `definition`
- `profiles[]`：覆盖 D1 已定义的全部具名人物档案，含职责对象、权限、不可委托
  选择、目标、需要、恐惧、价值边界、信息限制、受压行为、自主选择、弧线、
  终态、控制对象、禁止解释、不可改写项和 `control_summary`；
- `relationship_layers[]`：覆盖 D1 已定义的关系，并围绕每个核心人物至少形成三个不同层级；每项含关系职责、初态、压力、变化和终态。 supporting 人物不要求机械复制三层，但必须能沿关系图追溯到核心人物、行动链或背景压力；
- 每段关系还必须明确触发条件、控制对象、必须成立项和 `control_summary`；
- `visual_model.type == "layered-relationship-map"`
- `review_question`

#### `fragments`

- `slots[]`：2–4 项，默认 3 项；
- 每项必须定义评审问题、定位的 D1 unit、POV、前后状态、必含事实、禁写事实、必引来源、允许来源、叙述约束、创作自由和最大长度；
- 所有 slot 合计覆盖：
  `world_in_action`、`story_causality`、`character_agency`、
  `relationship_change`、`narrative_contract`、`ending_nature`；
- 明示“评审样本，不是最终定稿或新设定权威”。

长度预算只统计最终报告会展示的片段标题、用途、评审问题、覆盖标签和片段正文上限；
必含事实、禁写事实、来源、前后状态等下游写作契约必须保持完整，但不计入作者阅读时长。
长度预算必须同时考虑实际需要出现的文字系统：中文片段若必含英文姓名、编号、
机构缩写或技术术语，`max_latin_words` 不得为零；英文片段同理应为必要的 CJK
专名预留 `max_cjk_chars`。预算不能让 required facts 在形式上不可写。

十分钟预算按页面默认可见内容计费：六层控制总链、各对象
`control_summary`、全部主要事件控制、边界、开放接口、评审问题和片段正文。
支持性的运行参数可以置于页面可展开的追溯层，但不得用折叠来隐藏决定性控制信息。

#### `decision`

- `questions` 精确覆盖 `world/story/characters/fragments`；
- `options == ["approve", "revise"]`；
- 显示未决开放项；
- 不得预填批准结论。

### 3.4 `coverage_ledger`

每个 `review_subjects.source_id` 必须恰有一项，且：

```json
{
  "source_id": "ID",
  "domain": "world",
  "visible_element_ids": ["HR-W-01"],
  "role": "它为何影响作者判断"
}
```

`visible_element_ids` 必须指向报告蓝图中真实存在的元素，且至少一个目标元素的
`source_ids` 必须实际包含当前 `source_id`。关键对象不得只标记为附录。

### 3.5 `review_tasks`

必须恰好包含：

- `story_identity`
- `world_logic`
- `story_causality`
- `thread_structure`
- `character_agency`
- `relationship_logic`
- `narrative_experience`
- `ending_and_open_interfaces`

每项包含人类问题、`visible_element_ids` 和 `source_ids`。

## 4. `fragment-briefs.json`

由 `export_fragment_briefs.py` 从 `review-plan.json` 确定性导出。片段技能必须交付
完整 canonical package，包括 generation session、三阶段 evidence、
`fragment-package.json`、`fragments.md`、`execution-record.json`、
`package-manifest.json` 与 `validation.json`。

其中 `fragment-package.json` 顶层绑定 `review_plan_sha256`，每个片段至少包含：

```json
{
  "id": "HR-FRAG-01",
  "title": "...",
  "text": "...",
  "source_ids": [],
  "control_ids": [],
  "unit_ids": [],
  "creative_choices": [],
  "introduced_authoritative_facts": [],
  "contract_checks": {
    "source_grounding": true,
    "narrative_contract": true,
    "no_new_authority": true,
    "review_question_fit": true
  },
  "brief_compliance": {}
}
```

`introduced_authoritative_facts` 必须为空。

片段 `execution-record.json` 必须声明
`skill == "novel-conception-fragment-writer"`、`mode == "autonomous_agent"`、
执行者/任务 ID，并哈希绑定当前 review plan 与 `fragment-package.json`。
组装阶段必须直接运行 `novel-conception-fragment-writer` 的
`validate_fragments.py`。三阶段 evidence、session、manifest、当前技能文件绑定和
最终片段派生关系必须全部通过；仅有同名文件或自声明 `ready` 不构成有效交接。

## 5. 组装交付

`assemble_human_review.py` 写出：

- `human-review-report.json`
- `human-review-report.md`
- `assembly-execution.json`
- `validation.json`
- `package-manifest.json`

`human-review-report.json` 保留计划中的所有定义、图形语义、覆盖账本和理解任务，只把已验收片段注入对应 slot。组装阶段不得进行生成式改写。

该文件是 `novel-conception-review-html-generator` 的唯一权威内容输入。HTML
技能仍须同时接收当前 plan、fragment 与 R1 包，重新验证完整来源链后才可呈现。

## 6. 验收结论

- `ready`：上游、内容结构、覆盖、预算、片段和哈希全部通过；
- `blocked`：任一硬准入、来源绑定、覆盖、预算或片段契约失败。

本技能不使用 `revise` 掩盖硬失败。需要内容修改时，修改 plan 或返回片段技能后重新完整验证。
