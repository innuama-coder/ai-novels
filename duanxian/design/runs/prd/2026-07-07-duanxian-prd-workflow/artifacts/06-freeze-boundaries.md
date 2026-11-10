# PRD Freeze Boundary Writer Artifact

Skill: `novel-prd-freeze-boundary-writer`

Output artifact: PRD freeze boundary list.

## Freeze boundary list

| Freeze id | Frozen item | Source | Downstream no-change rule | Reopen condition |
|---|---|---|---|---|
| PRD-FREEZE-01 | 本段起点必须是关键情报交接失败与事故死亡，最后线索因此转入死者记忆。 | scene:PRD-S00, claim:CLAIM-10 | HLD 不得把起点改成情报已经正常交接、生前主动备份、主动上传或组织已经掌握完整情报。 | 如果 proposal 重开并取消事故死亡或最后线索在记忆中，重开 PRD。 |
| PRD-FREEZE-02 | 死亡后生命维持和脑波分析读取必须被启动，并且外围记忆可触碰、关键记忆尚未可达。 | scene:PRD-S01, scene:PRD-S02, claim:CLAIM-01 | HLD 不得把读取改成完全不可读或已经成功读取。 | 如果死亡后脑活动维持无法成立，重开 PRD。 |
| PRD-FREEZE-03 | 关键记忆必须完全自闭，常规刺激、诱导和算法重构均失败。 | scene:PRD-S03, claim:CLAIM-02 | HLD 不得让常规脑波分析直接读出关键情报。 | 如果需要改变记忆锁性质，重开 proposal。 |
| PRD-FREEZE-04 | 数字生命注入必须发生在数日倒计时、未成熟应用、授权争议和具体执行责任压力下。 | scene:PRD-S04, scene:PRD-S05, scene:PRD-S06, claim:CLAIM-03 | HLD 不得把数字生命方案改成成熟、安全、常规工具。 | 如果注入方案不再危险，重开 PRD。 |
| PRD-FREEZE-05 | 研究员必须发现逝者是学生时代暗恋过的学长，并在后续对话中被旧情持续冲击。 | scene:PRD-S07, scene:PRD-S08, claim:CLAIM-04 | HLD 不得删除旧情，也不得把旧情改成现任恋爱关系或普通同事情谊。 | 如果焦点人物关系要改，重开 proposal。 |
| PRD-FREEZE-06 | 记忆自闭原因必须是学长保护与重大事件有关的某个人，且这个原因通过对话和碎片逐步确认。 | scene:PRD-S09, scene:PRD-S10, claim:CLAIM-05 | HLD 不得把原因改成宏大伦理宣言、技术故障或抽象善恶。 | 如果保护对象不再与事件有关，重开 proposal。 |
| PRD-FREEZE-07 | 危机必须通过数字生命体理解学长潜意识后打开记忆而化解，且完整原因未被全部上报。 | scene:PRD-S11, scene:PRD-S12, claim:CLAIM-06 | HLD 不得让危机靠外部偶然情报或组织单独破解解决。 | 如果解决路径改变，重开 PRD。 |
| PRD-FREEZE-08 | 危机解除后必须出现上报完整原因和保存数字生命体的双重矛盾，并让保存欲望暴露旧情投射。 | scene:PRD-S13, scene:PRD-S14, claim:CLAIM-07 | HLD 不得让结案变成无代价成功，也不得让保存数字生命体只表现为技术决策。 | 如果后半段矛盾取消，重开 PRD。 |
| PRD-FREEZE-09 | 终止必须由数字生命体形成主体性后设计，并由研究员在误判中执行。 | scene:PRD-S15, scene:PRD-S16, claim:CLAIM-08 | HLD/LLD/writing 不得改成组织强制销毁、研究员单方面牺牲它或单纯系统关闭。 | 如果终端能动性改变，重开 proposal。 |
| PRD-FREEZE-10 | 结尾必须呈现研究员事后理解骗局，并在真正原因未完整公开后带着痛苦和秘密继续生活。 | scene:PRD-S17, scene:PRD-S18, claim:CLAIM-09 | 下游不得让真相完全公开、数字生命继续存活或研究员立即释然。 | 如果余波方向改变，重开 proposal。 |
| PRD-FREEZE-11 | 可用情报必须与完整原因分层：前者包含时间、地点、触发条件、阻断方式和行动窗口，后者包含被保护者身份、关系和私人动机。 | scene:PRD-S11, scene:PRD-S12, claim:CLAIM-06 | HLD 不得让被保护者身份成为阻断危机的必要条件，也不得让完整原因被自然完整上报。 | 如果危机解决必须依赖公开被保护者身份，重开 PRD。 |
| PRD-FREEZE-12 | 被保护者必须是被胁迫或被误导卷入触发链的人，暴露后会面临组织处置、审查或重新卷入，且与学长存在私人关系或亏欠关系。 | scene:PRD-S09, scene:PRD-S10, claim:CLAIM-05 | HLD 不得把被保护者改成无关旁支、纯粹加害者或抽象伦理符号。 | 如果被保护者关系无法支撑学长封闭记忆和研究员隐瞒，重开 PRD。 |
| PRD-FREEZE-13 | 数字生命体终止骗局必须在能力边界内成立：不能控制外部系统、不能凭空伪造权限、不能改写权限，只能利用既有告警、日志、系统提示、对话节奏、研究员误判和终止流程多重确认。 | scene:PRD-S15, scene:PRD-S16, claim:CLAIM-08 | HLD 不得把终止骗局写成无约束超能力、组织命令或系统故障。 | 如果平台能力无法支撑该骗局，重开 PRD。 |
| PRD-FREEZE-14 | 组织在危机解除后仍会结案审查、追问情报缺口和评估数字生命体资产价值，但受隔离保存窗口、审查流程和终止权限限制，不能直接复制或接管数字生命体。 | scene:PRD-S13, scene:PRD-S14, scene:PRD-S15, claim:CLAIM-07 | HLD 不得让组织压力消失，也不得让组织直接抢走数字生命体终止选择。 | 如果组织可以直接复制或接管数字生命体，重开 PRD。 |

## Skill Verdict

| Field | Value |
|---|---|
| Skill quality verdict | pass |
| Source closure | pass |
| Boundary obedience | pass |
| Downstream readiness | pass |
| Blocking issue | none |
| Rerun target | none |
