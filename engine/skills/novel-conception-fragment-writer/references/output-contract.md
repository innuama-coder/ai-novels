# 小说构思评审片段交付契约

## 1. 输入

- 已通过 plan 验证的 `novel-conception-human-review-assembler` package；
- 该 plan 所绑定的技术 `ready` R1 package；
- `fragment-briefs.json`、`review-plan.json`、`source-inventory.json`；
- 当前技能文件与本次自主任务身份。

`fragment-briefs.json.review_plan_sha256` 必须与当前 plan 一致，slots 必须与 plan
完全相同。

## 2. 固定 style contract

所有阶段和最终包必须包含完全相同的：

```json
{
  "id": "restrained-concrete-scene-v1",
  "purpose": "conception_review_sample",
  "name": "克制具象的场景驱动现代白描",
  "fixed_principles": [
    "single_limited_pov",
    "continuous_scene_now",
    "concrete_selective_detail",
    "pressure_choice_consequence",
    "subtextual_interaction",
    "restrained_emotion",
    "earned_state_change"
  ],
  "adaptive_axes": [
    "pov_person",
    "genre_lexicon",
    "character_diction",
    "emotional_temperature",
    "sentence_rhythm",
    "sensory_channels"
  ],
  "prohibitions": [
    "outline_or_screenplay",
    "author_explanation",
    "author_imitation",
    "pov_or_information_breach",
    "exposition_instead_of_choice",
    "unearned_state_change",
    "new_authoritative_fact",
    "final_prose_claim"
  ]
}
```

不得由调用方覆盖。

## 3. 三阶段证据

### `01-scene-contracts.json`

每个 slot 恰有一项：

```json
{
  "id": "HR-FRAG-01",
  "style_contract_id": "restrained-concrete-scene-v1",
  "pov": "...",
  "start_value": "...",
  "end_value": "...",
  "immediate_intention": "...",
  "active_pressure": "...",
  "obstacle": "...",
  "turning_choice": "...",
  "direct_consequence": "...",
  "world_rule_in_action": "...",
  "relationship_change": "...",
  "information_limit": "...",
  "allowed_sensory_channels": [],
  "forbidden_sensory_channels": [],
  "creative_choices": [],
  "source_ids": [],
  "control_ids": [],
  "unit_ids": []
}
```

来源、控制点和 unit 必须在 slot 允许范围内；`creative_choices` 只能来自
`allowed_creative_freedom` 的局部实现。

### `02-drafts.json`

每项包含 `id`、`title`、`text`、来源 IDs、creative choices 和空的
`introduced_authoritative_facts`。文本必须是纯小说正文。

### `03-revision-audit.json`

每项包含：

- `draft_sha256`；
- `final_text`；
- 与 draft 一致或更窄的来源/控制/unit；
- `revisions[]`；
- 空的 `introduced_authoritative_facts`；
- 四个 `contract_checks`；
- `scene_audit`；
- `brief_compliance`。

`scene_audit` 必有：

- `orientation`
- `pressure_or_goal`
- `turning_choice`
- `consequence_or_state_change`
- `pov_and_information`

并根据 slot target 增加：

| target | audit key |
| --- | --- |
| `world_in_action` | `world_in_action` |
| `story_causality` | `causal_progression` |
| `character_agency` | `character_agency` |
| `relationship_change` | `relationship_change` |
| `narrative_contract` | `narrative_contract` |
| `ending_nature` | `ending_nature` |

每项审计包含 `finding` 和 4–80 字的 `evidence_quote`，且引文必须逐字存在于
`final_text`。

`brief_compliance` 必须包含：

- `final_text_sha256`：绑定当前最终文本；
- `before_state/after_state`：`value` 与 brief 完全一致，并各有正文引文；
- `required_facts[]`：与 brief 顺序完全一致，每项有 finding 与正文引文；
- `prohibited_facts[]`：与 brief 顺序完全一致，每项 verdict 为 `absent` 并说明
  检查理由；禁写事实的规范化原文不得出现在最终文本。

## 4. 最终 `fragment-package.json`

```json
{
  "schema_version": "1.0",
  "skill": "novel-conception-fragment-writer",
  "run_id": "RUN-ID",
  "status": "ready",
  "review_plan_sha256": "...",
  "style_contract": {},
  "fragments": []
}
```

每个 fragment 保留 assembler 已约定的字段：

- `id`
- `title`
- `text`
- `source_ids`
- `control_ids`
- `unit_ids`
- `creative_choices`
- `introduced_authoritative_facts`
- `contract_checks`

必须同时保留 `scene_audit`、`brief_compliance` 和 `style_metrics`，不得删除约定字段。

## 5. 文本硬验收

- 片段数量和 ID 与 slots 完全一致；
- 主要语言长度不超过 slot 上限，且达到该上限的 45% 或最小有效长度；
- 至少两个自然段、至少四个句末单位；
- 最大自然段不得超过全文可见字符的 75%；
- 不含 Markdown 标题、代码围栏、镜头/场次标签或评审说明；
- 感叹号不超过 2 个，连续省略号不超过 3 处；
- 不含契约列出的机械套语；
- required sources 全部引用，引用不得超出 allowed sources；
- 场景契约的 start/end 必须分别等于 brief 的 before/after；
- `brief_compliance` 必须逐项覆盖 brief 的必含事实、禁写事实和前后状态；
- unit 与 brief 完全一致，control 不得越界；
- 新增权威事实为空；
- 所有 contract checks 为 `true`；
- 所有审计引文真实存在。

计量规则用于稳定评审基准，不声称是所有小说的最终文体标准。

## 6. provenance

`execution-record.json` 必须：

- 声明 `autonomous_agent`；
- 绑定当前 task/executor；
- 哈希绑定当前 skill 文件、plan、briefs、source inventory；
- 哈希绑定三阶段 evidence 和最终 fragment package。

`validation.json` 必须绑定 plan、fragment package 和 execution record，以便
`novel-conception-human-review-assembler` 拒绝伪造或过期片段。

## 7. verdict

- `ready`：上游、三阶段、固定文风、来源、语义证据、文本指标和 provenance 全部通过。
- `blocked`：任一硬条件失败。

本技能不使用 `revise` 掩盖不合格片段；修改后必须重跑完整验证。
