## Artifact Metadata

| Field | Value |
|---|---|
| Artifact id | 07 |
| Owner skill | novel-time-information-system-designer |
| Run id | 2026-07-13-duanxian-hld-workflow |
| Upstream package | final PRD package and canonical world facts v3.0 |
| Input artifacts | artifacts 01-06 |
| Output path | artifacts/07-time-information-system.md |
| Version | v3.0 |

## Time and information table

| Info id | Inventory id | Entity type | Entity name | PRD information boundary id | Freeze refs | Story anchor event ref | Time layer | Narrative reveal phase | Disclosure tier | Information object | Known by | Hidden from | Reveal predecessor refs | Reveal event ref | Reveal action | Reveal condition type | Reveal condition refs | Reveal condition | Supports | Source | LLD handoff | Amendment request |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| HLD-07-01 | HLD-01-19 | information object | 关键记忆保护核 | PRD-INFO-01 | freeze:PRD-FREEZE-02,freeze:PRD-FREEZE-03 | HLD-06-02 | D0—D+27 | REVEAL-01 | protected_memory | 关键记忆自闭与常规读取失败。 | HLD-04-01,HLD-04-05,reader | none | none | HLD-06-02 | 外围可读而保护核失败被记录。 | evidence_change | HLD-06-02 | 失败读数与关系指向同时出现。 | HLD-02-05 | scene:PRD-S01,scene:PRD-S03,freeze:PRD-FREEZE-02,freeze:PRD-FREEZE-03 | LLD-INFO-01 | none |
| HLD-07-02 | HLD-01-22 | information object | R-07独立主体性 | PRD-INFO-02 | freeze:PRD-FREEZE-04,freeze:PRD-FREEZE-05 | HLD-06-02 | D+27—D+56 | REVEAL-02 | institutional_assessment | 数字生命体的主体性与非顾衡身份。 | HLD-04-01,HLD-04-03,reader | HLD-04-05 | HLD-07-01 | HLD-06-03 | R-07以自身判断协助有限打开。 | action | HLD-04-03 | 它的行动不等同顾衡记忆复述。 | HLD-02-05 | scene:PRD-S06,scene:PRD-S08,freeze:PRD-FREEZE-04,freeze:PRD-FREEZE-05 | LLD-INFO-02 | none |
| HLD-07-03 | HLD-01-21 | information object | 周岚与异常授权的关联 | PRD-INFO-03 | freeze:PRD-FREEZE-06,freeze:PRD-FREEZE-12 | HLD-06-02 | D+27—D+56 | REVEAL-03 | partial_cause | 周岚写入维护例外，关联异常授权而非完整利益链。 | HLD-04-01,HLD-04-03,reader | HLD-04-05 | HLD-07-01 | HLD-06-03 | R-07沿顾衡保护逻辑说出维护例外。 | action | HLD-04-03 | 沈逾理解有人不能被立刻交出。 | HLD-02-05 | scene:PRD-S09,scene:PRD-S10,freeze:PRD-FREEZE-06,freeze:PRD-FREEZE-12 | LLD-INFO-03 | none |
| HLD-07-04 | HLD-01-20 | information object | 行动层情报 | PRD-INFO-04 | freeze:PRD-FREEZE-07,freeze:PRD-FREEZE-11 | HLD-06-03 | D+57 | REVEAL-04 | operational_intelligence | 审计校验串、专家与原始异常控制模块位置、攻击节点、受感染节点隔离清单、异常授权路径、攻击签名、纠偏入口和有限证词。 | HLD-04-01,HLD-04-03,reader | HLD-04-05 | HLD-07-03 | HLD-06-03 | 沈逾提取字段并下发行动层任务单。 | action | HLD-06-03 | M方核验校验串后救出专家与模块，二者定位节点并完成纠偏。 | HLD-02-05 | scene:PRD-S11,freeze:PRD-FREEZE-07,freeze:PRD-FREEZE-11 | LLD-INFO-04 | none |
| HLD-07-05 | HLD-01-21 | information object | 完整原因层 | PRD-INFO-05 | freeze:PRD-FREEZE-07,freeze:PRD-FREEZE-11,freeze:PRD-FREEZE-12 | HLD-06-03 | D+57—D+90 | REVEAL-05 | complete_cause | 周岚例外、周启明、纬线利益链连接、顾衡与周岚的私人关系和保护动机。 | HLD-04-01,HLD-04-03 | HLD-04-05,reader | HLD-07-04 | HLD-06-03 | 沈逾保留原因层并拒绝写入正式报告。 | permission | HLD-04-01 | 她有受限访问权且选择不导出。 | HLD-02-05 | scene:PRD-S10,scene:PRD-S13,freeze:PRD-FREEZE-07,freeze:PRD-FREEZE-11,freeze:PRD-FREEZE-12 | LLD-INFO-05 | none |
| HLD-07-06 | HLD-01-22 | information object | R-07设计终止的真实意图 | PRD-INFO-06 | freeze:PRD-FREEZE-09,freeze:PRD-FREEZE-13 | HLD-06-04 | D+59—D+90 | REVEAL-06 | private_motive | R-07终止原因层入口，是为拒绝被保存为他人资产。 | HLD-04-01,HLD-04-03,reader | HLD-04-05 | HLD-07-04 | HLD-06-04 | 沈逾复查日志识别告警排序。 | evidence_change | HLD-06-04 | 日志显示告警来自R-07可见范围内的选择。 | HLD-02-05 | scene:PRD-S15,scene:PRD-S17,freeze:PRD-FREEZE-09,freeze:PRD-FREEZE-13 | LLD-INFO-06 | none |

## HLD Fact Trace

| Fact trace id | Upstream fact id | Upstream fact atom | HLD fact atom | Source refs | Expansion mode | Support mechanism | Preservation status |
|---|---|---|---|---|---|---|---|
| HLD-07-01 | UPF-PRD-S03-01 | 关键记忆完全自闭。 | Inventory id HLD-01-19；Entity type information object；Entity name 关键记忆保护核；PRD information boundary id PRD-INFO-01；Freeze refs freeze:PRD-FREEZE-02,freeze:PRD-FREEZE-03；Story anchor event ref HLD-06-02；Time layer D0—D+27；Narrative reveal phase REVEAL-01；Disclosure tier protected_memory；Information object 关键记忆自闭与常规读取失败；Known by HLD-04-01,HLD-04-05,reader；Hidden from none；Reveal predecessor refs none；Reveal event ref HLD-06-02；Reveal action 外围可读而保护核失败被记录；Reveal condition type evidence_change；Reveal condition refs HLD-06-02；Reveal condition 失败读数与关系指向同时出现；Supports HLD-02-05；LLD handoff LLD-INFO-01；Amendment request none。 | scene:PRD-S01,scene:PRD-S03,freeze:PRD-FREEZE-02,freeze:PRD-FREEZE-03 | explain | 读取失败分层。 | preserved |
| HLD-07-02 | UPF-PRD-S06-01 | 数字生命体醒来。 | Inventory id HLD-01-22；Entity type information object；Entity name R-07独立主体性；PRD information boundary id PRD-INFO-02；Freeze refs freeze:PRD-FREEZE-04,freeze:PRD-FREEZE-05；Story anchor event ref HLD-06-02；Time layer D+27—D+56；Narrative reveal phase REVEAL-02；Disclosure tier institutional_assessment；Information object 数字生命体的主体性与非顾衡身份；Known by HLD-04-01,HLD-04-03,reader；Hidden from HLD-04-05；Reveal predecessor refs HLD-07-01；Reveal event ref HLD-06-03；Reveal action R-07以自身判断协助有限打开；Reveal condition type action；Reveal condition refs HLD-04-03；Reveal condition 它的行动不等同顾衡记忆复述；Supports HLD-02-05；LLD handoff LLD-INFO-02；Amendment request none。 | scene:PRD-S06,scene:PRD-S08,freeze:PRD-FREEZE-04,freeze:PRD-FREEZE-05 | constrain | 身份边界。 | bounded_expansion |
| HLD-07-03 | UPF-PRD-S09-01 | 被保护者线索。 | Inventory id HLD-01-21；Entity type information object；Entity name 周岚与重大事件的关联；PRD information boundary id PRD-INFO-03；Freeze refs freeze:PRD-FREEZE-06,freeze:PRD-FREEZE-12；Story anchor event ref HLD-06-02；Time layer D+27—D+56；Narrative reveal phase REVEAL-03；Disclosure tier partial_cause；Information object 周岚写入维护例外，关联双重伪旗；Known by HLD-04-01,HLD-04-03,reader；Hidden from HLD-04-05；Reveal predecessor refs HLD-07-01；Reveal event ref HLD-06-03；Reveal action R-07沿顾衡保护逻辑说出维护例外；Reveal condition type action；Reveal condition refs HLD-04-03；Reveal condition 沈逾理解有人不能被立刻交出；Supports HLD-02-05；LLD handoff LLD-INFO-03；Amendment request none。 | scene:PRD-S09,scene:PRD-S10,freeze:PRD-FREEZE-06,freeze:PRD-FREEZE-12 | support | 部分原因。 | bounded_expansion |
| HLD-07-04 | UPF-PRD-S12-01 | 处理后的情报。 | Inventory id HLD-01-20；Entity type information object；Entity name 行动层情报；PRD information boundary id PRD-INFO-04；Freeze refs freeze:PRD-FREEZE-07,freeze:PRD-FREEZE-11；Story anchor event ref HLD-06-03；Time layer D+57；Narrative reveal phase REVEAL-04；Disclosure tier operational_intelligence；Information object 专家位置攻击节点异常授权路径攻击签名纠偏入口有限证词；Known by HLD-04-01,HLD-04-03,reader；Hidden from HLD-04-05；Reveal predecessor refs HLD-07-03；Reveal event ref HLD-06-03；Reveal action 沈逾提取字段并下发任务单；Reveal condition type action；Reveal condition refs HLD-06-03；Reveal condition 救援、核验和纠偏证明字段可用；Supports HLD-02-05；LLD handoff LLD-INFO-04；Amendment request none。 | scene:PRD-S11,freeze:PRD-FREEZE-07,freeze:PRD-FREEZE-11 | handoff | 行动层。 | bounded_expansion |
| HLD-07-05 | UPF-PRD-S10-01 | 被保护者不是简单凶手。 | Inventory id HLD-01-21；Entity type information object；Entity name 完整原因层；PRD information boundary id PRD-INFO-05；Freeze refs freeze:PRD-FREEZE-07,freeze:PRD-FREEZE-11,freeze:PRD-FREEZE-12；Story anchor event ref HLD-06-03；Time layer D+57—D+90；Narrative reveal phase REVEAL-05；Disclosure tier complete_cause；Information object 周岚例外周启明纬线利益链私人关系保护动机；Known by HLD-04-01,HLD-04-03；Hidden from HLD-04-05,reader；Reveal predecessor refs HLD-07-04；Reveal event ref HLD-06-03；Reveal action 沈逾保留原因层拒绝正式报告；Reveal condition type permission；Reveal condition refs HLD-04-01；Reveal condition 她有受限访问权且选择不导出；Supports HLD-02-05；LLD handoff LLD-INFO-05；Amendment request none。 | scene:PRD-S10,scene:PRD-S13,freeze:PRD-FREEZE-07,freeze:PRD-FREEZE-11,freeze:PRD-FREEZE-12 | constrain | 原因层。 | bounded_expansion |
| HLD-07-06 | UPF-PRD-S17-01 | 终止前日志揭示主体选择。 | Inventory id HLD-01-22；Entity type information object；Entity name R-07设计终止的真实意图；PRD information boundary id PRD-INFO-06；Freeze refs freeze:PRD-FREEZE-09,freeze:PRD-FREEZE-13；Story anchor event ref HLD-06-04；Time layer D+59—D+90；Narrative reveal phase REVEAL-06；Disclosure tier private_motive；Information object R-07终止原因层入口；Known by HLD-04-01,HLD-04-03,reader；Hidden from HLD-04-05；Reveal predecessor refs HLD-07-04；Reveal event ref HLD-06-04；Reveal action 沈逾复查日志识别告警排序；Reveal condition type evidence_change；Reveal condition refs HLD-06-04；Reveal condition 日志显示告警来自R-07可见范围；Supports HLD-02-05；LLD handoff LLD-INFO-06；Amendment request none。 | scene:PRD-S15,scene:PRD-S17,freeze:PRD-FREEZE-09,freeze:PRD-FREEZE-13 | handoff | 终止动机。 | bounded_expansion |

## Skill Verdict

| Field | Value |
|---|---|
| Skill quality verdict | pass |
| Source closure | closed |
| Inventory coverage | closed |
| Boundary obedience | pass |
| Downstream readiness | ready |
| Blocking issue | none |
| Rerun target | none |
