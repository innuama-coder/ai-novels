---
name: novel-interview-integrity-auditor
description: 自主审计六份已完成的小说构思访谈产物是否覆盖方向、主体、世界、人物、因果和叙述控制点，且版本一致、可追溯并可交接作者评审。用于所有访谈完成、生成可视化简报之前；不发起创作访谈、不补设定、不替作者裁决。
---

# 小说访谈完整性审计

## 任务边界

产出 `interview-integrity-report.md` 与同 run、哈希绑定的 `semantic-review.json`，回答：**六份访谈材料是否合起来形成完整、无冲突、可交接的构思控制面？** `semantic-review.json` 必须为意图、主体、世界、人物、因果、叙述六个控制区各列一条证据；只有 verdict `pass` 且没有活动回退包时，才可生成 V1 `ready` completion。 本 skill 是只读审计门，不新增任何世界事实、人物动机、事件或叙述决定。

读取 [integrity-checklist.md](references/integrity-checklist.md) 后执行。

## 输入与准入

必须读取六份当前有效设计产物、各自的 `stage-completion.json`、`validation.json` 和由事件日志重建的报告：

1. `intent-card.md` 与 I0 访谈报告；
2. `subject-definition.md` 与 I1 访谈报告；
3. `world-operating-contract.md` 与 I2 访谈报告；
4. `core-character-design.md` 与 I3 访谈报告；
5. `causal-storyline.md` 与 I4 访谈报告；
6. `narrative-contract.md` 与 I5 访谈报告。

先由 harness 执行 `validate_stage_completion.py` 验证六个 completion packet；任一 verdict 非 `ready`、引用的 `validation.json` 非 `ready` 或存在活动回退包，即输出 `blocked`，不得以审计判断覆盖确定性门。六份设计产物均须为 `ready`。报告用于确认过程、版本和授权；当前设计产物才是结论权威。缺失、过期、无法追溯或相互冲突时，不生成“通过”的简报输入。

## 审计步骤

1. 建立版本图：每个产物的输入版本、输出版本、状态、作者确认/授权来源和未决风险。
2. 按六维覆盖矩阵检查每个控制点是否有唯一拥有者、当前答案和下游消费者。
3. 审计跨文档一致性：故事承诺、主体选择、世界规则、角色能力/知识、因果节点、结局性质与叙述权限不得冲突。
4. 审计访谈过程完整性：读取每个 `validation.json` 的证据字段，核对不可变计划、实际问题数、计划修订授权、逐轮事件和完成判定；报告缺失不能由总结替代。
5. 按唯一拥有者形成问题包，并标记所有因上游修订而失效的下游版本。

## 覆盖与 verdict

| 维度 | 唯一拥有者 | 最低可交接信息 |
| --- | --- | --- |
| 方向 | I0 | 故事承诺、范围、硬边界、作者授权 |
| 主体 | I1 | 核心选择、目标、代价、关系功能、世界需求 |
| 世界 | I2 | 运行规则、限制/代价、权力/资源、信息与压力机制 |
| 人物 | I3 | 选择模型、关系动力、变化边界、能力/知识边界 |
| 因果 | I4 | 触发、转折、危机、高潮选择、结局、支线功能 |
| 叙述 | I5 | POV、读者知识、时间、披露、公平边界、表达禁区 |

- `ready`：六维均有可追溯的当前有效答案；没有结构性冲突；所有访谈报告完整；允许的 `provisional` 项带风险与回看点。
- `revise`：答案已有唯一来源，但版本失效、交接不全、报告缺段或存在可定位的非作者裁决问题。
- `blocked`：缺少会改变主线的作者决定、两份同权威产物冲突，或某个世界/人物/因果前提使故事无法推演。

## 输出与路由

V1 除语义审计外必须生成并校验 `fact-dependency-register.json`。逐一盘点六份当前设计产物中影响结构可行性的外部事实依赖：已有研究包且有明确采用记录的写为 `adopted`；不影响结构、允许后续保持未决的写为非阻塞 `open`；完全不需要外部事实时仍写一条 `not_applicable`。任何尚未解决的结构性事实依赖必须触发回退或 `blocked`，不得伪装为非阻塞项。V1 completion 使用 `contract_version: "2.0"`，哈希绑定该登记表，并只在六份 control projection 与登记表的专用 validator 全部通过后标为 `ready`。

报告必须包含版本图、覆盖矩阵、逐项通过/失败证据、冲突和缺口、唯一回退门、下游重跑范围、verdict 与简报准入结论。不得写“建议增加某设定”而不指明拥有者。

仅 V1 completion packet 为 `ready` 可由 harness 交给 V2 `novel-interview-brief-generator`。`revise` 或 `blocked` 时，协调者只重跑报告指定的最早拥有者和其依赖门；审计员不得自行修订材料。
