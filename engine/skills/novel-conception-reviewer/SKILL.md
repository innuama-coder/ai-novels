---
name: novel-conception-reviewer
description: 独立审查自主构思 V2 的故事线、世界、环境、事件和角色五个 canonical 模型，验证跨域覆盖、因果、状态、真实性、人物能动性、主题支撑和开发可用性，并确定性给出 ready、revise 或 blocked。用于 Q1 技术审查；不修改模型、不生成新故事答案、不组装交付物或人审报告。
---

# 小说构思独立审查

## 目标

独立证明 S1–C1 与 B0 共同形成一部完整、一致、可信、可进入开发的小说构思。

## 权威契约

完整读取：

- [自主构思工作流](../../engine/docs/ai-novel-workflow/conception-autonomous-workflow-v2.md)第 3、9、14、15 节；
- [Q1 Schema](../../engine/docs/ai-novel-workflow/contracts/autonomous-v2/conception-review.schema.json)；
- [return Schema](../../engine/docs/ai-novel-workflow/contracts/autonomous-v2/return-request.schema.json)。

本目录旧 D1/R1 `references/` 和 `scripts/` 只服务历史 1.x 包；不得用于生成、验证或
批准 V2 Q1 completion。

## 输入硬准入

只接受同一 run、同一 B0 baseline manifest 的当前 B0、S1、W1、E1、T1、C1
completion、manifest、canonical 模型、Q1 input gate 和执行前 run-state。必须重新
执行五个 Schema 验证器、设计决定检查、跨模型需求／引用／覆盖检查及来源哈希检查。

Q1 必须使用两个不同任务：

1. `semantic-reviewer` 可读取 B0、五个模型和生成证据；
2. `handoff-evaluator` 只能读取 B0、五个 ready canonical 包和 manifest，禁止读取
   聊天、访谈报告、生成证据、语义 findings 和预期答案。

## V2 运行入口

只使用 `scripts/run_v2.py`，按以下顺序调用；不得跳步、倒填 evidence 或把两个身份
参数化为同一任务：

1. 在调度上下文调用 `start_q1_controller`，重新验证并冻结 Q1 input gate、B0 与
   S1–C1 当前包，同时冻结完整 current implementation catalog 与 canonical digest。
   后续每个入口必须在写前重算该 identity；实现或协议变化后不得续跑旧 controller、
   partial semantic 或 handoff workspace，必须创建 fresh attempt。
2. 在独立 `semantic-reviewer` 任务调用 `start_semantic_review`，再依次调用
   `submit_semantic_phase` 提交 `review-plan`、`domain-challenges` 和
   `cross-domain-challenges`。payload 必须由该任务编写，运行时不生成审查语义。
P1 必须由 Agent 显式选择 B0/S1–C1 审查对象并提交当前对象指纹；其中 S1 与 T1
   的全部带 ID canonical 对象必须进入计划，不能抽样。P2/P3 的每项
   review check 必须提交显式 assertion binding，将证据对象完整哈希、具体字段或
   关系投影、挑战算子和结论绑定。运行时只从冻结 canonical 重算并拒绝失配，不替
   Agent 选择对象、关系或生成绑定。

   T1 `2.2+` 中 planned/canonical 双写不是两个审查对象。运行时只在事件、命题、
   因果边三组正式投影逐字段闭合时，使用 canonical 完整对象及 canonical pointer
   形成唯一指纹；缺项、漂移或第三来源必须在 evidence 写入前失败。

   T1 `2.5` 的生命周期不是章节文字判断。`review-plan` 必须列出
   `typed_lifecycle_causal_closure`，T1 域审查必须绑定
   `T1-2.5-typed-lifecycle-causal-closure`；跨域审查的同名 check 必须同时绑定全部
   `LFS-*`、`LFC-*` 与它们引用的 S1/E1 来源对象。handoff 的
   `chronology_reconstruction` 和 `causal_precondition_trace` 也必须各自完整覆盖这些
   对象，分别证明世界发生顺序与正式因果／权限链可以由下游独立重建。
3. 切换到新的 `handoff-evaluator` 任务调用 `start_handoff_review`。该入口只投影
   B0/S1/W1/E1/T1/C1 各自的 canonical 与 manifest，共 12 个文件。完成独立测试后
   handoff-evaluator 必须为九项开发可用性任务逐项提交同结构 assertion binding，
   再调用 `seal_handoff_review`。除主体、故事线、事件条件、人物选择和开发自由外，
   还必须完成 `chronology_reconstruction`、`causal_precondition_trace`、
   `information_release_trace`、`author_control_trace`。后四项 assertion binding 的
   证据并集必须覆盖 S1 与 T1 的全部带 ID canonical 对象。
4. 回到原 `semantic-reviewer` 任务调用 `import_sealed_handoff`，只导入已封存证据；
   再调用 `submit_final_review` 提交最终 review、finding 与 verdict。
5. 最后调用 `run_q1`。`ready` 生成独立审查 manifest 和 Q1 completion；
   `revise/blocked` 只生成 router return bundle 与下一 run-state，不生成 ready
   manifest 或 Q1 completion。

`CODEX_TASK_ID` 与 `CODEX_THREAD_ID` 必须来自当前受控环境。公开入口不接受身份覆盖
参数；semantic、handoff 与 S1–C1 生成上下文任一重合即失败。

## 职责

1. 检查五域内部完整性及跨域引用与覆盖。
2. 检查外部事实依据和虚拟世界内部一致性。
3. 检查故事线、事件因果、时间、状态和信息连续。
4. 检查环境能否实际承载事件行为。
5. 检查人物动机、能力、权限、信息、选择和代价与事件匹配。
6. 检查主题是否通过选择和后果被检验。
7. 挑战便捷解法、巧合推进、工具人和无人承担的后果。
8. 为每条 finding 计算唯一 owner 和最小重跑范围。
9. 生成 `quality_coverage` 证书，逐项登记全部 S1 obligation、T1 realization、对应
   handoff check 和尚未解决的阻断质量记录；缺项不得 ready。

`DEV-` 是 C1 交付的终端开发自由对象。Q1 将其索引为
`kind=development-freedom`，finding 的 evidence/affected ID 可以引用它；
确定性 owner 路由必须得到 `C1`，不得把 DEV 误判为 Q1 治理对象或作者开放项。

## Verdict 硬门

- `ready`：`status=ready`，findings 只能为 `note`，`return_request=null`，
  `quality_coverage.result=complete` 且未解决阻断质量记录为空。
- `revise`：`status=revise`，至少一条 `contradictory` 或 `revise` finding，并绑定
  唯一活动 return。
- `blocked`：`status=blocked`，至少一条 blocked finding，并绑定唯一活动 return。

Schema、语义审查和 handoff 测试任一失败都不能生成 ready completion。

## 边界

- 不修改 S1–C1。
- 不提出新的故事答案、审美偏好或市场模板。
- 不写构思规格、报告摘要、小说片段或 HTML。
- 不以字段存在、平均分或通用套话替代故事专属证据。
- 不把 `ready` 当作作者批准。

## 交付

交付 `conception-review.json`、`handoff-test-evidence.json`、两个任务的执行记录、
validation、manifest，以及仅在 verdict ready 时生成的 Q1 completion。revise／blocked
改为交付通过 router 验证的 return package 和下一 run-state。
