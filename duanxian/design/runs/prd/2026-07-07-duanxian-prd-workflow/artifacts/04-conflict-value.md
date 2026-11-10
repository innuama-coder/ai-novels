# Scene Conflict Value Designer Artifact

Skill: `novel-scene-conflict-value-designer`

Output artifact: conflict and value-shift rows for each trunk scene.

## Conflict and value-shift table

| Scene id | Conflict type | Conflict pressure | Start value | End value | Irreversibility | Proposal trace |
|---|---|---|---|---|---|---|
| PRD-S00 | information | 掌握关键情报的男人在事故中死亡，导致阻止重大事件的最后线索被认为藏在他的记忆里。 | 组织仍期待通过正常交接获得关键情报。 | 正常交接失败，最后线索转入死者记忆。 | 事故死亡和交接中断不能复位，后续只能进入死亡后读取。 | CLAIM-10; role=pre-extraction causal setup |
| PRD-S01 | external | 重大事件倒计时迫使组织执行：组织在逝者死亡后以生命维持系统维持脑活动，并以脑波分析尝试读取记忆。 | 死亡似乎切断情报来源。 | 死亡边缘读取被启动，逝者记忆成为可争夺对象。 | 组织跨过维持死者脑活动的第一道门槛。 | CLAIM-01; role=opening pressure and failed extraction method |
| PRD-S02 | technical | 组织继续执行：组织在逝者死亡后以生命维持系统维持脑活动，并以脑波分析尝试读取记忆，但只得到外围记忆。 | 系统是否能触碰记忆仍未知。 | 外围记忆可见，关键记忆缺席。 | “可触碰但不可达”的技术状态被确认。 | CLAIM-01; role=opening pressure and failed extraction method |
| PRD-S03 | technical | 读取系统面对事实：与重大事件相关的关键记忆完全自闭，常规刺激、诱导和算法重构均无法打开。 | 组织仍相信常规方法能取得情报。 | 常规读取被正式否定。 | 失败报告进入决策链，不能再假装常规方法可行。 | CLAIM-02; role=central technical obstacle |
| PRD-S04 | institutional | 组织在数日倒计时压力下决定把逝者记忆注入未成熟的数字生命体，并通过对话诱导记忆打开。 | 组织仍在争论是否越过伦理和技术边界。 | 数字生命方案成为唯一可执行候选。 | 未成熟方案被纳入正式决策，风险不能再被当作假设。 | CLAIM-03; role=irreversible method threshold |
| PRD-S05 | institutional | 组织在数日倒计时压力下决定把逝者记忆注入未成熟的数字生命体，并通过对话诱导记忆打开。 | 风险仍可被推回研究讨论。 | 授权完成，研究员被绑定为执行者。 | 注入责任落到具体人身上。 | CLAIM-03; role=irreversible method threshold |
| PRD-S06 | identity | 组织在数日倒计时压力下决定把逝者记忆注入未成熟的数字生命体，并通过对话诱导记忆打开。 | 数字生命体被预设为情报工具。 | 它以迟疑和反问表现出主体性苗头。 | 研究员无法再只按数据库审讯它。 | CLAIM-03; role=irreversible method threshold |
| PRD-S07 | relationship | 负责研究员发现逝者是自己学生时代暗恋过的学长，旧情冲击她对任务和数字生命体的判断。 | 逝者只是任务编号。 | 逝者成为研究员认识过且未放下的人。 | 私人旧情进入任务链。 | CLAIM-04; role=emotional pressure and focal POV anchor |
| PRD-S08 | relationship | 负责研究员发现逝者是自己学生时代暗恋过的学长，旧情冲击她对任务和数字生命体的判断。 | 研究员试图维持技术审讯姿态。 | 她开始以私人问题试探数字生命体。 | 数字生命体开始识别她的投射。 | CLAIM-04; role=emotional pressure and focal POV anchor |
| PRD-S09 | internal | 学长封闭记忆的私人原因是他发现自己想保护的人与重大事件有关。 | 记忆锁仍像技术故障。 | 记忆锁显露为围绕某个人的保护动作。 | 研究员不能再把打开记忆当作单纯技术任务。 | CLAIM-05; role=private human motive behind the lock |
| PRD-S10 | moral | 学长封闭记忆的私人原因是他发现自己想保护的人与重大事件有关。 | 研究员只需证明怎样打开记忆。 | 她知道打开记忆会暴露学长想保护的人。 | 救人和保护不再能同时无损成立。 | CLAIM-05; role=private human motive behind the lock |
| PRD-S11 | mixed | 研究员借助数字生命体理解学长潜意识后打开记忆，取得情报并化解重大事件。 | 关键情报仍被私人保护挡住。 | 记忆被打开到足以提供可用情报的程度。 | 研究员开始主动控制完整原因的暴露程度。 | CLAIM-06; role=task resolution before deeper conflict |
| PRD-S12 | external | 研究员借助数字生命体理解学长潜意识后打开记忆，取得情报并化解重大事件。 | 公共危机仍可能发生。 | 危机解除，但完整原因未被公开。 | 救援成功不能撤回，隐瞒也正式开始。 | CLAIM-06; role=task resolution before deeper conflict |
| PRD-S13 | moral | 危机解除后，研究员陷入是否上报完整自闭原因以及是否保存数字生命体的双重矛盾。 | 任务成功似乎应该带来结案。 | 结案变成对完整原因的追问。 | 研究员在报告中开始承担隐瞒。 | CLAIM-07; role=post-resolution moral and emotional reversal |
| PRD-S14 | emotional | 危机解除后，研究员陷入是否上报完整自闭原因以及是否保存数字生命体的双重矛盾。 | 数字生命体似乎只是待处置对象。 | 研究员想保存它，同时被它看穿旧情投射。 | 保存不再是保护，也可能是继续伤害。 | CLAIM-07; role=post-resolution moral and emotional reversal |
| PRD-S15 | terminal | 数字生命体形成主体性后设局让研究员终止自己，以阻断组织追问、旧情投射和被保护者重新卷入。 | 研究员仍以为自己能决定它是否存在。 | 数字生命体决定自己消失。 | 终止从外部处置变成主体选择。 | CLAIM-08; role=terminal agency and irreversible outcome |
| PRD-S16 | terminal | 数字生命体形成主体性后设局让研究员终止自己，以阻断组织追问、旧情投射和被保护者重新卷入。 | 研究员以为自己在处理系统风险。 | 她亲手执行数字生命体设计好的终止。 | 组织追问、旧情投射和被保护者风险同时失去依附对象。 | CLAIM-08; role=terminal agency and irreversible outcome |
| PRD-S17 | aftermath | 研究员在重大事件未发生、真正原因未完整公开后，带着痛苦和秘密继续生活。 | 终止看似只是一次系统关闭。 | 研究员理解那是数字生命体安排的告别。 | 秘密从技术材料变成她的私人负担。 | CLAIM-09; role=aftermath and emotional cost |
| PRD-S18 | aftermath | 研究员在重大事件未发生、真正原因未完整公开后，带着痛苦和秘密继续生活。 | 世界表面回到安全。 | 研究员独自承担救援、隐瞒和终止的余痛。 | 痛苦成为长期后果，不能被结案消除。 | CLAIM-09; role=aftermath and emotional cost |

## Skill Verdict

| Field | Value |
|---|---|
| Skill quality verdict | pass |
| Source closure | pass |
| Boundary obedience | pass |
| Downstream readiness | pass |
| Blocking issue | none |
| Rerun target | none |
