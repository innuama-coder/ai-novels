# PRD Integrator Artifact

Skill: `novel-prd-integrator`

Output artifact: integrated PRD assembly.

Source inputs:

- Artifact 01 part scope.
- Artifact 02 part goal.
- Artifact 03 trunk scene table.
- Artifact 04 conflict and value-shift table.
- Artifact 05 information-flow table.
- Artifact 06 freeze boundary list.
- Artifact 07 HLD expansion requirement list.

## PRD Integration Verdict

| Field | Value |
|---|---|
| Source completeness | pass |
| Scene fact preservation | pass |
| No new business content | pass |
| Package readiness | pass |

## Scene Source Map

| Scene id | Order | Event fact | Causal output | Proposal trace | Source artifact |
|---|---|---|---|---|---|
| PRD-S00 | 1 | 掌握关键情报的男人在事故中死亡，导致阻止重大事件的最后线索被认为藏在他的记忆里。 | 关键情报未能正常交接，组织确认最后线索只能转入死者记忆读取路径。 | CLAIM-10; role=pre-extraction causal setup | artifact 03 |
| PRD-S01 | 2 | 组织在逝者死亡后以生命维持系统维持脑活动，并以脑波分析尝试读取记忆。 | 死亡不再是调查终点，组织把逝者记忆转入可技术处理的状态。 | CLAIM-01; role=opening pressure and failed extraction method | artifact 03 |
| PRD-S02 | 3 | 组织在逝者死亡后以生命维持系统维持脑活动，并以脑波分析尝试读取记忆。 | 组织确认外围记忆有响应，但关键记忆尚未出现。 | CLAIM-01; role=opening pressure and failed extraction method | artifact 03 |
| PRD-S03 | 4 | 与重大事件相关的关键记忆完全自闭，常规刺激、诱导和算法重构均无法打开。 | 常规读取路线被正式判定失败，组织需要非常规方法。 | CLAIM-02; role=central technical obstacle | artifact 03 |
| PRD-S04 | 5 | 组织在数日倒计时压力下决定把逝者记忆注入未成熟的数字生命体，并通过对话诱导记忆打开。 | 数字生命方案成为唯一可执行候选，但伦理和技术风险被同时抬高。 | CLAIM-03; role=irreversible method threshold | artifact 03 |
| PRD-S05 | 6 | 组织在数日倒计时压力下决定把逝者记忆注入未成熟的数字生命体，并通过对话诱导记忆打开。 | 组织完成授权，研究员被绑定为注入后的首席对话者。 | CLAIM-03; role=irreversible method threshold | artifact 03 |
| PRD-S06 | 7 | 组织在数日倒计时压力下决定把逝者记忆注入未成熟的数字生命体，并通过对话诱导记忆打开。 | 数字生命体醒来，但没有直接给出情报，研究员必须通过对话进入记忆。 | CLAIM-03; role=irreversible method threshold | artifact 03 |
| PRD-S07 | 8 | 负责研究员发现逝者是自己学生时代暗恋过的学长，旧情冲击她对任务和数字生命体的判断。 | 逝者从任务编号变成研究员认识过的人，后续对话带上私人情绪。 | CLAIM-04; role=emotional pressure and focal POV anchor | artifact 03 |
| PRD-S08 | 9 | 负责研究员发现逝者是自己学生时代暗恋过的学长，旧情冲击她对任务和数字生命体的判断。 | 研究员的诱导方式从技术审讯转向私人试探，数字生命体开始识别她的投射。 | CLAIM-04; role=emotional pressure and focal POV anchor | artifact 03 |
| PRD-S09 | 10 | 学长封闭记忆的私人原因是他发现自己想保护的人与重大事件有关。 | 研究员发现记忆锁不是技术故障，而是围绕某个人形成的保护动作。 | CLAIM-05; role=private human motive behind the lock | artifact 03 |
| PRD-S10 | 11 | 学长封闭记忆的私人原因是他发现自己想保护的人与重大事件有关。 | 研究员确认打开记忆会暴露被保护者，救人与保护开始互相冲突。 | CLAIM-05; role=private human motive behind the lock | artifact 03 |
| PRD-S11 | 12 | 研究员借助数字生命体理解学长潜意识后打开记忆，取得情报并化解重大事件。 | 关键记忆被打开到足以提供情报的程度，但完整原因仍被研究员控制。 | CLAIM-06; role=task resolution before deeper conflict | artifact 03 |
| PRD-S12 | 13 | 研究员借助数字生命体理解学长潜意识后打开记忆，取得情报并化解重大事件。 | 公共危机解除，组织得到处理后的情报，但完整私人原因未被上报。 | CLAIM-06; role=task resolution before deeper conflict | artifact 03 |
| PRD-S13 | 14 | 危机解除后，研究员陷入是否上报完整自闭原因以及是否保存数字生命体的双重矛盾。 | 研究员开始在报告中隐瞒完整原因，组织对未解释部分产生追问。 | CLAIM-07; role=post-resolution moral and emotional reversal | artifact 03 |
| PRD-S14 | 15 | 危机解除后，研究员陷入是否上报完整自闭原因以及是否保存数字生命体的双重矛盾。 | 研究员试图延长数字生命体存在，数字生命体意识到她在把旧情投射到自己身上。 | CLAIM-07; role=post-resolution moral and emotional reversal | artifact 03 |
| PRD-S15 | 16 | 数字生命体形成主体性后设局让研究员终止自己，以阻断组织追问、旧情投射和被保护者重新卷入。 | 数字生命体决定设计自己的终止，而不是等待研究员或组织决定。 | CLAIM-08; role=terminal agency and irreversible outcome | artifact 03 |
| PRD-S16 | 17 | 数字生命体形成主体性后设局让研究员终止自己，以阻断组织追问、旧情投射和被保护者重新卷入。 | 研究员执行终止程序，数字生命体以自我消失完成最终选择。 | CLAIM-08; role=terminal agency and irreversible outcome | artifact 03 |
| PRD-S17 | 18 | 研究员在重大事件未发生、真正原因未完整公开后，带着痛苦和秘密继续生活。 | 研究员开始理解终止是数字生命体的设计，秘密也从技术材料变成个人负担。 | CLAIM-09; role=aftermath and emotional cost | artifact 03 |
| PRD-S18 | 19 | 研究员在重大事件未发生、真正原因未完整公开后，带着痛苦和秘密继续生活。 | 本段以研究员长期承担后果收束，HLD 后续只能扩展余波，不能改写终止和秘密。 | CLAIM-09; role=aftermath and emotional cost | artifact 03 |

## HLD information boundary table

| Information boundary id | Story anchor scene id | Narrative reveal scene id | Narrative reveal order | Disclosure tier | Information object | Reader access | Known by entity refs | Hidden from entity refs | Reveal predecessor boundary refs | Reveal condition type | Freeze refs | Source | HLD obligation |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PRD-INFO-01 | PRD-S01 | PRD-S03 | 4 | protected_memory | 关键记忆自闭与常规读取失败 | visible | reader, entity:研究员, entity:组织 | none | none | evidence_change | freeze:PRD-FREEZE-02, freeze:PRD-FREEZE-03 | scene:PRD-S01, scene:PRD-S03 | HLD 必须把关键记忆自闭绑定到常规读取失败的事件链，不得提前直接读取。 |
| PRD-INFO-02 | PRD-S06 | PRD-S08 | 9 | institutional_assessment | 数字生命体的主体性与非学长身份 | visible | reader, entity:研究员, entity:数字生命体 | entity:组织 | none | action | freeze:PRD-FREEZE-04, freeze:PRD-FREEZE-05 | scene:PRD-S06, scene:PRD-S08 | HLD 必须让数字生命体在对话中表现独立主体性，不得写成学长复活或情报数据库。 |
| PRD-INFO-03 | PRD-S09 | PRD-S10 | 11 | partial_cause | 被保护者与重大事件的关联 | visible | reader, entity:研究员, entity:数字生命体 | entity:组织 | PRD-INFO-01 | action | freeze:PRD-FREEZE-06, freeze:PRD-FREEZE-12 | scene:PRD-S09, scene:PRD-S10 | HLD 必须通过保护动作和碎片确认关联，不得把原因改成技术故障或抽象善恶。 |
| PRD-INFO-04 | PRD-S11 | PRD-S11 | 12 | operational_intelligence | 阻断危机的时间、地点、触发条件和行动窗口 | visible | reader, entity:研究员, entity:数字生命体 | entity:组织 | PRD-INFO-03 | action | freeze:PRD-FREEZE-07, freeze:PRD-FREEZE-11 | scene:PRD-S11 | HLD 必须让研究员与数字生命体经由有限打开取得可用情报，并保持与完整原因分层。 |
| PRD-INFO-05 | PRD-S10 | PRD-S13 | 14 | complete_cause | 被保护者身份、关系与私人保护动机 | concealed | entity:研究员, entity:数字生命体 | reader, entity:组织 | PRD-INFO-04 | permission | freeze:PRD-FREEZE-07, freeze:PRD-FREEZE-11, freeze:PRD-FREEZE-12 | scene:PRD-S10, scene:PRD-S13 | HLD 必须保留完整原因不进入正式上报，并让研究员的隐瞒承担人际后果。 |
| PRD-INFO-06 | PRD-S15 | PRD-S17 | 18 | private_motive | 数字生命体设计终止的真实意图 | visible | reader, entity:研究员, entity:数字生命体 | entity:组织 | PRD-INFO-04 | evidence_change | freeze:PRD-FREEZE-09, freeze:PRD-FREEZE-13 | scene:PRD-S15, scene:PRD-S17 | HLD 必须让终止骗局在既有权限、日志和确认流程内成立，并在事后揭示其主体选择。 |

## Skill Verdict

| Field | Value |
|---|---|
| Skill quality verdict | pass |
| Source closure | pass |
| Boundary obedience | pass |
| Downstream readiness | pass |
| Blocking issue | none |
| Rerun target | none |
