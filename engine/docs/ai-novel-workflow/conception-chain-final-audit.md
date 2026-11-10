# 小说构思技能链最终审计

审计日期：2026-08-05  
审计范围：访谈、构思、呈现、作者决定与开发准入  
结论：**ready**。当前链可从已确认 idea 开始，交付完整机器构思、人审报告、样章与
最终开发准入；旧 D1/R1 不再是合法生产路径。

## 1. 三段技能链

| 段 | 固定顺序 | 目标 | 终点 |
|---|---|---|---|
| 访谈 | I0 意图 → I1 主体 → I2 世界 → I3 角色 → I4 因果 → I5 叙事 → V1 完整性审计 → V2 访谈简报与作者批准 | 把 idea 转成作者确认、版本化、可追溯的六类创作控制；访谈前声明精确问题数与预计时长，逐轮记录，结束生成完整报告 | 当前 V2 HTML 获作者批准，hash-bound approval 可进入 B0 |
| 自主构思 | B0 → S1 故事线 → W1 世界 → E1 环境 → T1 事件 → C1 角色 → Q1 独立审查 → P1 完整机器包 | 先定义多线故事架构，再按故事需求展开世界、环境、事件和人物；独立检查完整性、一致性、因果与开发可用性；无损封包 | 当前 P1 package ready |
| 人类呈现 | H1-A plan → H1-B 样章 → 独立呈现忠实度审查 → H1-A assemble → H1-C HTML → formal H1 → 作者决定 | 在十分钟内以世界、故事线、角色、样章四维呈现同一 P1，样章只作非权威体验证据 | H1 ready；approved 后生成 final completion |

`novel-conception-presentation-fidelity-reviewer` 是 H1-A 消费的受控质量依赖，
不是新的构思阶段，也不拥有内容修改权。

## 2. 职责与边界检查

- I0–I5 各自只拥有一类作者控制；事件顺序归 I4，读者披露归 I5，世界运行规则归
  I2，人物解释与压力选择归 I3。V1 只审计，V2 只呈现。
- S1 只定义故事线架构及下游需求；W1 定义虚拟世界；E1 定义可承载活动的具体环境；
  T1 定义事件时间线；C1 最后解析人物槽并完成个体与关系；任何阶段不得反向改写 S1。
- Q1 只审查与路由，不修稿；P1 只无损组装，不创作；H1-B 只实例化样章；H1-C 只
  渲染；调度者只管状态、work order、lineage 和 return，不生成领域内容。
- 作者始终拥有价值选择、开放项裁决和最终批准。Agent 不得合成作者决定。

本轮修复了两处真实契约漂移：访谈 manifest/agent/V2 skill 仍把 D1/R1 写作终点；
H1 过去只能证明来源覆盖和确定性渲染，不能证明自然语言压缩没有改变构思含义。

## 3. P1 与人审报告一致性

一致性采用三层证明，缺一不可：

1. **字节与身份层**：同一 run、session、P1 completion、plan、fragments、assembly、
   HTML manifest 以 SHA-256 闭合；所有 package 重新验证完整 inventory。
2. **结构与范围层**：H1-A 的 presentation bindings、reduction ledger、drilldown index
   和 source coverage 精确覆盖 plan；H1-C 是 report JSON 的确定性投影。
3. **实质语义层**：独立 reviewer 逐一读取每个公开模块、图形、样章和决定提示，核对
   P1 anchors，分别判定无关键遗漏、无矛盾、无强调失真、无权威升级。普通内容只能
   `faithful`，样章只能 `non_authoritative_sample`。

第三层不能由 schema“理解”小说意义，因此职责明确交给独立语义审查技能；运行时只
负责验证它确实独立于规划/样章任务、逐元素完整、绑定当前内容 hash、证据引文存在且
五维 verdict 全部通过。把语义判断伪装成字符串规则会制造假安全，当前契约没有这样做。

## 4. 最终交付物

最终交付定义以
[final-delivery-contract.md](../../harnesses/novel-conception-autonomous/docs/final-delivery-contract.md)
为唯一规范，分为：

1. **完整机器构思包 P1**：canonical package、spec、权威原文/模型、cross-model
   index、traceability、open items、authority partition、development handoff、正式
   manifest/validation/completion。
2. **人审构思包 H1**：report JSON/Markdown、离线 HTML、样章包、H1 plan、独立
   `presentation-fidelity-review.json`、render record、formal H1 completion。
3. **完成与准入凭证**：外部 `author-decision.json`、最新 production state、
   `completion/conception-completion.json`。只有 approved 分支产生开发准入。
4. **强制来源证据**：I0–I5 的计划、逐轮 events、完整 report、设计产物和 completion，
   V1/V2 审计、简报与批准。它们是可回溯证据，不与 P1 并列成为第二套构思事实。

## 5. 硬验收结果

- Interview harness structural validator：通过。
- Interview positive/negative/boundary evals：23 项通过；D1/R1 输入明确拒绝。
- H1-A plan/assembly：45 项通过，含缺失忠实度审查、生成者自审、内容 hash 漂移、
  元素漏审等负例。
- H1-B fragment：34 项通过，含真实 H1-A→H1-B→H1-A 集成。
- H1-C HTML：14 项通过，含真实全链、SVG/文本等价、追溯、安全、打印和无障碍。
- Formal H1/author/final harness integration：24 项通过，含 approved/revise/rejected、
  orphan recovery、tamper、错误状态与旧路径负例。
- Dependency/release：4 项通过；十个阶段 owner 加一个呈现忠实度质量依赖均被锁定。
- Autonomous harness 全量包模式回归：130 项通过，覆盖 B0、schema、coordinator、
  migration、production orchestrator、H1、作者决定、final completion 与 release。
- 两个被修改/新增的 skill 均通过 `skill-creator` quick validation。

## 6. 最终判定

当前技能链的目标、职责、边界、输入、输出和调用顺序已经一致。它可以稳定拒绝缺失、
串线、旧版本、越权、篡改和呈现实质漂移；通过时同时交付机器本体、人审入口、样章、
作者决定与开发准入。内容质量仍由各领域 Agent 和独立语义 reviewer 作出专业判断，
但这些判断现在必须留下完整、当前、可追溯且可被下游硬门消费的证据。
