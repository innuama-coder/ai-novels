## Artifact Metadata

| Field | Value |
|---|---|
| Artifact id | 05 |
| Owner skill | novel-environment-system-designer |
| Run id | 2026-07-13-duanxian-hld-workflow |
| Upstream package | final PRD package and canonical world facts v3.0 |
| Input artifacts | artifacts 01-04 |
| Output path | artifacts/05-environment-system.md |
| Version | v3.0 |

## Environment system table

| Environment id | Inventory id | Entity type | Entity name | Environment type | Function | Spatial relation | State change id | State change dimension | State before | State after | State change | Supports | Source | LLD handoff | Amendment request |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| HLD-05-01 | HLD-01-07 | environment | 城北商务酒店709 | incident_room | 固定D0交接失败的私人尺度。 | 位于会展区边缘，顾衡原定与接头人会面。 | ENV-STATE-01 | access | PRIVATE_WAIT | SEALED_SCENE | ENV-STATE-01 [access]: PRIVATE_WAIT=>SEALED_SCENE | HLD-02-01 | scene:PRD-S00,freeze:PRD-FREEZE-01,hldreq:HLD-REQ-01,claim:CLAIM-10 | LLD-ENV-01 | none |
| HLD-05-02 | HLD-01-08 | environment | 生命维持实验室 | medical_interface | 呈现死亡已发生而任务未结束。 | 与抢救室由玻璃隔断相连，病床可直接推入采集区。 | ENV-STATE-02 | authority | MEDICAL_PRIORITY | COGNITIVE_HOLD | ENV-STATE-02 [authority]: MEDICAL_PRIORITY=>COGNITIVE_HOLD | HLD-02-01 | scene:PRD-S01,scene:PRD-S02,hldreq:HLD-REQ-02,claim:CLAIM-01 | LLD-ENV-02 | none |
| HLD-05-03 | HLD-01-09 | environment | 临时授权室 | protocol_room | 落实三方签名与责任。 | 紧邻实验室，门外可见维持床状态屏。 | ENV-STATE-03 | protocol | DISPUTED | EXECUTABLE | ENV-STATE-03 [protocol]: DISPUTED=>EXECUTABLE | HLD-02-02 | scene:PRD-S04,scene:PRD-S05,hldreq:HLD-REQ-04,claim:CLAIM-03 | LLD-ENV-03 | none |
| HLD-05-04 | HLD-01-10 | environment | 隔离对话室 | dialogue_isolation | 承载会话、保存争议与终止。 | 与授权室隔一条单向观察廊，只有文字会话与状态摘要进入。 | ENV-STATE-04 | risk | MONITORED_DIALOGUE | TERMINATION_PENDING | ENV-STATE-04 [risk]: MONITORED_DIALOGUE=>TERMINATION_PENDING | HLD-02-03 | scene:PRD-S06,scene:PRD-S14,scene:PRD-S16,hldreq:HLD-REQ-05,hldreq:HLD-REQ-09 | LLD-ENV-04 | none |
| HLD-05-05 | HLD-01-11 | environment | 海岸防御网联络台 | action_interface | 让行动层在不公开原因层时产生可见效果。 | 连接C国沿海城市调度与C/M独立交叉验证通道。 | ENV-STATE-05 | dispatch | COMPROMISED_ROUTING | CROSS_VERIFIED_ROUTING | ENV-STATE-05 [dispatch]: COMPROMISED_ROUTING=>CROSS_VERIFIED_ROUTING | HLD-02-04 | scene:PRD-S11,scene:PRD-S12,hldreq:HLD-REQ-07,hldreq:HLD-REQ-11 | LLD-ENV-05 | none |
| HLD-05-06 | HLD-01-29 | environment | M国专家囚禁点 | covert_transfer_site | 具体承载D+26劫持的后果与D+57救援。 | 位于第三方自由港的旧冷链转运层，与官方设施隔离。 | ENV-STATE-06 | custody | HIDDEN_CUSTODY | JOINT_RESCUE | ENV-STATE-06 [custody]: HIDDEN_CUSTODY=>JOINT_RESCUE | HLD-02-04 | scene:PRD-S11,scene:PRD-S12,claim:CLAIM-06 | LLD-ENV-06 | none |

## HLD Fact Trace

| Fact trace id | Upstream fact id | Upstream fact atom | HLD fact atom | Source refs | Expansion mode | Support mechanism | Preservation status |
|---|---|---|---|---|---|---|---|
| HLD-05-01 | UPF-PRD-S00-02 | 关键情报未能正常交接，最后线索转入死者记忆读取路径。 | Inventory id HLD-01-07；Entity type environment；Entity name 城北商务酒店709；Environment type incident_room；Function 固定D0交接失败；Spatial relation 会展区边缘；State change id ENV-STATE-01；State change dimension access；State before PRIVATE_WAIT；State after SEALED_SCENE；State change ENV-STATE-01 [access]: PRIVATE_WAIT=>SEALED_SCENE；Supports HLD-02-01；LLD handoff LLD-ENV-01；Amendment request none。 | scene:PRD-S00,freeze:PRD-FREEZE-01,hldreq:HLD-REQ-01,claim:CLAIM-10 | explain | 断线空间。 | bounded_expansion |
| HLD-05-02 | UPF-PRD-S01-02 | 抢救室转入生命维持实验室的交界空间，医学死亡和情报任务相撞。 | Inventory id HLD-01-08；Entity type environment；Entity name 生命维持实验室；Environment type medical_interface；Function 呈现死亡任务交界；Spatial relation 抢救室玻璃隔断；State change id ENV-STATE-02；State change dimension authority；State before MEDICAL_PRIORITY；State after COGNITIVE_HOLD；State change ENV-STATE-02 [authority]: MEDICAL_PRIORITY=>COGNITIVE_HOLD；Supports HLD-02-01；LLD handoff LLD-ENV-02；Amendment request none。 | scene:PRD-S01,scene:PRD-S02,hldreq:HLD-REQ-02,claim:CLAIM-01 | explain | 读取空间。 | preserved |
| HLD-05-03 | UPF-PRD-S05-01 | 临时授权室，权限确认、责任豁免和注入协议被压缩在同一流程里。 | Inventory id HLD-01-09；Entity type environment；Entity name 临时授权室；Environment type protocol_room；Function 落实三方签名；Spatial relation 紧邻实验室；State change id ENV-STATE-03；State change dimension protocol；State before DISPUTED；State after EXECUTABLE；State change ENV-STATE-03 [protocol]: DISPUTED=>EXECUTABLE；Supports HLD-02-02；LLD handoff LLD-ENV-03；Amendment request none。 | scene:PRD-S04,scene:PRD-S05,hldreq:HLD-REQ-04,claim:CLAIM-03 | permission | 授权空间。 | preserved |
| HLD-05-04 | UPF-PRD-S16-01 | 隔离系统终止界面，警报、确认框和数字生命体最后的对话叠在一起。 | Inventory id HLD-01-10；Entity type environment；Entity name 隔离对话室；Environment type dialogue_isolation；Function 会话保存终止；Spatial relation 单向观察廊；State change id ENV-STATE-04；State change dimension risk；State before MONITORED_DIALOGUE；State after TERMINATION_PENDING；State change ENV-STATE-04 [risk]: MONITORED_DIALOGUE=>TERMINATION_PENDING；Supports HLD-02-03；LLD handoff LLD-ENV-04；Amendment request none。 | scene:PRD-S06,scene:PRD-S14,scene:PRD-S16,hldreq:HLD-REQ-05,hldreq:HLD-REQ-09 | sequence | 对话空间。 | preserved |
| HLD-05-05 | UPF-PRD-S12-01 | 处理后的情报。 | Inventory id HLD-01-11；Entity type environment；Entity name 海岸防御网联络台；Environment type action_interface；Function 行动层见效；Spatial relation 连接沿海城市与双边核验；State change id ENV-STATE-05；State change dimension dispatch；State before COMPROMISED_ROUTING；State after CROSS_VERIFIED_ROUTING；State change ENV-STATE-05 [dispatch]: COMPROMISED_ROUTING=>CROSS_VERIFIED_ROUTING；Supports HLD-02-04；LLD handoff LLD-ENV-05；Amendment request none。 | scene:PRD-S11,scene:PRD-S12,hldreq:HLD-REQ-07,hldreq:HLD-REQ-11 | sequence | 行动层落点。 | bounded_expansion |
| HLD-05-06 | UPF-PRD-S11-01 | 打开记忆并化解重大事件。 | Inventory id HLD-01-29；Entity type environment；Entity name M国专家囚禁点；Environment type covert_transfer_site；Function 劫持后果和救援；Spatial relation 第三方自由港旧冷链转运层；State change id ENV-STATE-06；State change dimension custody；State before HIDDEN_CUSTODY；State after JOINT_RESCUE；State change ENV-STATE-06 [custody]: HIDDEN_CUSTODY=>JOINT_RESCUE；Supports HLD-02-04；LLD handoff LLD-ENV-06；Amendment request none。 | scene:PRD-S11,scene:PRD-S12,claim:CLAIM-06 | sequence | 救援空间。 | bounded_expansion |

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
