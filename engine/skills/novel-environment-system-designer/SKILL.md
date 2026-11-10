---
name: novel-environment-system-designer
description: 把故事线和世界模型展开为可承载具体行动的环境、功能区、通道、权限、风险和转场条件。用于自主构思 V2 的 E1 阶段；不决定事件是否发生、人物最终选择或正文级场景细节。
---

# 小说具体环境系统设计

## 目标

让每项后续事件行为都有具体、可观察、可进入并受限制的承载环境。

## 权威契约

完整读取工作流第 3、6、14、15 节，以及：

- [E1 Schema](../../docs/ai-novel-workflow/contracts/autonomous-v2/environment-system.schema.json)；
- [E1 唯一运行契约](references/runtime-contract.md)。

### E1 2.4 capability-readiness contract

Production E1 models use schema `2.4`. Schemas `2.0` through `2.3` are legacy
read-only shapes. Public legacy acceptance requires both a trusted packaged
runtime/schema digest pair and the exact released-package identity binding its
manifest, completion, and canonical artifact; relabeled or resealed packages
are not legacy.
Version `2.0` retains its old common topology/transition/hosting shape,
version `2.1` adds E1-local topology and trigger bindings, version `2.2`
adds the E1-local structured hosting evidence envelope, and version `2.3`
corrects the downstream affordance contract. Version `2.4` adds exact S1
transition/milestone/connection/obligation universe digests, initial-anchor
support options, a global fact-step-authority DAG, occurrence contracts, and
readiness ledgers. Final submission and `run_e1()` generate only `2.4`.

Every phase must fail before evidence is written. Phase 1 proves exact S1/W1
projection, same-line pairing, and the four sealed S1 universe digests; phase 2
validates decisions, environments, and every state-0 support option; phase 3
validates every zone/topology/access/channel/hazard/transition/affordance plus
the global fact-step-authority-occurrence graph and requires an independent
authority semantic review; phase 4 validates structured hosting, all readiness
universes, and every initial-option realization and requires an independent
transition-support review; phase 5 proves exact projection of the sealed first
four phases before validating the full model.

Before phase 3, call `start_e1_authority_semantic_review()` and give the sealed
request to a distinct reviewer task. Submit complete claim verdicts and the
reviewer task receipt with `submit_e1_authority_semantic_review()`. The request
binds the session, input gate, P1/P2 evidence, candidate, S1/W1
manifest/completion, exact upstream JSON pointers/value hashes, implementation,
schema, and protocol. No P3 evidence may be written until it passes.

For phase 4, call `start_e1_hosting_semantic_review()` with the complete
candidate. Give its frozen request to an independent reviewer thread. Submit
the exact claim- and record-level verdict envelope with
`submit_e1_hosting_semantic_review()`. For schema 2.4 the review covers every
transition, connection, milestone, obligation, occurrence rule, ambient host,
and deterministic P2 initial-option claim. It must pass support-mode
sufficiency, exact source binding, boundary preservation, no-story-outcome,
and objective-occurrence checks. Only then may `submit_e1_phase()` seal
`storyline-hosting-test`.

Keep environment definitions local and executable. Do not paste complete
upstream responsibilities, trace envelopes, or foreign-line text into them.
An upstream constraint that already is a local operating rule may remain exact
in `access_rules`, `blockers`, or `hazards`; do not dump it into descriptive
fields. Hosting evidence proves provenance separately from environment prose.

`zones-and-topology` must seal each transition's structured
`trigger_bindings` and every affordance in phase 3. Bindings anchor
the forward trigger ID to real source/target S1 states and an explicit E1
topology path. Cross-line triggers require a causal S1 connection or a
`causes`/`requires_all` obligation; `requires_all` must be complete and optional
melody cannot drive required material. Final validation resolves the forward
IDs against the phase-3 affordance catalog while preserving at-least-one
affordance coverage and source-line membership for every event requirement.

Each `2.1`, `2.2`, `2.3`, or `2.4` topology edge declares `directionality` and nonempty transfer
capabilities. A cross-environment binding must traverse a direction-valid,
cycle-free path whose every edge exposes its exact non-local transport
capability; a local binding uses `local` and no path. Transition permissions
must independently cover the binding's source and target environments through
their access assignments.

The optional-line check is structural. Semantic optionality of environment
state prose remains an Agent/reviewer judgment and is not inferred by Python.

Treat `event_affordance_catalog` as a catalog of local action interfaces, not
as the T1 event-coverage ledger. Every S1 EVD must have at least one
affordance, but one EVD may have several affordances in different same-line
hosting environments. Every action named by an affordance must be present in
that environment's `allowed_actions`; never mix a local action with a foreign
one. Do not duplicate an affordance under another ID. In a shared environment,
carry only the constraints of the lines actually served by that affordance.
T1 alone gives each EVD its exact event realization.

Every 2.4 capability fact uses a closed, typed `source_anchor` with the sealed
artifact path/hash, JSON Pointer, and value hash. Story-state anchors also bind
line/state index; W1 outputs bind system-or-flow/output index; E1 initial-state
anchors bind environment/subject/state and may point only to a unique sealed P2
`state_vocabulary`, `resources`, or `access_rules` value; the subject ID is
derived from the environment, kind, pointer, and value. Facts and steps are globally inverse.
At P4, transition producer/consumer keys are recomputed from the exact
support-step fact projection before the transition/fact/step prerequisite DAG
is validated. Only S1 `causes` and `strict_before` edges create strict
ancestry; `not_before` permits the same tick and never creates a strict graph
edge. Cross-line facts must prove either a continuous sealed S1
structural-precedence path or true
incomparability; future dependencies are invalid. Authority-token producer and consumer
scopes use exact environment/affordance/action triples, and occurrence sharing
is permitted only by explicit policy. E1 proves capacity; it never states that
an S1 transition or T1 event has occurred.

For a causal connection, keep the transfer consumer local to its declared
target anchor. Do not add that transfer fact to a generic target-line step that
also supports transitions before the anchor; use a bounded endpoint step (and
an objective occurrence rule when distinctness is real). Reuse at or after the
anchor is allowed when the structured order and semantic review support it.
Both endpoint sets must be support steps for the exact declared anchors.
Obligation `direct_path` and `inherited_anchor_path` are distinct: the latter
may only inherit complete anchor support and may not add a fact, step, or
occurrence path. A direct path has nonempty step, fact, and occurrence sets;
the selected steps project exactly those facts and occurrences in both
directions through `obligation_occurrence_bindings`. Bindings are owned by one
obligation and one selected anchor support, so two obligations may reuse the
same capability step while retaining separate occurrence requirements; do not
collect unrelated global occurrences merely because they name that step.
Disclosure allow/forbid sets must not overlap. State-zero causal
endpoints are matched against the union of every realized initial-anchor
option for that storyline, independent of array order.

Each accepted authority or transition-support semantic review is a sealed
six-file package (`candidate.json`, `request.json`, `review-task-output.json`, `review.json`,
`validation.json`, `manifest.json`). Phase evidence references the manifest,
not a loose verdict file; every source is bound by artifact, JSON Pointer and
value hash, and public validation recomputes the whole review package and the
independent reviewer-task receipt.

## 唯一生产运行路径

只允许使用 `scripts/run_v2.py`。在同一 `CODEX_THREAD_ID` 中依次调用
`start_e1_session()`、按契约顺序调用 `submit_e1_phase()`、最后调用
`run_e1()`。不得跳过受控会话、倒填阶段证据、传入会话外的一次性完整候选稿，
也不得手写 validation、manifest 或 completion。`validate_e1_package()` 只用于
只读复验，不能替代上述生产调用。

## 输入硬准入

只接受当前 B0、S1、W1 completion、manifest、canonical 模型、E1 input gate 和
执行前 run-state。E1 `environment_demands` ID 集必须与 W1 交付精确相等。

## 职责

1. 从故事所需的最大空间层级向下展开环境：国家／地区、城市或聚落、机构或设施、
   建筑、房间／功能区。只定义故事实际使用的层级，不为完整而虚构无关地理。
2. 定义主要环境的范围、叙事责任、特征、感知条件和状态词汇。
3. 对承载具体事件的环境，定义情节相关的空间布局、出入口、关键设备、家具、摆设、
   装饰与感官锚点；每项细节都必须帮助行动、阻碍、人物感受、线索或转场成立。
4. 定义功能区、拓扑、出入规则、权限、资源与信息通道。
5. 定义允许行为、阻碍、风险、失败方式和允许状态转移。
6. 证明每条结构故事线阶段都有环境承载。
7. 向 T1 提供事件可用条件和转场契约。

## 边界

- 不决定事件是否发生及其结果。
- 不编写场景调度、镜头、对白或散文化氛围正文；但不得以此为由省略对情节有作用的
  空间特征、设备、家具、摆设、装饰和感官条件。
- 不修改世界规则；若 W1 无法承载需求，定向 return W1。
- 不创建人物心理或关系。

## 交付与验收

交付 `environment-system.json`、证据、validation、manifest 和 E1 completion。
ready 必须证明需求全覆盖、环境与功能区引用闭合、关键行动有 affordance、权限和资源
可执行、风险与失败真实存在、全部转场符合 W1。每个主要环境还必须能回答：它位于
哪个空间层级、长什么样、有哪些关键物件、人物能在其中做什么、什么会阻止行动、
它承载哪些故事活动；缺少任一项不得 ready。
