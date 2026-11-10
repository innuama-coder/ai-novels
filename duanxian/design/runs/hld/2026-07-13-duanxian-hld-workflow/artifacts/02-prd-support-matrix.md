## Artifact Metadata

| Field | Value |
|---|---|
| Artifact id | 02 |
| Owner skill | novel-prd-support-matrix-builder |
| Run id | 2026-07-13-duanxian-hld-workflow |
| Upstream package | final PRD package and canonical world facts v3.0 |
| Input artifacts | artifact 01, PRD scenes, freezes, HLD requirements |
| Output path | artifacts/02-prd-support-matrix.md |
| Version | v3.0 |

## PRD support matrix

| Support id | Supports | Support type | Required HLD owner | Inventory obligations | Required answer | Boundary | Source | Support status |
|---|---|---|---|---|---|---|---|---|
| HLD-02-01 | PRD-S00—S03 | explain | artifact 03 | HLD-01-16 | 维持、读取失败与保护核为何同时成立。 | 常规读取不得直接成功。 | scene:PRD-S00,scene:PRD-S01,scene:PRD-S02,scene:PRD-S03,freeze:PRD-FREEZE-01,freeze:PRD-FREEZE-03,hldreq:HLD-REQ-01,hldreq:HLD-REQ-02 | ready |
| HLD-02-02 | PRD-S04—S06 | permission | artifact 03 | HLD-01-17 | 谁批准注入，为什么 R-07 受限且不可复制。 | 不把 R-07 写成成熟工具。 | scene:PRD-S04,scene:PRD-S05,scene:PRD-S06,freeze:PRD-FREEZE-04,hldreq:HLD-REQ-04 | ready |
| HLD-02-03 | 顾衡、周岚、周启明、组织 | support | artifact 04 | HLD-01-01,HLD-01-02,HLD-01-03,HLD-01-04,HLD-01-05,HLD-01-06,HLD-01-27,HLD-01-28 | 关系、责任与信息权限如何驱动每人选择。 | 不把周岚写成无知工具或简单恶人。 | scene:PRD-S07,scene:PRD-S09,scene:PRD-S10,freeze:PRD-FREEZE-05,freeze:PRD-FREEZE-06,freeze:PRD-FREEZE-12,hldreq:HLD-REQ-05,hldreq:HLD-REQ-12 | ready |
| HLD-02-04 | 双重伪旗危机 | sequence | artifact 06 | HLD-01-12,HLD-01-13,HLD-01-14,HLD-01-15,HLD-01-29,HLD-01-30,HLD-01-31 | D0、D+26、D+57、D+58 和终止如何形成因果链。 | 行动层不得依赖公开周岚身份。 | scene:PRD-S11,scene:PRD-S12,freeze:PRD-FREEZE-07,freeze:PRD-FREEZE-11,storylogic:PRD-LOGIC-01,hldreq:HLD-REQ-11 | ready |
| HLD-02-05 | 保护核与报告分层 | sequence | artifact 07 | HLD-01-19,HLD-01-20,HLD-01-21,HLD-01-22,HLD-01-23,HLD-01-24,HLD-01-33 | 信息以何顺序向沈逾、联络组和读者开放，并让专家与模块形成可执行物证链。 | 完整原因不得自然上报；模块不得被写成单点启动密钥。 | scene:PRD-S09,scene:PRD-S10,scene:PRD-S11,scene:PRD-S12,hldreq:HLD-REQ-06,hldreq:HLD-REQ-07,storylogic:PRD-LOGIC-02 | ready |
| HLD-02-06 | 终止骗局 | constrain | artifact 06 | HLD-01-15 | R-07 如何只利用既有流程诱导终止。 | 无外部控制、无伪造权限。 | scene:PRD-S15,scene:PRD-S16,freeze:PRD-FREEZE-09,freeze:PRD-FREEZE-13,storylogic:PRD-LOGIC-03,hldreq:HLD-REQ-13 | ready |
| HLD-02-07 | 余波与焦点 | handoff | artifact 09 | HLD-01-25,HLD-01-26 | 如何保持沈逾限知并让 R-07 主体性可见。 | 不给 R-07 无边界内心独白。 | scene:PRD-S07,scene:PRD-S08,scene:PRD-S17,scene:PRD-S18,freeze:PRD-FREEZE-10,hldreq:HLD-REQ-10 | ready |

## HLD Fact Trace

| Fact trace id | Upstream fact id | Upstream fact atom | HLD fact atom | Source refs | Expansion mode | Support mechanism | Preservation status |
|---|---|---|---|---|---|---|---|
| HLD-02-01 | UPF-PRD-S03-01 | 关键记忆完全自闭。 | Supports PRD-S00—S03；Support type explain；Required HLD owner artifact 03；Inventory obligations HLD-01-16；Required answer 维持读取失败与保护核为何同时成立；Boundary 常规读取不得直接成功；Support status ready。 | scene:PRD-S00,scene:PRD-S01,scene:PRD-S02,scene:PRD-S03,freeze:PRD-FREEZE-01,freeze:PRD-FREEZE-03,hldreq:HLD-REQ-01,hldreq:HLD-REQ-02 | explain | 派发读取约束。 | preserved |
| HLD-02-02 | UPF-PRD-S04-01 | 数字生命方案成为唯一可执行候选。 | Supports PRD-S04—S06；Support type permission；Required HLD owner artifact 03；Inventory obligations HLD-01-17；Required answer 三方授权与受限实例；Boundary 不写成熟工具；Support status ready。 | scene:PRD-S04,scene:PRD-S05,scene:PRD-S06,freeze:PRD-FREEZE-04,hldreq:HLD-REQ-04 | permission | 派发注入约束。 | preserved |
| HLD-02-03 | UPF-PRD-S10-01 | 被保护者不是简单凶手。 | Supports 顾衡周岚周启明组织；Support type support；Required HLD owner artifact 04；Inventory obligations HLD-01-01,HLD-01-02,HLD-01-03,HLD-01-04,HLD-01-05,HLD-01-06；Required answer 关系责任权限；Boundary 不写无知工具或简单恶人；Support status ready。 | scene:PRD-S07,scene:PRD-S09,scene:PRD-S10,freeze:PRD-FREEZE-05,freeze:PRD-FREEZE-06,freeze:PRD-FREEZE-12,hldreq:HLD-REQ-05,hldreq:HLD-REQ-12 | support | 派发人物约束。 | bounded_expansion |
| HLD-02-04 | UPF-PRD-S11-01 | 打开记忆。 | Supports 双重伪旗危机；Support type sequence；Required HLD owner artifact 06；Inventory obligations HLD-01-12,HLD-01-13,HLD-01-14,HLD-01-15；Required answer D0至终止因果链；Boundary 行动层不依赖公开周岚；Support status ready。 | scene:PRD-S11,scene:PRD-S12,freeze:PRD-FREEZE-07,freeze:PRD-FREEZE-11,storylogic:PRD-LOGIC-01,hldreq:HLD-REQ-11 | sequence | 派发事件约束。 | bounded_expansion |
| HLD-02-05 | UPF-PRD-S12-01 | 处理后的情报。 | Supports 保护核与报告分层；Support type sequence；Required HLD owner artifact 07；Inventory obligations HLD-01-19,HLD-01-20,HLD-01-21,HLD-01-22,HLD-01-23,HLD-01-24；Required answer 信息开放顺序；Boundary 完整原因不得自然上报；Support status ready。 | scene:PRD-S09,scene:PRD-S10,scene:PRD-S11,scene:PRD-S12,hldreq:HLD-REQ-06,hldreq:HLD-REQ-07,storylogic:PRD-LOGIC-02 | sequence | 派发信息约束。 | bounded_expansion |
| HLD-02-06 | UPF-PRD-S15-01 | 数字生命体决定设计自己的终止。 | Supports 终止骗局；Support type constrain；Required HLD owner artifact 06；Inventory obligations HLD-01-15；Required answer 既有流程诱导终止；Boundary 无外部控制无伪造权限；Support status ready。 | scene:PRD-S15,scene:PRD-S16,freeze:PRD-FREEZE-09,freeze:PRD-FREEZE-13,storylogic:PRD-LOGIC-03,hldreq:HLD-REQ-13 | constrain | 派发终止约束。 | preserved |
| HLD-02-07 | UPF-PRD-S08-01 | 研究员的诱导方式转向私人试探。 | Supports 余波与焦点；Support type handoff；Required HLD owner artifact 09；Inventory obligations HLD-01-25,HLD-01-26；Required answer 沈逾限知与主体可见；Boundary 无边界内心独白禁止；Support status ready。 | scene:PRD-S07,scene:PRD-S08,scene:PRD-S17,scene:PRD-S18,freeze:PRD-FREEZE-10,hldreq:HLD-REQ-10 | handoff | 派发叙述约束。 | preserved |

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
