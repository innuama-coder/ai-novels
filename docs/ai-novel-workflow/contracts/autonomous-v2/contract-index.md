# 自主构思 V2 公共契约索引

这些 schema 是 `conception-autonomous-workflow-v2.md` 的机器契约。领域技能可以
通过自己的 schema 增加约束，但不得放宽或复制出不兼容的公共类型。

| 文件 | 约束对象 |
| --- | --- |
| `common-defs.schema.json` | 相对路径、SHA-256、artifact reference、completion reference 等公共类型 |
| `autonomous-run-state.schema.json` | B0–H1 当前版本、不可变状态快照、return 和开发失效状态 |
| `input-gate.schema.json` | 每个阶段冻结的输入门 |
| `package-manifest.schema.json` | 不可变交付包 manifest |
| `stage-completion.schema.json` | B0、S1–P1、H1 顶层阶段 completion；权威修订 B0 完成时精确核对当前父状态引用 |
| `canonical-common.schema.json` | 五个设计模型共享的来源、权限、决定、派生和开放项结构 |
| `storyline-architecture.schema.json` | S1 canonical 模型 |
| `world-model.schema.json` | W1 canonical 模型 |
| `environment-system.schema.json` | E1 canonical 模型 |
| `event-timeline.schema.json` | T1 canonical 模型；2.5 起包含按故事发生时间验证的主体生命周期、一次性许可消费与启动/关停因果闭包 |
| `character-system.schema.json` | C1 canonical 模型 |
| `conception-review.schema.json` | Q1 独立审查模型与任务隔离证据 |
| `novel-conception-package.schema.json` | P1 机器构思包 |
| `h1-review-plan.schema.json` | H1 报告计划 |
| `h1-fragment-briefs.schema.json` | H1-A 向 H1-B 交付的片段输入包 |
| `fragment-package.schema.json` | H1 非权威小说片段包 |
| `human-review-report.schema.json` | H1 组装后的人审内容模型 |
| `presentation-fidelity-review.schema.json` | P1 与候选人审内容逐元素的独立语义一致性审查 |
| `author-control-baseline.schema.json` | B0 作者控制基线、六份权威产物和事实依赖；当前来源唯一，权威修订的当前状态绑定 finalization.parent_run，native 或迁移仅作为父基线 |
| `h1-workspace-state.schema.json` | H1 内部复合阶段状态机 |
| `author-decision.schema.json` | `approved / revise / rejected` 三种作者决定 |
| `return-request.schema.json` | workflow 计算 owner 后生成的唯一活动 return |
| `development-handoff.schema.json` | P1 交给小说开发的授权与边界 |
| `conception-completion.schema.json` | 最终构思完成与开发准入 |
| `authority-revision-bootstrap-intent.schema.json` | 已批准构思权威修订的新运行事务意图 |
| `authority-revision-evidence-index.schema.json` | 父构思与后续作者指令的不可变证据索引 |
| `author-directive-binding.schema.json` | 作者原话绑定；明确不批准系统生成的新字节 |
| `authority-revision-patch-plan.schema.json` | 与确定性候选摘要绑定的七个允许控制项精确局部文本修订 |
| `authority-revision-semantic-review.schema.json` | 外部任务封存、逐项通过且与改稿者三重身份隔离的语义复核 |
| `authority-revision-finalization.schema.json` | 基础/生效权威材料及修订证据的最终绑定 |
| `authority-revision-bootstrap-validation.schema.json` | 新运行建立前的完整验证结果 |
| `authority-revision-bootstrap-completion.schema.json` | 权威修订新运行的建立凭证 |

## Finalization runtime boundary

公共 schema 只约束文档形状；以下 runtime 负责 schema 无法证明的 current、哈希、
拓扑、原子发布和状态转换：

- `runtime/h1_completion.py`：正式重验 H1-C 输入链，把 current rendered workspace
  提升为唯一 H1 stage completion；H1-C 自身不得生成 completion。
- `runtime/author_decision.py`：只接收外部 sealed `approved / revise / rejected`
  事件。`revise` 的 owner、恢复点与失效后缀由 workflow 计算；跨 owner 必须拆分。
- `runtime/final_completion.py`：只允许 current `approved` 分支绑定九个顶层
  completion、P1、H1 HTML、作者决定和 development handoff 后授予开发准入。
- `runtime/production_orchestrator.py:apply_internal_h1_plan_return`：在组装前
  只接受与当前候选报告、P1、plan、fragment 和独立审查者身份精确绑定的
  `presentation-fidelity-review.verdict=revise`，以仅追加事务退回 H1-A plan；
  旧 plan、fragment 与 assemble 工作单不可修改或复用。
- `skills/novel-conception-deliverable-assembler/scripts/run_v2.py`：P1 目标目录存在时
  只允许 exact existing crash recovery。runtime 必须重验既有包，并证明 coordinator
  状态、sealed gate、B0–Q1 来源集合和实现快照与包内绑定完全一致。执行前状态中的
  valid non-current orphan 可首次接纳；仅 forward 模式下，`previous_state`、current
  P1 completion 和 successor path 完全匹配的已持久化 successor 可 persistent replay。
  partial、tampered、stale 或异门包一律原地保留并 fail closed，不得覆盖。

三个发布边界都必须执行：staging → 完整验证 → 输入 TOCTOU 复查 → 原子发布 →
目的地复验 → coordinator。最后一步拒绝时，包保持为 valid non-current orphan。
首次接纳返回 `P1RunReceipt.replayed=true`、`transition.replayed=false`；forward
persistent replay 时两者均为 `true`。return-resolution 已进入 `resolved_returns`
后严格 one-shot，原样抛 `COORD_RETURN_ALREADY_RESOLVED` 且不产生新 receipt。
该恢复协议属于 runtime 跨文件语义；现有 package、manifest 与 completion schema
均不改变。

所有 schema 使用 JSON Schema Draft 2020-12。实现前必须：

1. 解析全部 schema；
2. 检查所有 `$ref`；
3. 使用真正执行本目录所用 Draft 2020-12 关键字的 validator 验证实例，不得只检查 schema 字段是否存在；
4. 用正例验证正常前进、局部 return、上游重新访谈和 H1 局部重跑；
5. 用反例验证空／错序上游、未绑定 return、绝对路径、旧哈希、H1 混装、非法决定分支和缺失 completion 会失败；
6. 对 Schema 不能跨文件计算的当前版本、哈希、集合相等、package profile 和 owner 路由执行确定性语义验证；
7. 将 schema、语义 validator 和阶段拓扑表哈希纳入对应 completion。

本目录的硬契约按责任分为两层：

- **Schema 层**：拒绝 Q1 verdict/status/finding 矛盾、错误 return 类型或失效后缀、
  只有 ID 的阶段需求、空壳 H1 报告，以及缺少单方案排除证据的设计决定。
- **语义层**：执行 B0 控制登记集合相等、设计选择属于候选集合、S1→W1、
  W1→E1、S1→T1、S1→C1 需求集合相等、事件—环境—角色槽引用闭合、
  active/resolved return 状态转换，以及 H1 权威来源到可见元素的精确覆盖。

只运行其中一层不能生成 completion。`testing/autonomous_v2_schema_runtime.py` 是仓库
回归用的严格关键字子集执行器和语义验证参考；生产 harness 仍须使用 Draft 2020-12
validator，并执行同等或更强的上述语义检查。
