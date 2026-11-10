# Q1 双上下文隔离与交付协议

## 1. 目的

Q1 只负责独立证明当前 B0、S1、W1、E1、T1、C1 是否一致、可信、
完整、可开发。Q1 不修改六个正式包，不补写故事答案，不生成 P1/H1
产物，也不把同一任务中的角色切换当作独立审查。

本协议把隔离从身份声明变成可复验事实：

1. controller 在审查前重验并冻结正式输入；
2. semantic reviewer 与 handoff evaluator 在不同受控任务、线程和物理
   工作区运行；
3. handoff evaluator 只能看到逐文件列明的白名单；
4. handoff 先封存，controller 再单向投影，semantic reviewer 最后裁决；
5. finding 的 owner、resume point 与 invalidated suffix 由 §14 router
   重算，不能由 reviewer 自报；
6. ready 与 return 使用互斥交付路径。

## 2. 正式输入与 controller 门禁

controller 只接受当前 input gate 指向的：

- B0：`author-control-baseline.json`、manifest、completion；
- S1：`storyline-architecture.json`、manifest、completion；
- W1：`world-model.json`、manifest、completion；
- E1：`environment-system.json`、manifest、completion；
- T1：`event-timeline.json`、manifest、completion；
- C1：`character-system.json`、manifest、completion。

controller 必须在其工作区外对六个正式包运行各自权威 validator，确认：

- run、baseline、lineage 完全相同；
- gate 的 upstream completion 顺序严格为
  `[S1, W1, E1, T1, C1]`；
- `active_return` 与 gate mode 合法；
- canonical、manifest、completion 和 validation 未过期；
- S1–C1 generation task/thread identities 可读取且互不冒充当前审查者。

controller 创建前还必须重算 `_implementation_paths()` 的完整 catalog。每项封存稳定
identity、仓库内 source path 与 raw SHA-256，并对排序后的完整 catalog 计算 canonical
digest；完整 identity 同时写入 `frozen-inputs.json` 与每个 controller state revision。
semantic start/submit、handoff start/seal、handoff import、final review 与 `run_q1` 在任何
新文件或目录写入前都必须重算 current identity 并与两处封存值逐值相等。旧 controller、
partial semantic 或 sealed handoff 不得跨 runtime、schema、SKILL 或协议变更恢复。
ready/return package 的 execution record 必须携带同一 identity；public replay 要求 catalog
无缺项、无额外项、artifact SHA 与 current source SHA 同时闭合。

T1 `2.2` 及以上同时封存规划层与 canonical 层。Q1 的对象索引只允许三组受约束的
双来源投影：`planned_event_registry → major_events`、
`planned_proposition_registry → proposition_registry`、
`planned_causal_edges → causal_edges`。事件按 T1 `_EVENT_MAP` 加
`changed_subject` 的 subject/before/after 规范化逐字段核对；命题按八个正式字段核对；
因果边必须逐值完全相等。索引代表始终取 canonical registry 的完整对象、完整值哈希和
canonical JSON Pointer，并另记唯一 planned source pointer。任一集合缺项、字段漂移、
第三来源或未列入上述三组的非精确重复均按 hard admission failure 拒绝。其他阶段及
T1 旧版本只允许值完全相同的重复对象合并来源指针。

门禁通过后冻结逐文件 path、SHA-256、stage completion、gate、run-state 和
generation identity。后续任一字节或引用变化均使本次 Q1 会话失效。legacy
D1/R1 completion、run-state 和输出不得进入该 inventory。

## 3. 两个独立执行上下文

每个动作都从当前受控环境读取 `CODEX_TASK_ID` 与 `CODEX_THREAD_ID`。
API 不接受 caller 传入或覆盖这两个值。

### 3.1 Semantic reviewer

semantic task、thread、session 必须：

- 与 handoff 三项身份不同；
- 与 S1–C1 每个 generation task/thread identity 不同；
- 在全部 semantic 阶段保持不变。

其只读输入投影允许：

- B0 canonical + manifest；
- S1–C1 canonical + manifest；
- S1–C1 generation session、evidence index 和 index 精确引用的 evidence。

禁止修改正式包、替换冻结输入、执行 handoff 任务或直接写第四阶段。

### 3.2 Handoff evaluator

handoff 工作区的 `inputs/` 必须双向精确等于以下 12 个文件：

| Stage | 允许文件 |
|---|---|
| B0 | `author-control-baseline.json`, `package-manifest.json` |
| S1 | `storyline-architecture.json`, `package-manifest.json` |
| W1 | `world-model.json`, `package-manifest.json` |
| E1 | `environment-system.json`, `package-manifest.json` |
| T1 | `event-timeline.json`, `package-manifest.json` |
| C1 | `character-system.json`, `package-manifest.json` |

不得复制整包目录。尤其禁止：

- `stage-completion.json`；
- `validation.json`；
- generation session、index 或 evidence；
- chat、访谈记录；
- semantic 计划、挑战、finding 或 final review；
- expected answer、旧 handoff 答案。

运行时比较 allowlist、实际文件树、逐文件哈希和 evidence `read_set`。任何
遗漏、额外文件、路径逃逸或哈希变化都失败。修改 role 字符串、声称清空
上下文、或测试中模拟不同 ID，不构成生产隔离。生产 `SKILL.md` 的调用者
必须真的创建独立子任务与独立工作区；测试 fixture 只验证状态机。

## 4. 固定五阶段

唯一合法顺序是：

1. `review-plan`：semantic reviewer 定义可失败的审查计划；
2. `domain-challenges`：semantic reviewer 完成五领域、真实性和覆盖重算；
3. `cross-domain-challenges`：semantic reviewer 完成跨域、因果、便捷解与
   一致性挑战，并提出 findings；
4. `development-handoff-test`：外部 handoff 已先封存，controller 只投影
   该封存 artifact，不写答案、不改 verdict；
5. `final-review`：原 semantic task/thread/session 读取第四阶段后完成最终
   review。

每阶段证据绑定 session、actor task/thread、输入 inventory、前一证据哈希和
payload 哈希。禁止跳步、重复、倒填、换 session、semantic 伪写阶段 4、
handoff 写 semantic 阶段、未封存 handoff 就 final。

## 5. Handoff 固定任务

handoff evaluator 必须仅凭白名单完成以下五项：

1. 用自己的话复述故事主体；
2. 从任一故事线追踪到其事件、环境和承担角色；
3. 定位一个主要事件的前提、触发、变化、结果和下一压力；
4. 解释核心角色关键选择受哪些目标、边界、信息与关系约束；
5. 指出开发阶段仍保留的自由以及不得改变的控制信息。

每项回答必须引用白名单中真实 object ID，并绑定当前对象值 SHA-256。
回答、结论和 result 均由 handoff Agent 提供；Python 只验证、封存和投影。

## 6. Semantic review 的最低证据

`conception-review.json` 必须严格符合公共 schema，并同时满足：

- `domain_reviews` 恰好覆盖 S1/W1/E1/T1/C1；
- cross-domain、reality、coverage、consistency、causal、
  easy-solution、development-usability 均有非空检查；
- 每个 check 的 evidence ID 存在且属于其 scope；
- 跨域检查至少绑定两个不同 stage；
- method 使用 `[VALUE_SHA256:<ID>:<digest>]` 绑定当前对象值；
- conclusion 包含可反驳、故事特定的对象或值解释；
- 泛化的“字段存在、结构完整、全部通过”不能成为 ready 证据。

Python 不生成 review、finding、verdict 或 handoff 语义。它只拒绝缺失、
不相关、模板化、伪造或过期的 Agent 输出。

## 7. Finding、唯一责任与 resolver

finding 在 `violated_contract` 中携带一个既有 contract 内的路由标记：
`[ISSUE:<issue_kind>]`。validator 用 §14 router 重算：

- storyline → S1；
- world → W1；
- environment → E1；
- event/timeline/causality/state → T1；
- character → C1；
- `DEV-` development-freedom → C1；
- review/evidence/isolation → Q1；
- author-locked control → 对应 I0–I5。

`calculated_owner` 与 `minimum_rerun` 必须与重算结果相同。若多个非 note
finding 指向不同阶段，按依赖顺序选择最早根因，router 只生成一个活动
`return-request.json`；其他 finding 仍保留。reviewer 不得自己制造 route。

修复时只有 target stage 可带 `return_resolution` completion。完成后按后缀
重跑：

- S1 → S1–H1；
- W1 → W1–H1；
- E1 → E1–H1；
- T1 → T1–H1；
- C1 → C1–H1；
- Q1 → Q1–H1。

Q1 自身缺陷必须重新运行两套独立 context。任何上游 canonical 改变后，
旧 Q1/P1/H1 completion 均不得恢复或复用。

## 8. 互斥交付

### Ready package

只在全部 checks 和 handoff 为 pass、findings 仅 note、return 为 null 时
生成：

- canonical review；
- 两套 execution record 与 controller master record；
- generation session、五阶段 evidence 和 index；
- handoff evidence；
- preview、validation、implementation snapshots；
- `independent-review` manifest；
- Q1 ready completion。

completion 必须绑定 exact gate、state-before、`[S1..C1]` completions、
manifest、validation、统一 session ID 和 return binding。

### Revise/blocked return bundle

必须包含经验证的 canonical review、五阶段证据、handoff evidence、
execution records、validation、router 生成并封存的 return request 和 bundle
index。不得含 package manifest 或 ready stage completion；coordinator 只能
`apply_return_request`，不得推进 Q1。

两种路径发现对方专属文件时均失败。

## 9. 必须通过的攻击

- 同 task/thread/session 伪造双审查；
- 任一 reviewer 冒充 S1–C1 generator；
- handoff 多文件、少文件、改哈希或越权引用；
- semantic 直接写第四阶段或在 handoff 前 final；
- handoff seal 后篡改；
- generic pass、假 ID、错误 scope 或旧 value hash；
- finding owner/minimum rerun 篡改；
- ready 带 return/non-note，或 return bundle 带 completion；
- 多个 active return、错误 invalidation suffix；
- 上游正式包被 reviewer 改字节；
- legacy D1/R1 completion 混入；
- 修改任一 evidence、execution、manifest 或 completion 后仍被接受。
