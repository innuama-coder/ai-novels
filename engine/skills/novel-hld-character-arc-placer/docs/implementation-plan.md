# HC1 implementation plan and realized design

## 1. Authority 与坐标准入（已实现）

技能契约冻结 HC1 owner、`[HB0,HA1,HS1]` 拓扑、allowlist、HDD 和 current completion roles。所有 person/relationship/motivation/capability/permission/knowledge/event/outcome 必须回到 HB0-indexed authority；HA1/HS1 只提供 placement 坐标和 network，不提供新人物事实。

## 2. Agent 语义执行（已实现为 instructions/evidence）

Agent 先冻结人物/关系权威，再遍历 storyline participation 和 key results，比较合法 placement 方案。Canonical 投影将 character participation、state model、arc steps、bilateral relation、choice-cost-consequence、event actor 和 capability-information-permission 分开表达。Adversarial review 主动攻击 jump、author invention、plot compulsion、unsupported action、one-sided relation 与 unowned result。

五份 generation evidence 把 dependency、obligation、option、projection、自我反证分层，防止 Agent 只生成字段完整的人物弧。

## 3. 确定性 runtime（已实现）

公共 gate/draft/package runtime 检查身份、topology、reads、HDD、IDs、authority/ownership、forbidden fields 和信封。HC1 分支从 participation register 取得 core set，要求 state model 覆盖；从 arc steps 聚合角色 role，要求 start/pressure/choice/cost/result 全集；要求每 step 的 pressure、choice、cost、consequence、unit、event、storyline segment 非空；要求 relationship step 恰好两个 character 且 before/after state 均存在。

合法 candidate → exact ready；candidate/边界缺陷 → revise/local_candidate；`required_now` → blocked/author_required。Runtime 不判断心理可信度、不新增 authority、不决定 route/run-state。

## 4. 验收实现（已完成）

P01 使用一个 core character 的五角色完整 path、bilateral relation 和 feasibility checks；N01 注入 `new_relationship`；B01 注入 `appearance`。Fixtures 预密封且 hash 校验。六维 evidence 区分脚本检查与 agency/relationship 的语义依据。

## 5. 后续边界

知识持有者、POV 和 reveal 由 HI1；节奏由 HR1；关键场景功能由 HK1；LLD 才能展开具体行动/对白。若 conception 缺人物定义，应 blocked/return，不得扩充 HC1 schema 或放松 forbidden keys 让 Agent自行补齐。
