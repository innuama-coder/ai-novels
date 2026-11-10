## Artifact Metadata

| Field | Value |
|---|---|
| Artifact id | 03 |
| Owner skill | novel-world-rule-designer |
| Run id | 2026-07-13-duanxian-hld-workflow |
| Upstream package | final PRD package and canonical world facts v3.0 |
| Input artifacts | artifacts 01-02 |
| Output path | artifacts/03-world-rules.md |
| Version | v3.0 |

## World rule design table

| Rule id | Rule type | Design fact | Supports | Boundary | Source | LLD handoff | Amendment request |
|---|---|---|---|---|---|---|---|
| HLD-03-01 | technology | 神经残留维持仅保存死亡后72小时内的波形可读性；保护核只对承载者认可的关系叙事降低噪声。 | HLD-02-01 | 不等于复活；强刺激不能直接打开保护核。 | scene:PRD-S01,scene:PRD-S03,freeze:PRD-FREEZE-02,freeze:PRD-FREEZE-03 | LLD-RULE-01 | none |
| HLD-03-02 | protocol | R-07 由值班负责人、项目主任和操作者三方签名创建；只能访问注入记忆、会话、状态摘要和自身日志。 | HLD-02-02 | 不可读取组织网络、不可复制、不可越权控制。 | scene:PRD-S04,scene:PRD-S05,scene:PRD-S06,freeze:PRD-FREEZE-04 | LLD-RULE-02 | none |
| HLD-03-03 | data | 行动层保存审计校验串、专家与原始异常控制模块位置、攻击节点、受感染节点隔离清单、异常授权路径、攻击签名、纠偏入口和有限证词；原因层保存周岚例外、周启明、纬线利益链与私人关系。 | HLD-02-05 | 原因层不得进入即时国际归因或公开材料；模块与专家共同证明硬件植入，单独一方不得替代另一方。 | scene:PRD-S11,scene:PRD-S12,freeze:PRD-FREEZE-11,storylogic:PRD-LOGIC-01 | LLD-RULE-03 | none |
| HLD-03-04 | authority | 隔离保存窗口内，组织可审查但不能复制或接管 R-07；终止只能由操作者在风险评估与延迟复核后确认。 | HLD-02-02 | 组织压力存在，终局选择不得被组织夺走。 | scene:PRD-S13,scene:PRD-S14,scene:PRD-S15,freeze:PRD-FREEZE-14,storylogic:PRD-LOGIC-04 | LLD-RULE-04 | none |
| HLD-03-05 | security | 裂隙网络只能污染认证链和提供掩护；纬线利益链只能滥用遗留紧急授权，在既有强对流天气带上实施局地干预；R-07只能重排自身可见日志。 | HLD-02-06 | 任何一方不得凭空制造天气、控制政府、伪造权限或改写审计记录。 | scene:PRD-S15,scene:PRD-S16,freeze:PRD-FREEZE-13,storylogic:PRD-LOGIC-03 | LLD-RULE-05 | none |

## HLD Fact Trace

| Fact trace id | Upstream fact id | Upstream fact atom | HLD fact atom | Source refs | Expansion mode | Support mechanism | Preservation status |
|---|---|---|---|---|---|---|---|
| HLD-03-01 | UPF-PRD-S03-01 | 关键记忆完全自闭。 | Rule type technology；Design fact 神经残留维持72小时和关系叙事保护核；Supports HLD-02-01；Boundary 不等于复活且强刺激无效；LLD handoff LLD-RULE-01；Amendment request none。 | scene:PRD-S01,scene:PRD-S03,freeze:PRD-FREEZE-02,freeze:PRD-FREEZE-03 | explain | 读取失败机制。 | bounded_expansion |
| HLD-03-02 | UPF-PRD-S04-01 | 数字生命方案成为唯一可执行候选。 | Rule type protocol；Design fact 三方签名与受限访问；Supports HLD-02-02；Boundary 不可复制越权；LLD handoff LLD-RULE-02；Amendment request none。 | scene:PRD-S04,scene:PRD-S05,scene:PRD-S06,freeze:PRD-FREEZE-04 | permission | 注入责任机制。 | bounded_expansion |
| HLD-03-03 | UPF-PRD-S12-01 | 处理后的情报。 | Rule type data；Design fact 行动层与原因层包含字段；Supports HLD-02-05；Boundary 原因层不公开；LLD handoff LLD-RULE-03；Amendment request none。 | scene:PRD-S11,scene:PRD-S12,freeze:PRD-FREEZE-11,storylogic:PRD-LOGIC-01 | constrain | 报告边界。 | bounded_expansion |
| HLD-03-04 | UPF-PRD-S13-01 | 重大事件被化解，组织进入结案审查。 | Rule type authority；Design fact 保存窗口限制组织接管；Supports HLD-02-02；Boundary 终局选择不被夺走；LLD handoff LLD-RULE-04；Amendment request none。 | scene:PRD-S13,scene:PRD-S14,scene:PRD-S15,freeze:PRD-FREEZE-14,storylogic:PRD-LOGIC-04 | constrain | 制度压力。 | bounded_expansion |
| HLD-03-05 | UPF-PRD-S15-01 | 数字生命体决定设计自己的终止。 | Rule type security；Design fact 裂隙网络与R-07的能力边界；Supports HLD-02-06；Boundary 无天气国家系统权限审计控制；LLD handoff LLD-RULE-05；Amendment request none。 | scene:PRD-S15,scene:PRD-S16,freeze:PRD-FREEZE-13,storylogic:PRD-LOGIC-03 | constrain | 终止能力边界。 | preserved |

## Skill Verdict

| Field | Value |
|---|---|
| Skill quality verdict | pass |
| Source closure | closed |
| Inventory coverage | not_applicable |
| Boundary obedience | pass |
| Downstream readiness | ready |
| Blocking issue | none |
| Rerun target | none |
