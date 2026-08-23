# SOP

## A. consumer_test

1. 验证 work order、input gate、HB0/HP1 身份、implementation digest、allowlist 与所有 hash。
2. 由精确 role 闭包确认 mode；发现任何生产包、canonical、spec、traceability 或呈现报告立即拒绝。
3. 只读取 handoff、handoff schema 和两个身份元数据；完整记录 actual reads。
4. 从 handoff 重建 LLD 工作顺序、依赖、进入/退出状态和启动条件。
5. 对所有 mandatory storyline、核心角色变化、关键功能/结果做全量追踪。
6. 对每个 HDF 逐章定义做消费测试，确认详细设计不需要猜测本章目标、阻力、选择、代价、章末变化与下一章连接。
7. 对每个 LWK 核对 required elaboration、LLD freedom、prohibition、POV/知识边界和 acceptance criteria。
8. 把会迫使 LLD 猜测主体信息的问题写入 `missing_guesswork`；其他实质问题写入 `findings`。
9. 完成六维对象证据、verdict/origin，交由公共运行时验证并原子发布内部包。

## B. fidelity_test

1. 重新验证准入；确认 sealed consumer 的 manifest、主文件、task id、run id、verdict 和 hash 均为当前值。
2. 验证 HP1 manifest/completion/validation 与正式包的封存关系，只读其正式产物。
3. 比较 source LWR 与 handoff LWK，验证双射与 traceability ID 集合一致。
4. 对每个 LWK/HKF obligation 检查 mandatory、open、required-elaboration、freedom、prohibition 分类。
5. 逐项检查 omission、enhancement、weakening、reclassification，并覆盖所有 LWK 和 trace record。
6. 完成六维对象证据、verdict/origin，交由公共运行时原子发布内部包。

## C. 终止与交付规则

- 准入、hash、schema、读取闭包、任务隔离、封存绑定失效：退出码 3，不保留可接受输出。
- 当前候选可本地修复：`revise/reviewer_local`，退出码 2。
- 上游、作者或现实依赖阻塞：`fail` 加精确 origin，内部结果为 blocked，退出码 2。
- 只有所有 primary test 均 pass、findings 为空且六维证据完整时才能 ready。
- 双构建字节不一致或发布中断必须回滚；不得留下半包。
