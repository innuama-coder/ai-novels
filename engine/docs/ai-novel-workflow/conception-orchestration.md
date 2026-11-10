# 构思编排：兼容性说明

> **自主构思 V2 权威迁移**：访谈批准之后的故事线、世界、环境、事件、角色、
> 独立审查、机器交付和人审报告调用链，改由
> [conception-autonomous-workflow-v2.md](conception-autonomous-workflow-v2.md)
> 定义。本文后文的 `D1 → R1 → 作者最终批准` 仅解释旧包，不得用于创建新的
> 自主构思 completion。

> **权威迁移**：访谈的顺序、回退、会话产物、验证和审批现在唯一由
> [novel-conception-interview harness](../../harnesses/novel-conception-interview/workflow.md)
> 与其 `rules.md` 定义。本文件保留为旧链接的解释材料；若其后文与 harness
> 冲突，以 harness 为准，且不得据此直接交接技能或绕过 completion packet。

## 1. 使命与边界

本文件将构思阶段编排为一个**评审门控、有限回退的 DAG harness**。它规定技能顺序、唯一控制点所有权、交接产物和回退规则；不把各技能合并成一个大提示词，也不授权下游静默补设定。

构思的完成含义是：方向、主体、世界、人物、因果和叙述六类信息均有当前有效的权威来源，且一位未参与访谈的开发者能据此开发而不猜测主线决定。

适用的规范主线包含十个技能：六个作者访谈技能、两个审计/呈现技能和两个开发交接技能。旧 PRD/HLD/LLD 技能属于另一条开发路径，未建立权威桥接前不得混用来补同一控制点。

## 2. 状态、版本与访谈记录

每份设计产物维护：决策状态（`confirmed` / `delegated` / `provisional` / `blocked`）、交接状态（`ready` / `blocked`）、输入版本、权威来源和风险/回看点。`ready` 只表示可消费，不表示所有决定均由作者直接确认。

六个访谈技能还必须遵守 [interview-protocol.md](interview-protocol.md)：第一条实质问题前展示问题预算和预计时长；结束时生成完整逐轮访谈报告。报告用于审计与回退，当前设计产物才是下游唯一可消费的结论。

## 3. 默认调用图

```text
作者原始材料
  │
  ▼
I0 意图 ─► I1 主体 ─► I2 世界 ─► I3 角色 ─► I4 因果 ─► I5 叙述
  │              │          │           │           │
  │              └──仅当世界使主体选择不成立时回退───┘
  │
  ▼
V1 访谈完整性审计 ─► V2 三板块 HTML 简报 ─► 作者访谈结果批准
  │                                                        │
  └── revise / blocked：回到唯一拥有者 ───────────────────┘
                                                           ▼
                                                   B0 权威基线
                                                           ▼
                                            S1→W1→E1→T1→C1→Q1→P1
                                                           ▼
                                         H1-A→H1-B→H1-A→H1-C→H1 completion
                                                           ▼
                                                   外部作者决定
                                              approved / revise / rejected
```

| 门 | 技能 | 目标与唯一职责 | 最小输入 | 通过产物 | 明确不负责 |
| --- | --- | --- | --- | --- | --- |
| I0 | `novel-intent-facilitator` | 锁定故事承诺、主题问题、范围、硬边界和作者授权。 | 作者 idea/材料 | `intent-card.md` + 报告 | 角色、世界规则、事件或 POV。 |
| I1 | `novel-subject-designer` | 锁定谁承担核心选择、目标/代价和关键关系功能；提出所需的世界压力。 | I0 `ready` | `subject-definition.md` + 报告 | 完整世界规则、心理模型、事件链。 |
| I2 | `novel-world-interviewer` | 锁定可运行的世界前提、规则、环境、资源、权力、历史、信息与压力机制。 | I0、I1 `ready` | `world-operating-contract.md` + 报告 | 人物弧、事件顺序、POV 或场景描写。 |
| I3 | `novel-character-interviewer` | 锁定人物如何理解世界压力、默认/越界行为、关系动力和变化边界。 | I0–I2 `ready` | `core-character-design.md` + 报告 | 新增世界基本规则、安排事件、读者披露。 |
| I4 | `novel-causality-architect` | 将世界后果和人物选择组织成触发、转折、危机、高潮和结局的因果链。 | I0–I3 `ready` | `causal-storyline.md` + 报告 | 改写世界、人物或叙述事实。 |
| I5 | `novel-narrative-contract-designer` | 规定谁讲述、读者何时知道什么、时间组织和表达禁区。 | I0–I4 `ready` | `narrative-contract.md` + 报告 | 改写事实、因果、人物目标或世界规则。 |
| V1 | `novel-interview-integrity-auditor` | 审计六维覆盖、版本链、访谈报告和跨文档一致性。 | I0–I5 当前产物与报告 | `interview-integrity-report.md` | 发起创作访谈或补设定。 |
| V2 | `novel-interview-brief-generator` | 将通过审计的材料压缩成世界、故事线、人物三板块 HTML。 | I0–I5 `ready` + V1 `ready` | `interview-review-brief.html` | 补设定、代替作者批准。 |
| B0–P1 | V2 自主构思技能链 | 在 `novel-conception-autonomous` 持久调度器签发的唯一工作单下，依次建立基线、故事线、世界、环境、事件、角色、独立语义审查和机器交付包。 | 当前访谈批准与持久 production state | 八个正式 stage package、逐阶段 state 与 P1 completion | 跳序、跨所有权补写、手写 completion、用测试 driver 代替生产调度。 |
| H1-A/B/C | V2 人审呈现技能链 | 规划十分钟评审、写片段、组装报告并确定性渲染离线 HTML。 | 当前 P1 completion | 同 session 的 plan、fragments、assembly、HTML 与 rendered workspace | 改写 P1 控制信息、由 renderer 推断关系、提前生成顶层 H1 completion。 |
| 总调度/H1/作者门 | `novel-conception-autonomous` | 从访谈批准开始维护 append-only 状态和唯一 owner 工作单；重验 H1 子链，分事务发布 H1、转发外部决定，仅 approved 发布 final。 | 当前访谈批准；作者阶段另需外部密封决定 | 可恢复 production state、三分支 receipt；approved 才有 final completion | 创作领域内容、创建作者决定、让 revise/rejected 进入开发、接受 D1/R1。 |

## 4. 访谈计划与报告门

| 访谈 | 决策组 | 问题预算 | 时长估计 |
| --- | ---: | ---: | ---: |
| I0 意图 | 4 | 12–16 | 20–35 分钟 |
| I1 主体 | 4 | 12–16 | 20–35 分钟 |
| I2 世界 | 8–10 | 22–30 | 45–75 分钟 |
| I3 角色 | 5 | 首位核心角色 14–18；每增加一位 +8–12 | 35–70 分钟 |
| I4 因果 | 4 | 16–22 | 35–55 分钟 |
| I5 叙述 | 4 | 14–20 | 30–45 分钟 |

每一门只在其设计产物和访谈报告均存在、版本一致、状态可交接时才算完成。超预算必须由作者同意 `plan_revision`；缺少逐轮原始问答、计划/实际问题数或修订链的访谈报告，V1 至少给出 `revise`。

## 5. 所有权与回退

| 发现的问题 | 唯一拥有者 | 修订后必须重跑 |
| --- | --- | --- |
| 故事承诺、范围、主题禁区、作者授权或事实采用方式不清 | I0 | I1–R1 |
| 核心选择、目标/代价、关系因果功能不成立 | I1 | I2–R1 |
| 规则、资源、机构、环境、历史、信息通道或世界压力不成立 | I2 | I3–R1 |
| 人物动机、压力行为、关系误读、变化阈值不可预测 | I3 | I4–R1 |
| 触发、转折、危机、高潮或结局缺少前提、选择或后果 | I4 | I5–R1 |
| POV、读者知识、披露、公平隐瞒、时间或表达边界冲突 | I5 | V1–R1 |
| 覆盖不足、报告缺失、版本失效或跨文档矛盾 | V1 指向最早拥有者 | 由回退门确定 |
| 作者否决 HTML 中的某项 | 对应 I0–I5 拥有者 | V1–R1 |

世界与主体的关系受限：I1 可以声明“主体选择需要何种外部压力”，I2 拥有该压力的世界实现。只有 I2 证明已确认世界使主体选择不可行时，才形成单一 `subject-revalidation` 回退包；不得形成无限循环。

一次只允许一个结构性回退包活动。回退包必须记录问题、受影响控制点、权威输入、责任门、待废弃版本和重跑范围。下游不得就地修补。

## 6. 准入与完成

1. 每门只能读取上游 `ready` 的当前设计产物及允许继承的风险项；不得从聊天记录、旧稿或下游文档补回决定。
2. 现实历史、科学、法律、地域或行业事实需要时走条件研究支线：`事实依赖 → 研究包 → 作者采用方式 → 回写 I0 或 I2`。研究包不拥有创作决定权。
3. V1 `ready` 是访谈简报的硬门；访谈简报的作者批准是 B0 的硬门；P1 与 rendered H1 当前一致、且外部作者决定为 approved 后，才允许最终构思 completion 进入开发。
4. NDB 的完整性由访谈权威材料、B0–P1 正式 stage completion、H1 人审包、外部作者决定和最终 completion 共同证明，而非由任一长文档替代。
