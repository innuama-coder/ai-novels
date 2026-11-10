# HLD 技能定义修复方案 V1

> 本方案是定义修复的前置门。它不修改现有技能，不代表修复已经执行。

## 1. 根因定位

### RC1：控制面只完整建模了 ready，没有统一建模其他结果

现有定义把 ready package、stage completion、blocked report、revision report、return 和 author decision 分散定义。结果是 happy path 清楚，revise、blocked、must-ask 和上游事实重入没有共同的 work-order result 与状态事务。

对应 findings：H1、H3、M3。

### RC2：验收边界早于实际交付物

LLD readiness evaluator 在 `lld-handoff.json` 产生前运行，验证的是设计模型，而不是最终交接文件。结构验证与语义消费验证被错误合并。

对应 finding：H2。

### RC3：thinking skill 只有 artifact contract，没有 decision contract

六个核心技能和 HQ1 已经知道“交付哪些字段”，但没有冻结分析步骤、候选真实性、选择依据、反证、自检和 pass/fail anchor，因此无法阻止合规填表。

对应 findings：H4、M2、M4。

### RC4：确定性 owner 接收了未确定的语义映射

HP1 被要求把 HKF 与全部约束变成 LWK，但 HKF→LWK 的基数、分组和 freedom 来源未在 HK1 决定。HB0 的 `allowed_stages` 也缺少固定访问矩阵。Script 因而可能被迫作语义判断。

对应 findings：M1，并影响输入硬度。

## 2. 总体修复策略

不增加技能数量，不改变构思／HLD／LLD／Writing 四层边界。14 个技能重新排成：

```text
HB0 → HA1 → HS1 → HC1 → HI1 → HR1 → HK1
→ HQ1 语义审查
→ HP1 机器包与 lld-handoff
→ HQ2 实际 handoff 消费验收
→ HH1-A → HH1-B → HH1-C
→ final author decision → HF1
```

原 `novel-hld-lld-readiness-evaluator` 不新增副本，改为 top-level HQ2，专门读取 HP1 正式交付。HQ1 负责上游 HLD 模型的语义质量和开发可用性；HQ2 负责最终 handoff 的消费者验收。

## 3. 解决 RC1：统一阶段结果与作者事务

### 3.1 `stage-result.json`

每个 work order 必须且只能产生一个 `stage-result.json`，状态为：

- `ready`：引用 ready manifest、validation 和 completion；
- `revise`：引用 candidate manifest、revision report 和本地 owner；
- `blocked`：引用 failure manifest、blocked report、blocker class 和建议 target；
- `runtime_error`：无语义 verdict，记录 runtime failure。

Skill 只声明事实和受影响对象，不决定最终 return owner。Harness router 根据固定 owner matrix 计算 owner、resume stage 和 invalidated suffix。

### 3.2 非 ready 包

Revise 包固定包含：

```text
candidate canonical / evidence / execution
revision-report.json
validation.json
result-manifest.json
stage-result.json
```

Blocked 包固定包含：

```text
gate-data.json
blocked-report.json
validation.json
result-manifest.json
stage-result.json
```

两者均无 stage completion，但 result manifest 和 stage result 被下一份 run-state 强绑定，形成不可变失败证据。

### 3.3 Parent consumption

Harness 对结果的唯一动作：

| Result | Harness 动作 |
| --- | --- |
| ready | 重验 completion，推进到下一 stage |
| revise/local | 生成 local return，同 owner 新 revision；不推进 |
| blocked/upstream | 生成 upstream return，失效 owner 后缀 |
| blocked/author_required | 进入 author-question transaction |
| blocked/reality_dependency | 进入 conception reentry |
| runtime_error | 保持 current state，记录错误；不得解释为语义失败 |

### 3.4 中途作者问题

新增 harness artifact：

- `author-question.json`：绑定 source control、受影响 decision、owner、允许回答范围、resume stage 和问题原文；
- `author-answer-event.json`：外部事件，绑定 question hash、event seq 和作者原文；
- `author-resolution.json`：确定性分类为 `hld_local_resolution` 或 `conception_authority_change`。

新增状态：`waiting_author_answer`。

- `hld_local_resolution`：答案只解释 baseline 中已存在的 must-ask，不改变 mandatory/open 事实；同 stage 以 return-resolution 重跑，后续全部绑定 resolution；
- `conception_authority_change`：关闭当前 HLD run 的开发资格，返回构思 owner，重新批准并重新生成 development baseline 后启动新 HLD run。

最终作品批准仍使用独立 `author-decision.json`，不得与中途回答混用。

### 3.5 现实事实重入

新增 `reality-dependency-request.json`：记录 claim、为什么是结构性、受影响对象、所需证据和发现 stage。

HLD 不自行研究。结构性事实依赖返回构思事实研究 owner，重新批准和 preparation 后开启新 run；纯 HLD 的时间、权限、资源或迁移矛盾仍返回 HR1／对应 HLD owner。

## 4. 解决 RC2：把 LLD acceptance 放到实际 handoff 之后

### 4.1 HQ1

`novel-hld-semantic-reviewer` 成为单一 top-level HQ1：

- 检查 HB0 与 HA1–HK1；
- 检查领域和跨域语义；
- 检查 HLD 开发可用性；
- 不读取 HP1；
- pass 后允许 HP1 组装。

### 4.2 HQ2

`novel-hld-lld-readiness-evaluator` 移到 HP1 后，精确 upstream：`[HB0,HP1]`。

唯一内容 allowlist：

- `novel-hld-package.json`；
- `lld-handoff.json`；
- HP1 cross-index、traceability、manifest、validation、completion。

禁止读取聊天、generation evidence、HQ1 findings、独立 HA1–HK1 工作区和预期答案。

HQ2 必须以正式 LLD caller 身份验证：

- 每个 LWK 可解析；
- 每个 LWK 的约束、开放项和 freedom 可区分；
- 能从 handoff 追溯到 HKF、章节、事件、人物、环境、POV 和状态；
- 无需新增高层结构或主要事实；
- HP1 没有遗漏 HQ1 已通过的必要义务。

HQ2 pass 产生 top-level completion。HH1 和 HF1 都必须绑定当前 HQ2 completion。

## 5. 解决 RC3：补齐 thinking contract

### 5.1 六阶段公共决策 SOP

HA1–HK1 每次受控生成必须依次提交四类 evidence：

1. `obligation-analysis`：穷举当前 stage 必须解决的上游义务、开放项和禁止项；
2. `option-analysis`：对真实 freedom 生成可区分方案；只有一个可行方案时提交排除证据；
3. `projection-analysis`：把选择投影到 canonical 对象，证明没有只写理由不落模型；
4. `adversarial-self-review`：主动寻找因果、覆盖、边界、权限、信息和下游消费反例。

候选真实性规则：两个候选必须在至少一个实际 canonical 决策字段上不同，并产生不同代价或下游影响；同义改写不算候选。

### 5.2 各 skill 的专属决策框架

| Skill | 必须执行的核心判断 |
| --- | --- |
| HA1 | 比较结构形态；验证阶段变化、转折承载和章节容器弹性 |
| HS1 | 逐线建立—发展—转折—回收；验证连接必要性和主体重建 |
| HC1 | 逐人物压力—选择—代价—结果；验证能力／权限／信息匹配 |
| HI1 | 逐知识变化来源；验证 setup—probe—reveal—payoff 和 POV 不越权 |
| HR1 | 逐状态连续；验证时间、空间、资源、切线、张力累积和恢复 |
| HK1 | 逐高层义务证明 HKF 必要；检查合并、拆分、过载和 LLD 边界 |

每个 skill 定义必须加入专属 pass/revise/fail anchors、证据要求、正例类型和边界反例类型。实现时这些进入 `references/sop.md`、evaluation spec 和 agentic fixtures；顶层 catalog 固定契约，不塞入冗长故事样例。

### 5.3 对象级 contract

在实现 Schema 前，先为每个 canonical 数组定义：元素 ID、必需字段、枚举、引用允许集合、基数规则、跨字段不变量、覆盖算法和失败等级。

覆盖采用故事义务集合相等或明确 disposition，不采用固定数量。关键不变量至少包括：结构无环、顺序唯一、来源可追溯、状态前后闭合、开放项不被裁决和 owner 唯一。

### 5.4 HQ1/HQ2 anchored rubric

HQ1 使用 blocker-first rubric：权威继承、结构因果、多线、人物弧线、信息悬念、时空连续、关键功能、主题支撑和 HLD/LLD 边界。每个 pass 必须包含完成的反证挑战和对象证据；不得只输出 `pass`。

HQ2 使用消费者测试 rubric：重建、随机追踪、约束分类、缺失猜测和 handoff 完整性。`missing_guesswork` 非空即 fail。

## 6. 解决 RC4：把语义决定移回正确 owner

### 6.1 HK1 拥有 LLD work requirement

HK1 canonical 新增 `lld_work_requirements[]`。每项明确：

- `LWK-` ID；
- 关联的一个或多个 HKF；
- 分组依据；
- 进入／退出状态；
- required elaboration；
- LLD freedom；
- acceptance criteria。

HK1 对合并／拆分承担语义责任。HP1 只做一对一无损投影：一个 `lld_work_requirement` 生成一个 handoff LWK，不再判断分组。

### 6.2 HB0 固定 source access matrix

Harness manifest 固定 `SOURCE_ACCESS_MATRIX`，按 domain 和 artifact role 声明每个 stage 可读内容。HB0 只执行矩阵，不能自行判断 `allowed_stages`。

## 7. 修复后的精确拓扑

| Stage | 精确 upstream |
| --- | --- |
| HB0 | `[]` |
| HA1 | `[HB0]` |
| HS1 | `[HB0,HA1]` |
| HC1 | `[HB0,HA1,HS1]` |
| HI1 | `[HB0,HA1,HS1,HC1]` |
| HR1 | `[HB0,HA1,HS1,HC1,HI1]` |
| HK1 | `[HB0,HA1,HS1,HC1,HI1,HR1]` |
| HQ1 | `[HB0,HA1,HS1,HC1,HI1,HR1,HK1]` |
| HP1 | `[HB0,HA1,HS1,HC1,HI1,HR1,HK1,HQ1]` |
| HQ2 | `[HB0,HP1]` |
| HH1 | `[HB0,HP1,HQ2]`；内容输入仍只有 HP1 |
| HF1 | `[HB0,HA1,HS1,HC1,HI1,HR1,HK1,HQ1,HP1,HQ2,HH1]` |

## 8. 方案关闭矩阵

| Finding | 修复机制 | 可验证完成条件 |
| --- | --- | --- |
| H1 | author-question transaction | 问题、外部答案、resolution、状态和 resume 全部有唯一绑定 |
| H2 | HQ2 位于 HP1 后 | HF1 必须消费针对当前 lld-handoff 的 HQ2 pass |
| H3 | stage-result + result manifest | ready/revise/blocked/runtime error 都有 parent-consumption 和状态 successor |
| H4 | 四阶段 thinking SOP + anchors | 六技能均有决策框架、证据、反例和 verdict 边界 |
| M1 | HK1 输出 lld_work_requirements | HP1 对 LWK 只做一对一投影，无语义选择 |
| M2 | 对象级 contract table | 每个数组元素可唯一实现 Schema 和 validator |
| M3 | reality dependency reentry | HLD 不研究，新事实只能经构思批准和新 baseline 回来 |
| M4 | HQ1/HQ2 anchored rubric | pass 必须带反证挑战和对象证据，机械 pass 无效 |

## 9. 方案自身风险检查

- **没有增加技能数量**：仍为 14 个，只移动 LLD evaluator 的位置并改为 HQ2。
- **没有扩大 HLD 内容边界**：中途作者问答、事实重入和 HQ2 都是控制／评审，不生成故事内容。
- **没有让 script 承担判断**：LWK 分组回到 HK1，source access 来自固定矩阵。
- **没有削弱独立审查**：HQ1 与 producer 隔离；HQ2 与上游工作区隔离；HH1 fidelity 仍独立。
- **没有让作者决定被 Agent 代替**：所有 author event 外部、密封、一次消费。
- **没有把未实现当成修复完成**：本轮只修改定义；Schema、代码、fixtures 和 live E2E 仍属于后续开发。

## 10. 允许执行修复的前置判定

方案可以进入定义修复，因为：

1. 8 个 findings 均有单一机制和可验证完成条件；
2. 新拓扑无环，所有语义产物在被验收前已存在；
3. 每次失败和作者问答都有 durable parent-consumption；
4. 14 个 skill 的数量、核心职责和四层边界保持稳定；
5. HP1、HH1、HF1 继续分别只组装、呈现和封闭；
6. 最终 LLD admission 新增了针对实际 handoff 的语义证据。

前置判定：**方案通过，可以开始修改定义。**
