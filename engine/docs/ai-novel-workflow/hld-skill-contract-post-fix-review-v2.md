# HLD 技能定义修复后验收 V2

> 历史中间结论：本文件已被 `hld-skill-contract-post-fix-review-v3.md` 取代。V2 关闭了隔离、发布权和状态问题，但仍遗漏跨文档契约漂移、真实 upstream 权威语义、harness-level eval 与时间戳确定性问题。

## 1. 结论

**定义级验收通过，可以进入实现；尚未实现，不能宣称运行级通过或已经能够稳定交付真实 HLD。**

当前仍为 14 个 bounded skill，主调用顺序不变。此次修复关闭了会导致假通过、状态多写、误路由和人审不可用的真实问题，没有增加领域职责，也没有把内部 harness operation 伪装成新技能。

## 2. 根因定位

| 根因 | 会造成的实际故障 |
| --- | --- |
| 隔离只限制“文件范围”，没有限制“先后上下文” | HQ2 可先看机器包答案再声称 handoff 可独立消费，形成被污染的假通过 |
| 复合 stage 只有内部 worker，没有唯一顶层发布者 | HQ2、HH1 可能由多个内部技能生成 completion，状态和交付物出现双重 owner |
| 上游权威、HLD 处理归属、review verdict 和 stage result 混用语义 | schema 看似完整，但 router 无法确定是内容返工、作者裁决还是流程错误 |
| 质量要求停留在声明，没有落到每个技能和独立人审门 | 技能可在没有负例／边界证明时发布；人审包可忠实但仍无法在十分钟内完成判断 |

## 3. 修复方案及执行前可解性检查

修复前先以定义模型验证以下条件，全部成立后才修改文件：

1. 保留 14 个技能与原主拓扑，不用增加技能解决控制面问题；
2. HQ2 可由同一技能的两个隔离 task 完成 handoff-only 消费与 package fidelity，对象职责不重叠；
3. HQ2、HH1 可由 harness core 的固定 publisher 发布顶层结果，publisher 不作语义判断、不写状态，因此不构成第 15 个技能；
4. `source_authority_refs[]` 与 `ownership_class` 可分别表达来源权威和 HLD 处理归属，映射是全定义的；
5. `pass|revise|fail` 到 `ready|revise|blocked|runtime_error` 可由 defect origin 唯一转换；
6. 14 个技能都能设置 positive、negative、boundary eval，不需要扩张其职责；
7. 人审忠实性和十分钟决策可用性可以由独立 HH1-B 同时验证，不让报告组装者自证。

可解性检查结果：**7/7 成立，方案能覆盖四个根因，允许执行修复。**

## 4. 已落地的机制

- HQ1 的产品语义 verdict 只读 canonical、manifest、completion 和确定性 validation，不读取 producer 的生成证据或自评。
- HQ2 固定为 `consumer_test → 密封 → 新上下文 fidelity_test → composite publisher`；consumer 严禁读取 package、canonical、spec、cross-index 和 traceability。
- HQ2、HH1 的内部 task 只产生内部结果；只有固定 publisher profile 可以生成顶层 completion，且 publisher 不能判断内容或写 run-state。
- Harness 是唯一 parent consumer 和唯一 run-state writer；reviewer 只给 defect origin 与 affected IDs，router 才计算 owner、return 和失效后缀。
- Canonical 同时保存原样 `source_authority_refs[]` 与独立 `ownership_class`，并使用固定映射，避免覆盖上游权威。
- Review verdict 使用固定代数转换为 stage result；未定义组合 fail closed。
- HH1-B 独立检查 material fidelity、十分钟阅读预算、固定决策问题可检索性和认知过载。
- 14 个技能各有 positive、negative、boundary eval 槽位；每个适用维度必须 2/2，不能用总分抵消 blocker。

## 5. 修复后验收

| 检查 | 结果 |
| --- | --- |
| 技能数量、名称与主设计／catalog 一致 | 14/14，通过 |
| 主调用拓扑单向、无新增领域技能 | 通过 |
| HQ2 handoff-only 与 fidelity 上下文隔离 | 通过 |
| HQ2／HH1 顶层 completion 唯一发布者 | 通过 |
| Harness 唯一状态写入者 | 通过 |
| 权威继承与 HLD ownership 分层且映射完整 | 通过 |
| Review verdict → stage result 转换完整 | 通过 |
| 最终三个作者决定全部经 HF1 消费 | 通过 |
| 现实事实依赖只由 router 生成 request | 通过 |
| 14 个技能的三类 eval 与硬 Pass Bar | 14/14，通过 |
| 人审忠实性与十分钟决策可用性独立验收 | 通过 |
| 两份当前定义文件 UTF-8、无 replacement character、无残留旧规则 | 通过 |
| 当前定义文件内部相对链接 | 0 个缺失 |

## 6. 边界

本次只修复并验收了技能框架、职责、调用链和输入／交付契约。Schema、validator、skills、adapter、publisher、eval fixture 和真实 HLD 运行均属于下一阶段实现工作。只有实现通过 14 个技能的 agentic eval、端到端契约场景和真实项目验收后，才可宣称技能链能够稳定交付合格 HLD。
