# HLD 技能定义修复后验收 V3

> 历史快照：本文件已被 [`hld-skill-contract-post-fix-review-v4.md`](hld-skill-contract-post-fix-review-v4.md) 取代。V3 的“可进入实现”结论不再代表当前定义状态。

## 1. 结论

**定义级验收通过，可以进入实现；不代表 schema、validator、技能、adapter、eval 或真实运行已经完成。**

本轮保持 14 个技能和既定调用拓扑不变，修复的是会导致权限误判、错误消费、不可复现或假验收的契约问题，没有扩张 HLD 的业务边界。

## 2. 根因

共同根因是：同一实现契约在主设计、技能目录、矩阵和验收段落中被重复定义，却没有唯一规范源和跨文档一致性门。由此产生六类实际问题：

1. HQ1 的原始权威读取权限在 source matrix 与输入 allowlist 中互相冲突；
2. 上游 `classification`、独立 `open_item`、上游 `authority_class` 和 HLD `ownership_class` 被混成一套枚举；
3. `downstream_freedom` 被错误地直接解释成 `lld_freedom`，与真实 development baseline 契约不符；
4. 生产者—消费者矩阵使用未注册同义字段，并漏列 HF1 对 HH1 的依赖及 HF1 最终产物；
5. bounded-skill eval 与 harness-level eval 被合并，导致整链编排、adapter 和 release 没有独立验收；
6. 确定性 script 要求字节一致，但 `produced_at` 由运行时生成，合同自相矛盾。

## 3. 动手前的方案验证

在修改定义前，先用只读检查确认：

- 真实 upstream schema 的主分类确为 `mandatory|freedom|must_ask|open`；
- `open_item` 是独立标志，`authority_class` 是另一字段；
- upstream runtime 明确规定 `classification=freedom` 允许 HLD 决定；
- 四层权威数据可以用互斥字段建模，不需要改变 upstream；
- HQ1 可以读取 source index 授权的权威对象，同时禁止 producer rationale；
- 14 技能 eval 与整链 eval 可以使用不同 Pass Bar 且互不替代；
- 固定时间戳可由 work order 预签发，不需要放弃确定性；
- 全部修复不增加技能、不改变主拓扑。

预检全部通过后才执行修改。

## 4. 已落地的修复

- 技能目录成为字段、artifact role、输入顺序、source access、verdict 和包 profile 的唯一实现契约；主设计不得另造同义字段。
- HQ1 读取经 HB0 source index 授权且重新验证 hash 的原始权威对象，但禁止读取 generation evidence、execution 和 producer self-review。
- `authority_partition` 固定拆为 `source_classifications / source_open_items / source_authority_classes / hld_ownership`，并定义集合不变量。
- `classification=freedom` 根据 HLD 当前责任决定 `hld_owned` 或有证据的 `lld_freedom`；上游 `downstream_freedom` 不再自动下推至 LLD。
- HA1–HK1 的设计元素与 HQ1/HQ2/HH1 的评审证据元素分开；评审证据禁止携带 `ownership_class` 或故事设计权威。
- 生产者—消费者矩阵统一使用 catalog 已注册 role／字段，补齐所有声明消费者、HH1 publisher 和 HF1 最终消费者。
- 最终交付物分为机器内容权威、验收审计证据、人审包和最终闭合包；审查文件不再冒充故事内容权威。
- 中途 author question 与最终 author decision 完全分离；`external_author_request` 只允许 HF1 投影最终 revise。
- Bounded-skill eval 要求适用维度全部 2/2；harness-level eval 另设 positive／negative／boundary 三类 case 和七维 12/14 Pass Bar。
- 定义 portable core、Codex adapter 和 release contract，使 harness-level adapter／release 评测有可验证对象。
- Work order 预签发 `event_sequence/result_timestamp`，skill 逐值复制，真实接收时间只写入后续 run-state。

## 5. 修复后验收结果

| 检查 | 结果 |
| --- | --- |
| 14 个技能名称与主设计／catalog 一致 | 通过 |
| 主拓扑与 skill 数量保持不变 | 通过 |
| Catalog 唯一规范源与跨文档引用 | 通过 |
| 与真实 upstream baseline enum／flag／authority 兼容 | 通过 |
| 四层权威字段与集合不变量 | 通过 |
| HQ1 独立性与 source access 一致 | 通过 |
| Artifact role 与主设计字段全部已注册 | 通过 |
| Producer／consumer／HF1 依赖闭合 | 通过 |
| 中途与最终作者事务互斥 | 通过 |
| Script／publisher 时间字段可复现 | 通过 |
| 机器内容与验收证据不混权威 | 通过 |
| 14 个 bounded-skill eval | 14/14，通过 |
| 3 个 harness-level eval 及 12/14 Pass Bar | 通过 |
| Codex adapter 与 release 定义边界 | 通过 |
| 相对链接、UTF-8、尾随空白 | 通过 |

## 6. 剩余边界

下一阶段只能依据当前定义开发 portable core、schema、validator、14 个技能、两个 composite publisher、Codex adapter、eval fixtures 和 release tooling。实现必须重新执行 V3 中的全部静态检查、bounded-skill eval、harness-level eval、端到端契约场景和真实《断线》运行，才能声称 HLD 技能链稳定可交付。
