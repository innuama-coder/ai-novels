# HQ1 执行 SOP

1. 准入：校验 work order、input gate、run/revision、stage/owner、implementation hash、完整上游拓扑和精确文件白名单；失败立即退出，不发布结果。
2. 隔离：确认 HQ1 task ID 与七个生产 task ID 均不同；只读取授权的 source lineage、HB0 和 HA1–HK1 公共交付。
3. 复验：逐个验证上游 main、manifest、completion、validation 的 hash、closed schema、ready profile、completion binding。
4. 原值验证：按照 source index 的 JSON Pointer 重新解析授权来源，并核对 value hash；不得依赖摘要替代原值。
5. HDD：把 quality-domain unresolved projection 精确重建为 HQ1 HDD；`required_now` 在 verdict 前转为 author-required blocked。
6. 对象盘点：从 HA1–HK1 canonical 收集全部属于各阶段的 HLD 对象 ID，作为覆盖全集。
7. 领域审查：按叙事架构、故事线、角色弧、信息架构、节奏连续性、关键场景功能六域分别检查；领域证据不得跨阶段冒充。
8. 跨域审查：检查主体—故事线覆盖、世界/环境/事件/角色派生、跨阶段因果与状态、悬念/冲突/节奏/关键功能。
9. 反证挑战：检查因果、资源授权、知识与 POV、时空、角色状态、选择—代价—后果、主题承载、HLD/LLD 边界。
10. 证据绑定：每条证据必须提供 stage、object ID、JSON Pointer、解析所得 actual value 和 contract anchor。
11. 判定：本地草稿/证据错误为 revise；上游内容缺陷、作者必答项、现实依赖分别为 blocked；无 finding 且全部适用检查通过才 ready。
12. 发布：运行公共入口。运行时在同级 staging 目录完成 closed-schema、manifest、completion、result 校验后原子发布；失败不得留下半成品 canonical。
13. 路由交接：blocked 只交付 finding IDs、affected IDs 和原因；Router 根据 producer registry 计算归属和最小返工点。
