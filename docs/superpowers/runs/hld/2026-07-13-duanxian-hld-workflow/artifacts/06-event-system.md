## Artifact Metadata

| Field | Value |
|---|---|
| Artifact id | 06 |
| Owner skill | novel-event-system-designer |
| Run id | 2026-07-13-duanxian-hld-workflow |
| Upstream package | final PRD package and canonical world facts v3.0 |
| Input artifacts | artifacts 01-05 |
| Output path | artifacts/06-event-system.md |
| Version | v3.0 |

## Event system table

| Event id | Inventory id | Entity type | Entity name | Event type | Visibility | Cause refs | Event action | Causal role | Participants | Environment refs | Environment state change refs | Environment state transitions | Environment state realizations | Consequences | Supports | Source | LLD handoff | Amendment request |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| HLD-06-01 | HLD-01-12 | event | 酒店交接袭击 | trigger | partial | none | 顾衡确认认证链被渗透后在709遭袭，原始交接中断。 | 切断正常情报路径。 | HLD-04-02 | HLD-05-01 | ENV-STATE-01 | ENV-STATE-01:PRIVATE_WAIT=>SEALED_SCENE | ENV-STATE-01 [access]: 709由私密等待变为封控现场。 | 顾衡死亡，保护核成为最后入口。 | HLD-02-04 | scene:PRD-S00,freeze:PRD-FREEZE-01,claim:CLAIM-10 | LLD-EVENT-01 | none |
| HLD-06-02 | HLD-01-13 | event | 常规读取失败 | revelation | visible | HLD-06-01 | 维持系统显示外围可读而保护核自闭，常规刺激失败。 | 证明需要R-07而非继续强读。 | HLD-04-01,HLD-04-05 | HLD-05-02 | ENV-STATE-02 | ENV-STATE-02:MEDICAL_PRIORITY=>COGNITIVE_HOLD | ENV-STATE-02 [authority]: 实验室由医疗优先转为受限认知维持。 | 注入方案成为唯一候选。 | HLD-02-04 | scene:PRD-S02,scene:PRD-S03,freeze:PRD-FREEZE-02,freeze:PRD-FREEZE-03,claim:CLAIM-02 | LLD-EVENT-02 | none |
| HLD-06-03 | HLD-01-14 | event | D+57救援与防御纠偏 | reversal | hidden | HLD-06-02 | R-07协助沈逾有限打开行动层；C/M救出专家、交叉验证并纠正调度。 | 将可用情报变成可验证结果。 | HLD-04-01,HLD-04-03,HLD-04-06 | HLD-05-04,HLD-05-05 | ENV-STATE-04,ENV-STATE-05 | ENV-STATE-04:MONITORED_DIALOGUE=>TERMINATION_PENDING;ENV-STATE-05:COMPROMISED_ROUTING=>CROSS_VERIFIED_ROUTING | ENV-STATE-04 [risk]: 原因层解锁令保存风险上升；ENV-STATE-05 [dispatch]: 联络台改用独立核验调度。 | D+58攻击失去破坏会面的条件，原因层仍受限。 | HLD-02-04 | scene:PRD-S11,scene:PRD-S12,freeze:PRD-FREEZE-07,freeze:PRD-FREEZE-11,claim:CLAIM-06 | LLD-EVENT-03 | none |
| HLD-06-04 | HLD-01-15 | event | R-07终止确认 | decision | implied | HLD-06-03 | R-07重排已有风险告警；沈逾在延迟复核后完成双重确认。 | 终止原因层的不可复制入口。 | HLD-04-01,HLD-04-03 | HLD-05-04 | ENV-STATE-04 | ENV-STATE-04:MONITORED_DIALOGUE=>TERMINATION_PENDING | ENV-STATE-04 [risk]: 终止界面从受监控会话进入待确认状态。 | 行动层仍存，R-07离开，沈逾承担秘密。 | HLD-02-06 | scene:PRD-S15,scene:PRD-S16,freeze:PRD-FREEZE-09,freeze:PRD-FREEZE-13,claim:CLAIM-08 | LLD-EVENT-04 | none |
| HLD-06-05 | HLD-01-30 | event | D+26专家劫持 | escalation | visible | HLD-06-01 | 裂隙网络伪装C国人员劫持首席安全认证师并夺走原始异常控制模块。 | 切断网络渗透物证，制造C国嫌疑和M国领导层的报复压力。 | HLD-04-07,HLD-04-08,HLD-04-09 | HLD-05-06 | ENV-STATE-06 | ENV-STATE-06:HIDDEN_CUSTODY=>JOINT_RESCUE | ENV-STATE-06 [custody]: 专家与模块由隐匿囚禁等待D+57救援。 | 会面受损；M国无法确认备用节点是否同样被渗透，媒体、金融和承包利益推动报复叙事。 | HLD-02-04 | scene:PRD-S11,scene:PRD-S12,claim:CLAIM-06 | LLD-EVENT-05 | none |
| HLD-06-06 | HLD-01-31 | event | D+58报复性气象攻击失效 | consequence | visible | HLD-06-03,HLD-06-05 | 纬线利益链滥用紧急授权，在既有强对流天气带上启动局地干预；专家与模块已定位受感染节点，C国防御完成纠偏。 | 使两国从竞争滑向战争边缘，又证明行动层足以阻断升级。 | HLD-04-06,HLD-04-08,HLD-04-09 | HLD-05-05 | ENV-STATE-05 | ENV-STATE-05:COMPROMISED_ROUTING=>CROSS_VERIFIED_ROUTING | ENV-STATE-05 [dispatch]: 独立核验调度提前吸收攻击风险。 | 城市未陷入灾害；真实M国技术签名不能再被直接当作最高层战争决定。 | HLD-02-04 | scene:PRD-S11,scene:PRD-S12,claim:CLAIM-06 | LLD-EVENT-06 | none |

## HLD Fact Trace

| Fact trace id | Upstream fact id | Upstream fact atom | HLD fact atom | Source refs | Expansion mode | Support mechanism | Preservation status |
|---|---|---|---|---|---|---|---|
| HLD-06-01 | UPF-PRD-S00-02 | 关键情报未能正常交接。 | Inventory id HLD-01-12；Entity type event；Entity name 酒店交接袭击；Event type trigger；Visibility partial；Cause refs none；Event action 709遭袭中断交接；Causal role 切断路径；Participants HLD-04-02；Environment refs HLD-05-01；Environment state change refs ENV-STATE-01；Environment state transitions ENV-STATE-01:PRIVATE_WAIT=>SEALED_SCENE；Environment state realizations ENV-STATE-01 [access]: 709由私密等待变为封控现场；Consequences 顾衡死亡保护核成为入口；Supports HLD-02-04；LLD handoff LLD-EVENT-01；Amendment request none。 | scene:PRD-S00,freeze:PRD-FREEZE-01,claim:CLAIM-10 | sequence | 断线触发。 | bounded_expansion |
| HLD-06-02 | UPF-PRD-S03-01 | 关键记忆完全自闭。 | Inventory id HLD-01-13；Entity type event；Entity name 常规读取失败；Event type revelation；Visibility visible；Cause refs HLD-06-01；Event action 外围可读保护核失败；Causal role 需要R-07；Participants HLD-04-01,HLD-04-05；Environment refs HLD-05-02；Environment state change refs ENV-STATE-02；Environment state transitions ENV-STATE-02:MEDICAL_PRIORITY=>COGNITIVE_HOLD；Environment state realizations ENV-STATE-02 [authority]: 实验室由医疗优先转为受限认知维持；Consequences 注入成为候选；Supports HLD-02-04；LLD handoff LLD-EVENT-02；Amendment request none。 | scene:PRD-S02,scene:PRD-S03,freeze:PRD-FREEZE-02,freeze:PRD-FREEZE-03,claim:CLAIM-02 | explain | 读取失败。 | preserved |
| HLD-06-03 | UPF-PRD-S11-01 | 打开记忆。 | Inventory id HLD-01-14；Entity type event；Entity name D+57救援与防御纠偏；Event type reversal；Visibility hidden；Cause refs HLD-06-02；Event action 行动层救援核验纠偏；Causal role 可验证结果；Participants HLD-04-01,HLD-04-03,HLD-04-06；Environment refs HLD-05-04,HLD-05-05；Environment state change refs ENV-STATE-04,ENV-STATE-05；Environment state transitions ENV-STATE-04:MONITORED_DIALOGUE=>TERMINATION_PENDING;ENV-STATE-05:COMPROMISED_ROUTING=>CROSS_VERIFIED_ROUTING；Environment state realizations ENV-STATE-04 [risk]: 原因层解锁令保存风险上升；ENV-STATE-05 [dispatch]: 联络台改用独立核验调度；Consequences D+58失效原因层受限；Supports HLD-02-04；LLD handoff LLD-EVENT-03；Amendment request none。 | scene:PRD-S11,scene:PRD-S12,freeze:PRD-FREEZE-07,freeze:PRD-FREEZE-11,claim:CLAIM-06 | sequence | 危机化解。 | bounded_expansion |
| HLD-06-04 | UPF-PRD-S15-01 | 数字生命体决定设计自己的终止。 | Inventory id HLD-01-15；Entity type event；Entity name R-07终止确认；Event type decision；Visibility implied；Cause refs HLD-06-03；Event action 重排已有告警并双重确认；Causal role 终止原因层入口；Participants HLD-04-01,HLD-04-03；Environment refs HLD-05-04；Environment state change refs ENV-STATE-04；Environment state transitions ENV-STATE-04:MONITORED_DIALOGUE=>TERMINATION_PENDING；Environment state realizations ENV-STATE-04 [risk]: 终止界面从受监控会话进入待确认状态；Consequences 行动层仍存R-07离开；Supports HLD-02-06；LLD handoff LLD-EVENT-04；Amendment request none。 | scene:PRD-S15,scene:PRD-S16,freeze:PRD-FREEZE-09,freeze:PRD-FREEZE-13,claim:CLAIM-08 | constrain | 终局主体性。 | preserved |
| HLD-06-05 | UPF-PRD-S11-01 | 打开记忆并化解重大事件。 | Inventory id HLD-01-30；Entity type event；Entity name D+26专家劫持；Event type escalation；Visibility public；Cause refs HLD-06-01；Event action 伪装C国人员劫持专家；Causal role 制造互信危机；Participants HLD-04-07,HLD-04-08；Environment refs HLD-05-06；Environment state change refs ENV-STATE-06；Environment state transitions ENV-STATE-06:HIDDEN_CUSTODY=>JOINT_RESCUE；Environment state realizations ENV-STATE-06 [custody]: 专家等待D+57救援；Consequences 会面筹备暂停攻击获得放大器；Supports HLD-02-04；LLD handoff LLD-EVENT-05；Amendment request none。 | scene:PRD-S11,scene:PRD-S12,claim:CLAIM-06 | sequence | 第一伪旗。 | bounded_expansion |
| HLD-06-06 | UPF-PRD-S12-01 | 处理后的情报。 | Inventory id HLD-01-31；Entity type event；Entity name D+58报复性气象攻击失效；Event type consequence；Visibility visible；Cause refs HLD-06-03,HLD-06-05；Event action 局地气象攻击因纠偏失效；Causal role 证明行动层有效；Participants HLD-04-06,HLD-04-07；Environment refs HLD-05-05；Environment state change refs ENV-STATE-05；Environment state transitions ENV-STATE-05:COMPROMISED_ROUTING=>CROSS_VERIFIED_ROUTING；Environment state realizations ENV-STATE-05 [dispatch]: 独立核验调度吸收风险；Consequences 城市未灾害指纹不能归因；Supports HLD-02-04；LLD handoff LLD-EVENT-06；Amendment request none。 | scene:PRD-S11,scene:PRD-S12,claim:CLAIM-06 | sequence | 非法报复失效。 | bounded_expansion |

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
