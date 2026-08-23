---
name: novel-event-timeline-designer
description: 将已验收的 B0/S1/W1/E1 构思包转化为可验证的小说事件时间线。用于 T1 阶段：先完成初态、事件、因果、里程碑、连接、义务、能力 occurrence 与权限实例计划，经独立语义审查后精确实现并封包；不创作场景正文或角色心理。
---

# 小说事件时间线设计

## 目标

把故事线架构落实为一套完整、可执行、可审计的事件模型：每个故事状态变化都有事件承载，每个事件都有环境能力、因果前提、时间位置和下游结果，所有故事线连接与叙事义务都能从输入追溯到输出。

当前生产模型固定使用 T1 schema `2.5`，语义审查协议固定为 `t1-initial-event-plan-semantics-v5`，只接受 E1 `2.4`。T1 `2.0`–`2.4` 仅按各自冻结的实现与发布包 identity 做只读历史验证；不得新建、重封或把当前结果降标为历史版本。2.3 仅有受信的完整实现绑定快照，没有发布过 ready package，因此可审计其实现 provenance，但完整 package replay 必须因 package identity inventory 为空而关闭。T1 2.4 把叙事因果边与 capability/proposition/token/sequencing 依赖边分型；2.5 在此基础上增加显式生命周期、有效发生顺序和权限实例消费闭环。只有 `narrative_causal` 可实现 S1 causal connection 或触发 associative connection 的因果禁令。

## 开始前

完整阅读：

- [运行时契约](references/runtime-contract.md)
- [T1 canonical schema](../../docs/ai-novel-workflow/contracts/autonomous-v2/event-timeline.schema.json)

只使用 `scripts/run_v2.py` 进入生产路径。必须设置非空 `CODEX_THREAD_ID`，并提供同一 run 的已验收 B0、S1、W1、E1 包，以及 coordinator 发出的精确 T1 input gate。运行时会冻结上游 canonical、manifest、completion、E1 两个语义审查包、实现文件、schema 和 review protocol；任一 identity 漂移都必须失败。

## 工作边界

本技能负责：

1. 读取 S1 的全部事件需求、相邻状态转移、里程碑、故事线连接和故事义务。
2. 读取 E1 的初态支持选项、能力事实/步骤/occurrence、转移支持、连接路径、里程碑与义务 readiness。
3. 在 P2 一次性设计完整事件计划，并由独立 reviewer 审查所有确定性语义 claim。
4. 在 P3 将已审计划逐字段精确投影为 canonical 事件、命题和因果边。
5. 在 P4 加入故事线序列、连接实现、状态与信息 ledger、需求覆盖、authority、derivation 和 open items，并在写 evidence 前运行完整 provisional validation。
6. 在 P5 精确组装、封包并推进 coordinator 状态。

本技能不负责：

- 改写 S1 故事线、W1 世界规则或 E1 环境能力；
- 新建具体角色身份，或补写人物心理、对白、场景、章节与小说正文；
- 通过文本关键词猜测事实、能力、状态变化或因果关系；
- 用偶然、巧合或未密封的能力弥补上游缺口；
- 把 associative connection 偷换为因果边。

## 五阶段执行

1. `event-demand-scan`：逐对象复制 S1 `event_requirements`，并从密封 E1 canonical 重新计算 universe、capability graph 和 occurrence 三个 digest。
2. `global-timeline`：提交完整 P2 计划，包括初态原子命题与分类、支持选项选择、计划事件/命题/因果边、process subject、转移 exact cover、里程碑 bucket、连接路径、义务、occurrence cover、authority-token instance ledger，以及 lifecycle scope/contract registry。先调用 `start_t1_plan_semantic_review()`；不同 reviewer thread 必须先用 `seal_t1_review_task_output()` 封存真实任务输出及 receipt，再把该 receipt 原样交给 `submit_t1_plan_semantic_review()`。只有 candidate/request/review-task-output/review/validation 五件套完整、全部 claim 通过、零 blocking finding 且 package replay 通过才能继续。
3. `event-and-causality-model`：精确复制 P2 已冻结事件、命题和因果边，只补充属于 T1 的人类可读事件字段与 environment placement；任何计划字段漂移都失败。
4. `cross-line-state-test`：补全序列、连接 realization、obligation realization、state/information ledger、EVD coverage、authority partition、derivation 和 open items。运行时先组装完整 provisional 2.5 模型并通过全量验证，之后才允许写 P4 evidence。
5. `final-event-model`：精确组装最终模型；随后生成 validation、manifest、completion，并只读重验公开包。

每阶段使用 `submit_t1_phase()`；在已有受控会话中可用 `run_t1()` 顺序提交剩余阶段。不得回填 evidence、复用 stale review receipt，或让 Python 自动创作事件语义。

## 必须满足的硬约束

- 每个 S1 state-0 anchor 必须被原子化并完整分类。静态初态没有事件或 producer；active-process 与 connection-entry 必须有闭合 producer，并选择同一 anchor、ready、kind-compatible 的 E1 option。
- 每个 S1 相邻状态转移对应一个非空、有序、ID 唯一的原子事件跨度。跨度事件属于同一故事线、按直接因果边和严格递增世界时间连续；只有末事件是 `story_transition`，并精确提交该故事线的 before→after 状态，之前事件不得改变该故事线 subject。单事件跨度保持旧语义。S1 明确列入 milestone 的状态在末提交事件精确满足 first-arrival；未列入 milestone 的中间状态不得被要求虚构一个 milestone。
- 每个事件只能改变一个 formal subject；process 事件必须使用有限、连续、来源可追溯的 `process_state_subject_registry`。
- 每个事件声明精确 E1 capability step occurrence；环境、affordance、action、required/produced facts 必须与步骤逐字段闭合。非 root fact 必须来自严格的 producer ancestor。
- 每个 E1 occurrence requirement 遵守 min/max、distinct group 与 share policy；E1 明确归属于 direct obligation 的 occurrence，还必须落在其 `obligation_occurrence_bindings` 指定的 transition、initial option 或 connection support 事件上，不能用另一个恰好调用同一步骤的事件替代。
- authority fact 是类型，不是可消费实例。每个生产/消费 occurrence 必须映射到确定性的 token instance；single-use、multi-use、non-consumable 与 issuer/consumer scope 均须重算。
- 每个模型必须显式声明 lifecycle 是否适用；适用时，生命周期只能按 `NOT_STARTED → ACTIVE → SHUTDOWN` 推进，启动和关停各恰好一次。正式接受必须先于许可生产，许可生产必须先于启动；这两段关系只能由 `narrative_causal`、`capability_dependency` 或 `token_dependency` 的有向路径证明，并允许多跳。
- 生命周期比较以世界发生时间为主；同一发生时点必须由事件 DAG 定序。章节位置、披露位置和倒叙不改变发生顺序，因此启动后披露更早的“未启动”记忆是合法的，但启动后的当前状态不得回写 `NOT_STARTED`。
- single-use 权限除 `requires_token_instance_ids` 外还必须写入 `consumes_token_instance_ids`；事件消费声明与 authority-token instance ledger 精确互逆，且只能消费一次。
- P3 的事件 ID 集合、冻结字段、命题和因果边必须与 P2 完全相同。
- 每个 milestone bucket 只投影 S1 milestone 控制信息并完整拥有其事件；有 first-arrival、connection 或强制 occurrence 的 milestone 不得为空。
- 每个 causal connection 有连续的 predecessor/causal path、E1 endpoint steps、transfer fact 和 topology；每条跨线因果边只归一个 causal SLC。associative connection 不得拥有或暗含因果路径。
- 每个 S1 story obligation 必须恰好有一个实现；causes、requires_all、strict_before、not_before 仍绑定状态边界，first_disclosure 与 must_remain_unknown 可把目标 arrival span 内的精确事件作为 witness，并与 occurrence step 和 proposition 闭合，不能由解释文字代替。
- 每个非 optional 故事线具有单调的 `[RESP:...]` 责任链，序列最终事件同时承担 result/aftermath。通常它也提交 end-state；唯一例外是终态锚点之后仍须完成 causal SEND 的源故事线。此时终态 `story_transition` 必须仍是该线最后一个 transition-span／状态变化事件，后续只能是属于该源线的非状态 `connection_bridge`。这些 bridge 必须由 E1 `connection_path_readiness` 精确授权，按完整 `source anchor → ordered bridges → target anchor` 路径执行，并对该连接的 `transport_step_ids` 做无重复 exact cover；任何 lifecycle effect、错线／外来、重复、绕过端点、目标之后或无归属的尾随动作都失败。
- `predecessor_event_ids` 与 causal edges 双向一致，图无环，世界时间不逆行；每个 root 都有 background 责任与明确的独立/并发 timing 说明。
- 所有命题生产、需求与披露都通过 ID registry 表达；禁止扫描 prose 推断。
- 当前 2.5 的每个披露 `(event, proposition)` 必须在 P4 产生至少一个原子信息变化；该记录把接收角色槽、事件、命题、事件内可通信 E1 occurrence，以及适用的 S1 `first_disclosure`/E1 obligation occurrence 精确闭合并双向回链。无披露时才允许信息账本为空。

## 交付物

ready 包至少包含：

- `canonical/event-timeline.json`
- P1–P5 五个阶段 evidence
- P2 独立 semantic-review package 及 validation
- T1 package validation、manifest 与 completion
- 密封的 B0/S1/W1/E1 source trees 与实现目录

验收时必须调用 `validate_t1_package()` 做只读重验。它会重新验证 schema、P1 digests、P2 语义审查、P2 全计划、P3 exact projection、P4 provisional/full semantics、evidence chain、implementation freeze、manifest/completion 和 coordinator lineage。只有公开包验证为 ready 才算完成。
