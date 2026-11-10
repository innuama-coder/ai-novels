# HLD 技能定义深度 Review V1

> Review 对象：
>
> - `hld-autonomous-workflow-v1-design.md`
> - `hld-skill-contract-catalog-v1.md`
>
> Review 边界：只检查技能和 harness 的纸面定义，不检查尚未编写的代码、Schema、测试、adapter 或《断线》HLD 成果，也不在本次 review 中修改定义。

## 1. 总体结论

**判定：方向正确、职责划分基本成立，但当前仍是 `usable with gaps`，不能认定为“严丝合缝”或直接进入实现。**

不需要推倒重来。六个核心设计技能的顺序和边界是合理的：先建立唯一叙事坐标系，再编排故事线、落位人物弧线、安排 POV 与信息、校验时空节奏，最后综合关键场景功能。HB0、HP1、HH1 和 HF1 也基本遵守“准入不创作、组装不创作、呈现不改写、封闭不代签”的边界。

真正阻止当前定义成为生产契约的是 4 个高优先级缺口和 4 个中优先级缺口。前三个高优先级问题会直接造成流程在真实执行中无法闭合；第四个会使 Agent 能够交付结构完整但内容空泛的 HLD。

## 2. 高优先级 Findings

### H1. 中途 `must_ask` 没有完整的作者问答事务

**问题**

设计允许某个 HLD 决定把开放问题判定为 `required_now`，并要求阻塞当前 stage、等待作者外部事件。但现有契约只完整定义了最终 `approved / revise / rejected` 的 `author-decision.json`。没有定义中途问答所需的：

- `author-question.json`；
- `author-answer-event.json`；
- 问题、受影响决定和 stage 的绑定；
- `waiting_author_answer` 状态；
- 答案是只授权本次 HLD，还是要回写构思权威；
- answer 被消费后的 return resolution；
- 答案变化时哪些 completion 失效。

**证据**

- 主设计规定 `required_now` 要“生成作者问题并阻塞受影响 stage”，但只在最终阶段定义作者决定。
- HA1 准入要求所有结构性 must-ask 有 `decision_dependency`，catalog 却没有对应问答 artifact role、Schema 摘要或状态转换。

**影响**

真实执行遇到必须回答的问题时，只能停住、借用聊天继续，或错误使用最终 author decision；三种结果都会破坏硬契约。

**根因**

把“最终作品批准”和“开发过程中的作者裁决”视为同一种 author gate，但两者的作用域、状态和失效范围不同。

**修正方向（本次不执行）**

增加独立的 author-question transaction：问题包、外部回答事件、作用域、owner、状态、resume stage 和失效规则。明确哪些回答属于 HLD 局部授权，哪些必须退出 HLD、回到构思权威链重新批准。

### H2. HQ1-B 没有验收最终交给 LLD 的实际 handoff

**问题**

HQ1-B 在 HP1 之前运行，只读取 HB0 与 HA1–HK1 canonical 模型。它可以证明“这些设计模型大体可被未来 LLD 理解”，但不能证明 HP1 后来生成的 `lld-handoff.json` 真的完整、没有遗漏、没有错误归类，也不能证明一个 LLD 调用者只拿最终 handoff 就能启动。

HP1 之后只有确定性结构验证和 HF1 重验，没有独立语义消费者对实际 `lld-handoff.json` 做 acceptance。

**证据**

- HQ1-B upstream 固定为 `[HB0,HA1,HS1,HC1,HI1,HR1,HK1]`。
- `lld-handoff.json` 直到 HP1 才产生。
- HF1 只“重验” handoff，没有定义意义层消费测试。

**影响**

HLD 模型可能合格，但最终 handoff 因投影遗漏、错误分组或约束丢失而不合格；当前链仍会批准并进入 LLD。这直接违反 `hld-to-lld-handoff-and-acceptance`。

**根因**

把“上游模型可消费性”和“最终交付文件可消费性”合并成了一次发生在组装前的盲测。

**修正方向（本次不执行）**

保留当前 HQ1-B 作为“设计模型可消费性”测试，同时在 HP1 后增加只读取正式 `lld-handoff.json` 和其绑定 HLD package 的独立 handoff acceptance；或者把 HQ1-B 移到 HP1 后并重新设计其隔离范围。最终 HF1 必须消费这份 post-assembly pass 证据。

### H3. `revise / blocked` 有文件形状，但没有完整的 parent-consumption 语义

**问题**

公共契约定义了 revise 和 blocked 包，却没有明确 harness 收到它们后如何：

- 消费 work order；
- 持久化失败结果；
- 计算 owner；
- 生成 active return；
- 推进到哪一种 run-state；
- 区分当前 owner 自修、上游返工和作者问题；
- 在无 manifest、无 completion 的 blocked 包上建立不可篡改引用；
- 处理 revise 候选和新一轮候选之间的 lineage。

Finalizer 的 revise 分支有 return，但 HA1–HK1 和 HQ1 的常规 revise/blocked 没有同等明确的事务。

**证据**

- Catalog 只规定 revise 可保存候选但无 completion，blocked 只允许三个文件且无 manifest。
- 公共 artifact reference 又默认需要 manifest 和 completion。
- 主设计有 active return 规则，但没有把 stage result、router input 和 run-state successor 严格连接起来。

**影响**

Happy path 是清楚的，任何失败路径却可能依赖调度者临时解释。这样无法保证一次真实返工后仍然是同一个可追溯 run，也无法证明下游旧 completion 已正确失效。

**根因**

阶段内容包、工作单结果和 harness 状态事务三个概念尚未完全分开。

**修正方向（本次不执行）**

定义统一 `stage-result.json` 或 work-order receipt，覆盖 ready/revise/blocked 三分支；规定 router 的唯一输入、失败证据绑定、return 产生、state successor 和 revision lineage。Blocked 可以没有 stage completion，但必须有被状态链强绑定的失败 manifest 或等价不可变 receipt。

### H4. 六个 thinking skill 有“要填什么”，但缺少“怎样作出合格判断”

**问题**

HA1–HK1 已经有明确目标、输入字段、输出字段和边界，这是好的。但每个技能仍主要是一份职责清单和字段清单，缺少 thinking skill 必须具备的执行性推理框架：

- 分析步骤和先后顺序；
- 方案生成与比较方法；
- 选择标准；
- 好／坏结果的故事专属锚点；
- 典型失败反例；
- 自检问题；
- revise 与 fail 的具体分界。

公共规则要求非平凡决定提出两个候选，但没有规定怎样证明候选真实、怎样比较，也没有防止 Agent 先写答案再伪造两个候选。

**影响**

实现后很可能稳定地产出 Schema 合格、字段齐全、语言流畅，但逻辑浅、结构机械的 HLD。HQ1 自身也缺少足够锚定的 rubric，未必能稳定拦住这种“合规填表”。

**根因**

当前定义重点解决了 artifact contract，却尚未完成 thinking contract。

**修正方向（本次不执行）**

为 HA1–HK1 分别补充 SOP、决策框架、至少一个正例和两个边界／反例、故事专属证据要求、pass/revise/fail anchors 和 agentic eval。不要把这些内容塞进顶层 harness；它们应成为各 bounded skill 的方法论和评估契约。

## 3. 中优先级 Findings

### M1. HP1 被定义为纯 script，但 LWK 投影规则不够确定

**问题**

HP1 要“从 HK1 和全部上游约束投影 LLD 工作单”，但没有冻结：

- 一个 HKF 是否严格对应一个 LWK；
- 何时允许多个 HKF 合并为一个 LWK；
- 一个跨章节 HKF 如何处理；
- 冲突约束的优先级；
- required elaboration 与 LLD freedom 的确定性来源字段。

如果这些需要 HP1 判断，HP1 就不是 script；如果它必须是 script，映射算法必须在上游或契约中冻结。

**影响**

不同运行可能在工作单数量、边界和自由度上出现语义差异，却仍声称确定性。

**建议方向**

冻结一对一投影，或让 HK1 直接生成带稳定 ID 的 `lld_work_requirements[]`，HP1 只封装；如确需分组判断，则增加明确的 thinking owner，不能藏在 assembler。

### M2. 输出契约停留在顶层字段名，关键嵌套对象仍可被多种方式解释

**问题**

Catalog 已列出 canonical 文件和顶层数组，但大部分数组元素仍未定义：

- 必需字段、类型和枚举；
- 最小／最大基数；
- ID 唯一性；
- 允许引用集合；
- 跨字段不变量；
- 集合相等还是最小覆盖；
- 哪些缺失是 revise，哪些是 blocker。

HKF 的元素定义相对完整，但 HA1–HR1、HQ1 findings、HH1 visible element 等仍主要是自然语言契约。

**影响**

两个实现者可以产出结构不同但都声称符合定义的 Schema；下游“精确字段匹配”无法真正落地。

**边界说明**

没有实际 Schema 文件不是本次 finding——技能尚未实现是既定事实。Finding 是定义尚未明确到足以唯一实现 Schema 的程度。

**建议方向**

在开发前补充对象级 contract table 和跨模型 invariants，再据此实现 Schema；不要先写 Schema 再反向解释字段含义。

### M3. “真实性”检查没有现实事实依赖的退出与重入规则

**问题**

HQ1-A 被要求检查真实性，所有设计技能又禁止新增世界事实。这一边界本身正确。但如果 HLD 的结构决定暴露出构思阶段未登记的现实事实依赖，例如时间、技术能力、机构权限或空间迁移可行性，当前定义没有说明：

- 如何登记事实依赖；
- 谁判断它是结构性还是非结构性；
- 是否允许研究；
- 应返回 preparation、构思事实研究 owner，还是作者门；
- 新事实获批后从哪个 HLD stage 重启。

**影响**

Reviewer 只能在“凭常识判真”和“笼统 blocked”之间选择，无法形成可恢复的真实性闭环。

**建议方向**

复用构思链已经形成的 fact-dependency 规则：HLD 不自行研究；新结构性事实依赖返回对应构思研究 owner，重新批准并生成新 baseline；纯 HLD 连续性错误返回 HR1。

### M4. HQ1 的评审维度有名称，但 pass/fail anchor 和最低证据量不够硬

**问题**

HQ1-A 的输出包含 domain review、cross-domain check、causal challenge 和 findings；HQ1-B 也列出了追踪测试。但当前没有规定：

- 每个维度至少挑战多少类风险；
- `pass` 必须给出哪些反证尝试；
- 什么叫 actionable finding；
- severity 的枚举和路由含义；
- 失败样例与通过样例；
- 如何防止“逐项写 pass”成为合法输出。

**影响**

双评审的隔离做得正确，但评审深度仍可能不稳定，不能单靠“两个 reviewer”保证质量。

**建议方向**

为 HQ1-A/B 分别建立 evidence-based rubric、pass/fail anchors、最低挑战集和 agentic negative fixtures。测试评审者是否能发现植入的因果、权限、信息、时空和 handoff 缺陷。

## 4. 已经成立的部分

以下设计在当前定义层面没有发现实质问题：

1. **Harness-first 类型正确**：没有把完整工作流伪装成单一 workflow skill。
2. **六个核心设计技能顺序合理**：结构坐标先建立，后续逐层增加编排、人物、信息、连续性和关键功能。
3. **职责边界整体清楚**：构思事实、HLD 宏观安排、LLD 细节和正文四层分界明确。
4. **唯一 owner 思路正确**：下游不能直接修改上游，问题按最早责任 owner 返回。
5. **权威入口正确**：正式 development baseline 是唯一内容入口，聊天、HTML 和旧稿不能替代。
6. **机器稿与人审稿分离正确**：HP1 是内容权威，HH1 只呈现，fidelity reviewer 独立检查漂移。
7. **作者最终批准绑定正确**：批准同时绑定机器包、人审包和 HTML，避免批准错版本。
8. **不使用固定对象数量替代质量**：符合小说差异性，不会因模板化硬指标制造虚假完整。
9. **关键场景边界基本正确**：定义场景功能而非动作、对白、感官和正文。
10. **最终交付物方向完整**：机器 HLD、人审包、completion 和 LLD handoff 四类成果都已被纳入。

## 5. 全链路走查结论

### 5.1 Happy path

```text
baseline → HB0 → HA1 → HS1 → HC1 → HI1 → HR1 → HK1
→ HQ1-A/B → HP1 → HH1-A/B/C → final author decision → HF1
```

在所有阶段一次通过、没有 must-ask、HP1 投影不发生语义选择的理想情况下，调用链是连通的。

### 5.2 非 happy path

以下三条当前未闭合：

```text
required_now → ? → external answer → ? → resume stage

stage revise/blocked → ? → durable result → ? → active return → resume

HP1 lld-handoff → ? semantic consumer acceptance → HF1
```

因此不能说调用关系已经“严丝合缝”。

## 6. 是否能交付合格成果

分三个层次判断：

| 问题 | 当前结论 |
| --- | --- |
| 内容域是否覆盖 HLD 应做的工作 | 基本覆盖 |
| Happy path 是否能组装出形式完整的 HLD | 可以 |
| 是否能稳定阻止浅层、错误或不可消费的 HLD 被批准 | 目前不能充分保证 |
| 是否能处理作者问题、返工和失败 | 目前没有完整闭环 |
| 最终 `lld-handoff.json` 是否经过真正消费者验收 | 没有 |

所以，当前定义**有能力指导开发出一个形式完整的 HLD 系统，但还不足以证明实现后一定稳定交付合格 HLD**。解决 H1–H4 后，才具备进入技能实现的条件；M1–M4 应在对应技能实现前一并关闭。

## 7. Review verdict

- Target type：`harness-workflow`，内部依赖 thinking/script/hybrid skills；类型选择正确。
- Harness paradigm：review-gated self-improving generation；方向匹配。
- Scope fidelity：通过。
- Ownership and boundary：通过，存在少量待硬化点。
- Happy-path topology：通过。
- Failure/author-return topology：未通过。
- Final handoff semantic acceptance：未通过。
- Thinking rigor：未通过。
- Overall verdict：**usable with gaps；存在实现阻断项，暂不建议进入开发。**

本 verdict 不表示技能“开发失败”，因为开发尚未开始；它只表示当前纸面定义还没有达到可直接实施的硬度。
