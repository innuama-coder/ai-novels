# HLD 技能定义根因修复与验收 V4

## 1. 工作边界

本轮只修复 HLD harness 与14个 bounded skill 的**定义和契约**，没有开发 schema、validator、技能、adapter、eval fixture 或运行时包，也没有执行真实小说 HLD。

规范源仍为：

- [`hld-autonomous-workflow-v1-design.md`](hld-autonomous-workflow-v1-design.md)：目标、边界、流程和人类可读规则；
- [`hld-skill-contract-catalog-v1.md`](hld-skill-contract-catalog-v1.md)：字段、包、输入顺序、owner、verdict、return 和 eval 的唯一实现契约。

## 2. 根本原因

四个问题共享同一个根因：**控制面语义没有被分配给唯一 owner，导致流程只能依赖实现者临时解释**。

1. 开放问题的语义处置被放在 HA1 准入前，但 HB0、Harness 和上游 baseline 都不能合法产生它；
2. Return 只描述一个 target，没有描述一次 finding／作者返工事务中的多个 target；
3. 内容包、内部任务包、top-level completion 和 work-order result envelope 没有分层；
4. Eval 有案例方向，但没有统一 bounded-skill 评分维度和专门覆盖上述控制事务的回归 case。

## 3. 动手前的解决方案验证

在修改定义前，用五条路径验证方案不会改变14技能主拓扑：

| 场景 | 验证结果 |
| --- | --- |
| 无 unresolved source 的正常链 | `unresolved_projection=[]`，HA1–HK1 正常形成 canonical，HQ1/HP1 不增加额外故事判断 |
| HC1 依赖一个 must-ask | HC1 在 candidate 前生成 `required_now` HDD 并 blocked；外部 resolution 后从 HC1 新 revision 恢复 |
| 全链不依赖的 open item | 各被投影 stage 分别声明 `not_needed_for_current_stage`；HQ1 验证覆盖，HP1 才能聚合为 HLD 层状态，open item 不消失 |
| 作者同时要求修改 HS1 与 HH1-C | Router 建立两个有序 target group；HS1 先处理，HH1-C 要求持久化，随后在其 owner stage 消费 |
| 上游修改令旧 HUI target 消失 | Group 进入 superseded；外部 `revision_retarget` 只重绑 target，不回写 immutable plan，也不静默完成 |

复合 stage 另做早停推演：HQ2 consumer fail 时不签发 fidelity task；HH1-A/B fail 时不伪造后续包；publisher 逐字节包装第一个 non-ready internal result，Router 只消费 top-level result。

以上路径均可在不新增 bounded skill、不允许越权判断、不跨 workspace 猜文件的前提下闭合，才开始修改定义。

## 4. 已执行的修复

### 4.1 开放问题

- HB0 只登记 unresolved register；Harness 只按固定 domain matrix 投影；
- HA1–HK1 在候选前生成 non-quality `HDD-`；HQ1 在 verdict 前生成 quality-domain `HDD-`；
- `required_now` 不得产生 candidate／review verdict；
- HQ1 检查全链 HDD 覆盖，HP1 只确定性生成 `unresolved_dependency_summary[]`；
- Handoff 顶层携带 summary、preserved open items 和 resolution refs。

### 4.2 多目标返工

- Router 唯一生成 immutable `revision-plan.json`；
- 可变状态进入追加式 `revision-plan-state/revision-NNN.json`；
- 每个 finding/author target 独立成组，由 ID 唯一求 owner，再按拓扑和 source order 排序；Router 不做语义合并；同时只有一个 active group，其余 pending 持久化；
- Superseded target 使用 `question_kind=revision_retarget`，保持 request-meaning hash；
- Root-cause fingerprint 使用规范 JSON 的确定性 SHA-256；
- 失效后缀由最早 target 决定，HTML-only 不重跑 HP1/HQ2，但当前 HH1、作者门和 HF1 始终重做。

### 4.3 包与结果信封

- `stage-result.json` 固定为内容包外的唯一 parent-consumption envelope；
- Top-level ready 使用 completion，composite-internal ready 使用 internal manifest；
- HQ1、HQ2 internal、HH1-A/B/C 均有精确 package profile；
- Composite non-ready 由 publisher byte-copy internal package/result 后生成 top-level result；
- `render-target-registry.json` 使 `HUI-` 作者 target 可以确定性路由。

### 4.4 Eval

- 14个技能的 P/N/B case 固定六维评分，全部维度必须 2/2；
- Fixture 必须在执行前密封并声明唯一缺陷注入；
- Harness 除 P01/N01/B01 外，新增 HDD 回归 R01 和跨层多目标返工 R02。

## 5. 定义级验收

| 检查 | 结果 |
| --- | --- |
| 14个技能数量和固定主拓扑未改变 | 通过 |
| Upstream classification／authority enum 与真实 baseline schema 一致 | 通过 |
| Unresolved source 从投影、HDD、作者事务到 HP1 聚合闭合 | 通过 |
| 多 owner target 不丢失，plan 与 plan-state 不混写 | 通过 |
| HTML/report/source target 均有稳定 ID 和唯一 owner 路由 | 通过 |
| Top-level/internal、ready/non-ready 包和结果信封可区分 | 通过 |
| Composite early-stop 不要求伪造未执行任务 | 通过 |
| Bounded eval 六维与 R01/R02 已冻结 | 通过 |
| UTF-8、尾随空白和关键跨文档术语检查 | 通过 |

## 6. 结论

**定义级 blocker 已消除，可以进入实现。**

这只表示实现者不再需要为上述控制事务自行发明规则。只有 portable core、schema、validator、14个技能、两个 publisher、Codex adapter、全部 eval 和真实《断线》HLD 运行均通过后，才可以声称技能链已经稳定交付合格 HLD。
