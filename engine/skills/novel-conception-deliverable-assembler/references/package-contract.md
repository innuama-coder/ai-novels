# P1 确定性机器构思包契约

## Gate-authoritative upstream roots

P1 consumes B0 through Q1 from roots derived from its sealed gate, not from
caller-selected flat directories. Each completion must equal the gate
reference, and its manifest and validation must be hash-bound same-parent
logical and physical siblings. Generation and public replay use the same
check. Attempt-qualified logical references may map to Windows extended
workspace roots; unique flat legacy roots remain supported.

## Projection-aware Q1 quality admission

For T1 schema 2.2 through 2.5, P1 recomputes Q1 quality targets with the same
narrow projection pairs used by the sealed review: planned events map to major
events through the event-field map and changed-subject normalization; planned
propositions map through the formal proposition fields; planned causal edges
equal canonical edges exactly. The two registries in each pair must have exact,
internally unique ID sets. Their six top-level registries are excluded from the
remaining recursive index, while a third source, missing counterpart, or field
conflict fails closed. P1 then requires both Q1 `required_objects` and the
covered-object projection to equal that recomputed universe value-for-value.
For T1 2.5 only, the event projection additionally binds
`consumes_token_instance_ids` and `lifecycle_effects`; changing either side
fails closed before the canonical representative is hashed. T1 2.2 through
2.4 keep their frozen projection field set and do not require those 2.5-only
fields, so their canonical representative bytes and hashes remain unchanged.
T1 schema 2.0 and 2.1 retain the legacy recursive-ID rule.

## Schema/path-aware cross-model identities

`cross-model-index.json` is built only from explicit identity and reference
descriptors. P1 never infers a reference merely because a field ends in
`_id` or `_ids`. Each descriptor fixes the source JSON path and the allowed
target stage/kind. S1 line-claim `claim_id` values are alternate identities of
their authority records; C1 `slot_resolution.slot_id` values are character-slot
identities; E1 operational actor slots form a separate identity domain; T1
capability occurrences and authority-token instances are ledger identities.
Semantic-review claim/session/task IDs remain local technical provenance and
are not story cross-references. Missing definitions, wrong-stage or wrong-kind
shadows, and duplicate typed identities fail closed.

## Projection-aware author-open items

Open-item IDs remain stage-local except for the narrow S1-to-T1 preservation
projection. P1 may collapse one same-ID pair only when S1 and T1 each define
it exactly once, both records remain `author_open`, their non-empty
`source_ids` match exactly and resolve only to B0 `author_open` controls, and
the T1 question is exactly `Preserved author-open item.`. Q1 must contain the
current full-object hash for both the S1 obligation and T1 realization in both
`required_objects` and `covered_objects`. P1 emits the complete S1 record as
the canonical open item. A third-stage occurrence, same-stage duplicate,
source/status/question drift, stale Q1 hash, or missing Q1 side fails closed.
This output projection does not merge the distinct S1 and T1 definitions in
`cross-model-index.json`.

## 1. 单一职责

P1 只把当前 B0、S1、W1、E1、T1、C1、Q1 组装、索引、渲染并封包。
它不生成故事事实，不改写或修复上游，不新增摘要性权威结论，不写片段或
HTML，也不代替作者批准。发现上游问题时停止；P1 只能修复自己的组装、
索引、渲染或 manifest 问题。

## 2. 输入硬门

运行时必须重新执行七个正式包的权威 validator，并逐值确认：

- B0 与 S1–Q1 completion、manifest、canonical 都是当前文件；
- run ID、baseline 与 lineage 相同；
- Q1 `status=verdict=ready`、全部检查通过、无 actionable finding、
  `return_request=null`；
- Q1 `quality_coverage` 的 required/covered 与当前 S1/T1 全部带 ID canonical
  对象逐项、逐哈希一致，且未解决阻断质量记录为空；P1 必须独立重算；
- P1 gate 的 upstream 精确为 `[S1,W1,E1,T1,C1,Q1]`；
- gate 仅允许 `forward`，或 active return 的
  `resume_stage=resume_point=P1` 的 `return_resolution`；
- 不接受 legacy D1/R1 completion、非 ready Q1 或活动 Q1 return。

所有输入在组装前后都按逐文件 SHA-256 比较。P1 不得修改输入包。

## 3. 无损物化

包内必须包含：

- B0 canonical 的逐字节副本；
- B0 manifest 绑定的六份权威设计原文；
- S1–C1 五个 canonical 的逐字节副本；
- Q1 review 的逐字节副本；
- 七个正式输入包的只读快照，供独立重验；
- 六份设计原文、五模型和 Q1 review 的路径与哈希索引。

`novel-conception-package.json` 只引用上述完整值，不另写一套摘要事实。
validator 必须能从包内还原并逐字节比对 B0、六原文和五模型。

`quality_admission` 是 P1 的确定性准入回执：绑定当前 Q1 review，记录固定覆盖口径、
required/covered 数量与零未解决阻断记录。它不替代 Q1 审查，也不创造新质量判断。

## 4. package ↔ handoff 单向完整性

两文件不得互相包含对方的最终 hash：

1. canonical package 使用严格 path-only
   `{"path":"development-handoff.json"}` 定位 handoff；
2. handoff 使用完整 artifact reference 强绑定 canonical package；
3. manifest 用两个完整 artifact reference 分别绑定最终文件。

这消除不可构造的 SHA-256 自循环，同时保持 handoff 对机器包的精确版本绑定。
禁止占位 hash、规范化排除字段或跳过重验。

## 5. 确定性索引

`cross-model-index.json` 由五模型与 B0 控制表重算：

- 每个带 `id` 的对象记录 stage、JSON Pointer、kind、value SHA-256；
- 每个 `*_id`、`*_ids`、source/evidence/projection/decision/trigger 等引用
  记录来源 pointer、目标 ID 和全部定义位置；
- `run_id`、`session_id`、`task_id`、`thread_id`、`return_id` 等执行身份
  不作为故事引用；真正故事引用找不到定义时失败；
- 重复 ID 保留全部 occurrence；相同 stage+pointer 不得重复；
- 索引不得新增对象、关系或解释。

`novel-conception-package.cross_model_index` 必须与独立文件逐值相同。
`traceability-matrix.md` 是该 JSON 索引的确定性 Markdown 投影。

## 6. Authority 与开放项

P1 对 B0 控制表和 S1–C1 `authority_partition` 做集合并集：

- 同一 ID 同时落入两个 authority 类别时失败；
- author-locked、autonomous-owned、downstream-freedom、author-open 的
  ID 不得遗漏或改名；
- 五模型 open item 以完整对象去重；同 ID 不同值时失败；
- 每个 B0 author-open control 必须仍由 open item `source_ids` 覆盖。

P1 不替缺失开放项造问题文本。缺失说明上游/Q1 未满足，必须停止。

## 7. 开发交接

`development-handoff.json` 只做控制边界投影：

- `mandatory_controls`：author-locked，以及模型中可表示为 source ID 的
  author-locked/autonomous-owned 控制；
- `development_freedoms`：只投影 C1 `development_freedoms` 中定义的终端
  `DEV-*` IDs；历史阶段声明的 downstream-freedom 仍保留在 canonical
  package 的 authority 并集中，但不得进入最终开发交接；
- `must_ask`：author-open source IDs；
- `open_items`：所有开放项引用的 source IDs，并完整覆盖 `must_ask`；
- `development_entrypoint` 使用固定、与故事无关的流程指令，要求读取精确
  canonical 值。

完整模型中的自主决定仍由 canonical package 约束；P1 不把它们改写成新文案。

每个终端 `DEV-*` 必须满足以下硬约束，否则 P1 失败：

- 在 C1 `/development_freedoms/<index>` 有且只有一个完整对象定义；
- C1 `authority_partition.downstream_freedom` 与这些 `DEV-*` IDs 精确相等，
  且它们仍属于跨阶段 authority 的历史并集；
- `subject_ids` 非空且只能指向 C1 `/profiles/<index>`；
- `source_ids` 非空且全部在当前 B0/S1/W1/E1/T1/C1 模型索引中闭包；
- 泛型同名对象不能冒充 `DEV-*` 定义或角色 profile；
- 旧版 C1、非 `DEV-*` 自由、重复 ID、缺失或错误类型引用均 fail closed，
  不得通过正则过滤后静默消失。

## 8. 确定性规格

`novel-conception-spec.md` 只包含固定导航文字和 baseline、五模型、Q1 review、
cross-index、authority、open-items 的 canonical JSON fenced blocks。它不得加入
总结、推断或润色。相同输入必须产生字节一致的 JSON 和 Markdown。

## 9. 包与 completion

ready 包必须精确包含 V2 §10.5 文件、输入快照、实现快照、index 和 execution。
`assembly-execution.json` 绑定 gate、七个 completion/manifest/canonical、
全部输出与实现目录；P1 不生成 generation session/evidence。
`source-packages/` 一级目录必须精确为 B0、S1、W1、E1、T1、C1、Q1，
全文件集合必须是这七个正式快照的并集；禁止根文件、缺失阶段和 D1/R1
或其他未知阶段目录，即使攻击者重封 manifest 与 completion 也必须拒绝。
权威原文、canonical、review 与 implementation 子目录必须精确等于正式索引，
即使额外文件被写入 manifest 也必须拒绝。

manifest profile 必须为 `conception-package`，required roles 全部属于
`files`。P1 completion 绑定：

- exact manifest 与 validation；
- P1 gate 与执行前 run-state；
- `[S1,W1,E1,T1,C1,Q1]`；
- gate 的完整 return binding。

只有 coordinator 验收该 completion 后 P1 才完成。
提交顺序固定为：staging 全验、输入未变、原子发布、发布目录只读重验，
最后才调用 coordinator。原子发布发生 race 时，必须放弃本次 staging，并按第 10 节
只读重验已经占据目的地的 winner：若 winner exact-valid，且 coordinator 满足第 10
节的首次接纳或 forward persistent replay 状态，必须走同一 recovery 路径；只有
partial、tampered、stale、foreign、其他 non-exact winner 或不满足两种 coordinator
状态的 winner 才原地保留且不得接纳。coordinator 拒绝时，已验证包作为未进入 current
state 的 orphan 保留，不得伪造 transition 或不安全删除。

## 10. Exact existing crash recovery

目标 P1 目录已存在时，只允许恢复已经完整发布并与当前调用完全一致的 valid 包。
恢复路径必须先于任何 staging 或写入，并满足：

1. 使用正式 P1 validator 只读重验目录内全部产物、validation、manifest、
   completion、输入快照、执行记录和实现快照；
2. coordinator 必须精确满足下列一种状态：
   - 仍处于该 completion 记录的执行前状态，P1 尚未进入 current completion 集合；
     这是 valid non-current orphan 的首次接纳；
   - 仅对 forward 模式，已持久化 successor 的 `previous_state` 等于上述执行前状态
     引用、current P1 completion 等于既有 completion，且 successor reference path
     等于本次 `next_state_path`；这是 persistent replay；
3. 证明本次 sealed input gate 与包内执行记录逐值相等，包括 forward 或
   return-resolution 模式及完整 return binding；
4. 重新验证当前 B0–Q1 正式来源包，并证明 completion、manifest、canonical、
   baseline、lineage、文件清单和 SHA-256 与既有 P1 包绑定的来源完全相同；
5. 在调用 coordinator 前再次执行输入 TOCTOU 清单比较。

全部成立时，直接封装既有 `stage-completion.json` 并交给 coordinator；既有 P1
目录必须保持字节不变，不重新渲染、重封 manifest 或替换实现快照。返回
`P1RunReceipt.replayed=true` 表示本次调用复用了已存在的包。首次接纳时
`transition.replayed=false`；forward persistent replay 时两个 `replayed` 都为
`true`。

return-resolution completion 一旦已进入 `resolved_returns` 就严格 one-shot。
runtime 必须原样传播 `COORD_RETURN_ALREADY_RESOLVED`，不得把它转换成 persistent
replay，也不得生成新的 `P1RunReceipt`。

partial、无效、被篡改、过期、绑定其他 gate、其他执行前状态或其他来源集合的目录全部
fail closed。冲突目录原地保留供取证，不得覆盖、删除、合并或自动修复。实现快照不等于
当前 P1 实现即为 stale；因此旧执行留下的包（包括 A4 的旧实现快照）不能用于恢复，
必须保留旧目录并在新目标目录重新执行。

该协议只增加 runtime 的恢复分支与 receipt 语义，不改变
`novel-conception-package.schema.json`、`package-manifest.schema.json` 或
`stage-completion.schema.json`。

## 11. 必须拒绝

- 缺失、过期、非 ready 或 legacy Q1；
- gate 顺序错误、活动 Q1 return、伪造 P1 return；
- 上游包在组装中被改动；
- baseline、原文、canonical 或 review 的字节漂移；
- ID occurrence/reference、authority 或 open item 遗漏；
- spec/traceability 与 JSON 不一致；
- package/handoff 恢复双向 hash；
- handoff 分区互相重叠或遗漏 must-ask；
- manifest 未精确覆盖文件、role 漂移；
- completion 使用后态、旧上游或错误 return binding；
- 相同输入产生不同 canonical/Markdown；
- 任何生成式阶段证据或故事润色进入 P1。

## 12. C1 角色槽的类型化定义

`cross-model-index.json` 必须把合法 C1
`/slot_resolution/<index>` 完整对象登记为其 `slot_id` 的定义。该 occurrence
必须指向完整 resolution 对象，使用 `kind=slot_resolution`，以完整对象计算
`value_sha256`，并明确归属 C1。

定义字段 `/slot_resolution/<index>/slot_id` 本身不得再次登记为普通 reference。
所有值以 `SLOT-` 开头的引用只能解析到上述 C1 类型化 occurrence。通用对象即使
碰巧使用相同的 `id`，也不得满足、补充或遮蔽 SLOT 引用；缺少合法 C1 resolution
时必须返回 `P1_CROSS_REFERENCE_UNRESOLVED`。

非 SLOT 的 definition/reference 继续遵守通用 `id` 索引规则。
