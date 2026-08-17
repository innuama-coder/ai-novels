---
name: novel-storyline-architecture-designer
description: 将已批准的小说访谈控制基线设计为完整的多线故事架构，先建立统一时间主轴，再定义各故事线的职责、状态推进、连接点、关键转折、高潮、埋点、探针与回收，以及交给世界、环境、事件和角色阶段的硬需求。用于自主构思 V2 的 S1 阶段；不定义具体世界系统、环境、事件或人物档案。
---

# 小说故事线架构设计

## Current-session contract correction (bounded V2 increment)

Root cause: the current contract conflates reviewable numbered adjacency with
a promoted relation, stores source consistency provenance in generic witness
IDs, assumes every structural line must converge to the main line, and permits
duplicate physical edges or late milestone registration. This rejects valid
non-relational candidates and terminal consequences while leaving exact source
coverage ambiguous.

Correction: current sessions explicitly dispose candidate ordered links as
`non_relational_candidate` or promote them through an existing relational
scope; model numbered normative constraints as source atoms with exact
dimension provenance; declare structural-line closure as convergence or a
causally entered terminal consequence; and enforce unique physical endpoint /
relation tuples plus target-first-occurrence realization. Historical sealed
runs remain read-only compatible. This is not a V3 redesign and must not infer
relations, terminality, or consistency dimensions from story vocabulary.

## 目标

让不同角度、方向和时间层的故事线共同还原同一个故事主体，并为后续四个设计阶段提供可验收的需求接口。

先建立全书共享的时间阶段，再把所有故事线的重要状态变化放进跨线里程碑。每个里程碑必须说明故事怎样发展、改变了什么，并标注其叙事功能。探针必须说明它在试探什么以及读者能观察到什么；回收必须指回较早的埋点；高潮必须由至少两条结构线汇合形成。

## 权威契约

完整读取：

- [自主构思工作流](../../docs/ai-novel-workflow/conception-autonomous-workflow-v2.md)的第 3、4、14、15 节；
- [S1 Schema](../../docs/ai-novel-workflow/contracts/autonomous-v2/storyline-architecture.schema.json)；
- [公共 canonical Schema](../../docs/ai-novel-workflow/contracts/autonomous-v2/canonical-common.schema.json)；
- [S1 唯一运行契约](references/runtime-contract.md)。

## 唯一生产运行路径

只允许使用 `scripts/run_v2.py`。在同一 `CODEX_THREAD_ID` 中依次调用
`start_s1_session()`、按契约顺序调用 `submit_s1_phase()`、最后调用
`run_s1()`。不得跳过受控会话、倒填阶段证据、传入会话外的一次性完整候选稿，
也不得手写 validation、manifest 或 completion。`validate_s1_package()` 只用于
只读复验，不能替代上述生产调用。

`line-design` 是第一道需要独立提交前复核的阶段，负责检查主张权限与作者锁定顺序的状态兑现；第三阶段还要接受下述拓扑与信息语义复核。先用
`inspect_s1_line_claims()` 对故事线与设计决策的全部结论性文本做无缝、
非重叠 span 清点并填写 `line_claim_authority`；再由生成线程调用
`start_s1_line_claim_review()`。必须换到不同的真实 `CODEX_THREAD_ID` 调用
`submit_s1_line_claim_review()` 以完整 `review` envelope 对每个 claim 和每个
`source_sequence_realizations` 项分别给出判定和理由，全部通过后回到原生成
线程提交 `line-design`。精确作者原文只能按 exact span 标为 `source_bound`；
其余文字必须明确归入 S1 结构推导、下游需求或开放项，不能靠作品、人名或
领域关键词猜测权限。`source_sequence_realizations` 必须 exact-cover 全部
`relation_mode=required` 或 `kind=ordered_link` 来源单元；逐项绑定 exact
from/to semantic state anchor。`within_line` 的 boundary 字段必须为 null。
`cross_line` 还必须声明 `boundary_from_anchor` 与 `boundary_to_anchor`：前者与
from anchor 同线且不得更早，后者与 to anchor 同线且不得更晚；二者定义实际
跨线实施边界。跨线项必须预留双方故事线共享且不复用的 connection ID，第三阶段
必须用相同 ID 精确兑现 boundary 的方向、line/state index/state text，而不是
强迫 semantic endpoints 同里程碑出现。direct cross 可令 boundary 等于 semantic
endpoints。
第二阶段封存前还会做可实现性闭包检查：已预留的跨线 ID 只按其 from→to
方向计边；双方共享、尚未被任何顺序项预留的 ID 可暂按双向潜在边证明容量，
但不确定第三阶段的最终方向。每条非主干、非 `optional_melody` 的结构线都必须
显式声明闭合方式：`converges_to_main` 必须能沿确定/潜在边抵达主干；
`terminal_consequence` 必须声明来自非终端结构干线的精确 source anchor 与共享
entry connection，并允许作为只入不出的后果终点。任一声明无法证明时以
`S1_SOURCE_SEQUENCE_STRUCTURAL_CLOSURE_MISSING` 或对应 closure 错误失败。
第三阶段仍须给出真实有向连接，并重新通过 state DAG 与结构闭包检查。
叙述规范、信息边界、评价规则等非故事状态关系可声明为
`semantic_constraint`：不得携带 state anchor 或 reservation，必须说明
`phase3_fulfillment_kind` 和匹配的 `expected_witness_type`。第三阶段对应 source
atom 不得为 `non_relational`，并须以 source atom/control 可追溯到所声明的
obligation、marker 或 consistency witness。选择 consistency 时还必须声明
`consistency_dimension`；只有该 semantic constraint 对应的 atom/control IDs
可加入该维度的 witness allow-list，其他维度与未声明 ID 仍须拒绝。全局因果骨架、角色演化等真实状态链
不得借此降级；独立 reviewer 必须逐项拒绝这类逃逸。
结构检查不替代语义复核：reviewer 必须检查 semantic endpoints 与 boundary
anchors 的相邻状态和上下文，并在 rationale 中分别解释完整来源终点与实施边界；
不得用较晚 boundary 替代全局 source step 的真实 endpoint。终态映到过早中间
state 时 reviewer 必须 fail。
拒绝后修改候选并以新 hash 重审，不得覆盖旧证据。

`topology-and-consistency` 也必须在提交前独立复核。生成线程调用
`start_s1_topology_semantic_review()` 冻结候选，另一真实线程调用
`submit_s1_topology_semantic_review()`，按 request 的 `coverage_universe` 对
`time`、`causality`、`information`、`state`、`source-sequence`、
`overcorrection` 六维逐项做 exact-cover 判定。来源顺序、全部里程碑状态结论、
所有 causal/associative 端点和全部可见性边界都必须有 JSON pointer、对象 ID、
里程碑顺序证据；可见性控制若没有 unknown/first-disclosure 成对义务，必须留下
带证据的审计豁免。六维全 pass 后才可提交第三阶段，最终封装会复验同一请求、
候选 hash、session、来源 ID 和 reviewer thread。

## 输入硬准入

只接受同一 run 的当前 B0 completion、B0 manifest、`author-control-baseline.json`、
S1 `input-gate.json` 和执行前 autonomous run-state。输入门必须为合法 `forward`，
或绑定唯一 active return 且 `resume_stage=S1` 的 `return_resolution`。

任一输入缺失、哈希失配、基线未覆盖 I0–I5、存在未处置结构性事实或 return 不匹配时停止；
不得生成候选模型。

## 职责

1. 将作者控制点转化为故事线需求，不遗漏因果义务。
2. 定义前置线、主体线、支持线、背景线及可选旋律线的独立职责。
3. 定义每条线的行动者槽、目标、压力、起始状态、状态变化和终态。
4. 定义汇流、分叉、交接、碰撞、揭示与同步连接点，并明确每个连接是
   `causal`（承担因果闭包）还是 `associative`（只表达呼应、并置或余韵）。
5. 先把每个 B0 控制值确定性拆成 `story_claim_units`：显式箭头链按每对相邻
   节点拆分，编号项、编号相邻关系、表格行、句子和结构化叶子分别登记；再用
   `story_claim_atoms` 对每个 unit 恰好处置一次。不得直接从整段控制生成首尾义务。
6. 把作者锁定的因果、先后、共同前提和信息边界原子化为
   `story_obligation_register`。每项义务必须精确定位到 claim atom，并以
   故事线 ID、状态索引和完整状态文本绑定前件与后件；信息义务还必须使用稳定
   `PROP-` ID。六种允许的义务仅为 `causes`、`strict_before`、`not_before`、
   `requires_all`、`first_disclosure`、`must_remain_unknown`。
7. 用 `story_obligation_coverage` 聚合每个控制点的全部 atom 和全部义务；一个
   控制点可对应多个 atom 与多个义务。明确无关系型义务或候选相邻关系不成立时，
   必须留下理由并交语义复核。不得靠领域关键词扫描猜测因果。
8. 以六条结构化记录分别检查跨线时间、因果、信息、权限、状态和主题一致性；
   每条记录必须列出证据对象、可证伪主张和失败条件，并覆盖全部故事线。
9. 分别生成 W1、E1、T1、C1 的语义化需求对象；每项包含来源、责任、所需能力、
   约束、验收条件和下游自由。

## 边界

- 时间推进属于 S1，但只到抽象故事节拍，不展开为场景或章节。
- 世界、环境、事件和角色均须从故事线及其时间架构取得设计需求；后续阶段可以具体化实现方式，但不得改变已定义的先后、状态变化、跨线连接或标记功能。
- 不定义具体地点、摆设、事件执行记录、人物档案、视角排期或成品叙事文本。

- 不创建具体世界规则、环境、事件或人物档案。
- 不以固定故事线数量或固定叙事模板替代完整性判断。
- `converges_to_main` 结构线必须仅沿结构线和 `causal` 连接抵达主体线，允许
  多跳汇入；`terminal_consequence` 只需由非终端结构干线经声明的因果入口抵达，
  且不得再产生因果出边。两者不得互相冒充。
- 可选旋律线至少关联一条结构线，但其跨线连接必须全部为 `associative`；
  它不能弥补主体因果缺口，删除后主体故事仍须成立。
- 不改变作者锁定项，不回答作者开放项。

## 交付与验收

交付 `storyline-architecture.json`、生成证据、`validation.json`、
`package-manifest.json` 和 `stage-completion.json`。只有模型通过 S1 Schema、
设计决策语义检查、需求覆盖集合相等检查、引用闭合检查和 return 绑定检查时，
才可写入 `ready` completion。不得手写或绕过验证器生成 completion。

每个连接还必须用状态索引和完整状态文本双重绑定两端；索引、文本或所属故事线
任一不一致均不得交付。以 `(storyline_id, state_index)` 为节点，把每条线的
相邻状态和所有 `causal` 连接组成唯一因果实现图：完整图必须无环；
`converges_to_main` 必须从自己的 `state_index=0` 可达至少一个主线状态，
`terminal_consequence` 则必须从声明的结构干线 source anchor 经唯一因果入口
进入并可前向抵达自身终态，同时保持无因果出边。
`line_order` 只规定人类阅读时的展示顺序，必须完整且不重复，不承担因果或时间
拓扑证明；`associative` 连接同样不伪造时间或因果先后。

六维一致性记录必须恰好各一条。`causality` 的证据只能引用故事线和
`relation=causal` 的连接；关联连接可以支持时间、信息、状态或主题判断，
但绝不能冒充因果证据。未知引用、缺线覆盖以及 claim/failure condition
中的占位文本均阻断交付。

`story_obligation_register` 不是剧情摘要。运行时必须从原始控制值重建并逐值核对
`story_claim_units`；每个 unit 恰有一个 atom。显式箭头的每个相邻 link 都必须
独占一条义务，不能共享一条首尾义务。编号相邻关系只是 candidate：若不形成义务，
必须显式标记为非关系并进入后续语义复核，不能把普通编号分类强制解释为时序。
每个义务的控制点来源、来源文件、值哈希、atom、前件锚点和后件锚点都必须通过
机器校验。单线前件不得位于后件之后；
所有先后/因果边合并后不得成环；同一命题与受众只能有一个首次披露点。
运行时还以全局里程碑及同里程碑 `state_refs` 顺序计算每个状态的首次出现 rank：
`strict_before` 必须严格递增，因果、共同前提与 `not_before` 不得逆序；信息窗口
按 `(proposition_id, audience)` 在全局时间轴校验。关联连接不因端点首次出现
次序而被误判为因果，但必须在独立语义复核中逐端点举证。
不同来源关系 claim 不得默认压成同一组锚点。只有来源本身无顺序语义，并且两个
atom 都声明相同 `co_realization_group`、具体 justification 和 witness IDs 时，
才可共同实现；required 或 ordered-link 来源一律 fail closed。普通编号项自身不被
推定为时序，只有确定性拆出的 ordered-link 才进入顺序 exact-cover。
每个 `causes` 和 `requires_all` 前件还必须能沿线内相邻状态前向边及
`relation=causal` 的精确 SLC 边抵达后件；较早的反向连接和 `associative`
连接不能充当可达证据。`strict_before/not_before` 只受时序义务图约束。
`story_obligation_coverage` 必须与 B0 控制点集合精确相等；任何
`no_relational_obligation` 都必须给出具体理由并标记为后续语义复核项。
