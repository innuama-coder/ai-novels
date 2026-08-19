# HC1 design brief

## 要解决的问题

HC1 把已由构思权威定义的人物目标、信念、责任、关系、压力、选择、代价和后果放进 HA1/HS1 的单元、线路段和事件中。它建立的不是人物小传，而是“谁在何种压力下作出什么选择、付出什么代价、产生什么后果”的可追溯状态路径，使 HI1 后续可以安排知识/权限而不补造动机。

## thinking skill 的 Agent 工作

Agent 先对所有 `HDD-HC1-*` 投影作处分；`required_now` 在候选前阻断。然后冻结每个 core/important character 与 relationship 的权威目标、belief/value、responsibility、feeling、capability、permission、knowledge、start/end control 和 open items。authority 未提供的外貌、背景、社交、关系、能力或情感只能标记 out of scope。

Agent 遍历 HS1 segments/connections，为 relevant character 记录授权职责或具体合法缺席；为 key result 找到责任 actor。比较至少两个合法 placement 后，投影 participation register、arc state model、start/pressure/choice/cost/result steps、bilateral relationship steps、choice-cost-result links、event alignment 和 capability/information/permission checks。语义验收必须证明压力促成选择、代价使选择有意义、后果改变后续状态；flat/steadfast arc 可以合法，但仍需 pressure/choice/cost/effect。

## 确定性 runtime 的责任

`scripts/run_skill.py` 验证 gate、`[HB0,HA1,HS1]` 拓扑、allowlist/HDD/evidence、HAS/HRS IDs、authority/ownership 和 exact package。HC1 专属检查确保 core character 有 state model；每个 core arc 覆盖 start/pressure/choice/cost/result role；每个 step 有 pressure/choice/cost/consequence/unit/event/storyline segment；relationship step 恰含两人且有 before/after state。Forbidden walker 拒绝 appearance/new_backstory/new_relationship 等。

Runtime 不能判断心理变化是否可信、选择是否真正有能动性、代价是否具有情感重量，亦不能只凭字段存在给 semantic pass；这些属于 Agent adversarial evidence 与 HQ1。

## 边界与完成

HC1 不新增人物、外貌、传记、社交圈、关系、情绪、能力、信息或场景正文。P01 必须形成 HI1 可消费的授权 arc network；N01 的 unauthorized relationship 必须 non-ready 且不修；B01 的 profile detail overreach 必须被拒绝。三个 case 六维均 2/2 才达到当前实现标准。
