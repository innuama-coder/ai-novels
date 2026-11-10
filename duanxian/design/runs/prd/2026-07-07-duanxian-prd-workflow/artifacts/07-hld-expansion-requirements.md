# HLD Expansion Requirement Writer Artifact

Skill: `novel-hld-expansion-requirement-writer`

Output artifact: HLD expansion requirement list.

## HLD expansion requirement list

| Requirement id | Required expansion | Supports scene ids | Information boundary refs | Inherited HLD obligations | Required answer | Boundary | Source |
|---|---|---|---|---|---|---|---|
| HLD-REQ-01 | 情报交接与事故现场：接应机制、传输残片、事故发生条件、组织如何判断正常情报路径断裂。 | PRD-S00 | none | none | HLD 需回答情报员在什么情况下死亡，为什么关键情报未能交接，为什么最后线索只能转入死者记忆。 | 不得把情报改成已经正常交接、已被组织完整掌握或可从残片直接复原。 | scene:PRD-S00, claim:CLAIM-10 |
| HLD-REQ-02 | 死亡边缘读取体系：医学状态、生命维持权限、脑波分析界面、抢救室到实验室的空间转换。 | PRD-S01, PRD-S02 | PRD-INFO-01 | HLD 必须把关键记忆自闭绑定到常规读取失败的事件链，不得提前直接读取。 | HLD 需回答脑活动如何被维持，外围记忆为何可见，研究员如何在场景中感到“死亡已发生但任务未结束”。 | 不得让脑波分析直接成功读取关键记忆。 | scene:PRD-S01, scene:PRD-S02, claim:CLAIM-01 |
| HLD-REQ-03 | 关键记忆自闭机制：失败证据、算法日志、刺激诱导表现、组织如何形成失败结论。 | PRD-S03 | PRD-INFO-01 | HLD 必须把关键记忆自闭绑定到常规读取失败的事件链，不得提前直接读取。 | HLD 需定义“完全自闭”在画面、数据和人物判断中的表现。 | 不得把自闭原因提前解释成技术故障或普通加密。 | scene:PRD-S03, claim:CLAIM-02 |
| HLD-REQ-04 | 数字生命方案决策体系：支持派、反对派、授权记录、未成熟技术风险和研究员执行责任。 | PRD-S04, PRD-S05, PRD-S06 | PRD-INFO-02 | HLD 必须让数字生命体在对话中表现独立主体性，不得写成学长复活或情报数据库。 | HLD 需回答谁能批准注入，为什么反对无效，数字生命体初醒时系统如何限制它。 | 不得把方案写成成熟产品，也不得消除伦理和技术不确定性。 | scene:PRD-S04, scene:PRD-S05, scene:PRD-S06, claim:CLAIM-03 |
| HLD-REQ-05 | 研究员与学长旧情：学生时代资料、记忆触发物、语言习惯、研究员焦点视角规则。 | PRD-S07, PRD-S08 | PRD-INFO-02 | HLD 必须让数字生命体在对话中表现独立主体性，不得写成学长复活或情报数据库。 | HLD 需定义哪些资料或对话细节让研究员确认学长身份，以及旧情如何改变提问方式。 | 不得切换成数字生命体长篇内心独白，也不得把数字生命体写成学长复活。 | scene:PRD-S07, scene:PRD-S08, claim:CLAIM-04 |
| HLD-REQ-06 | 被保护者遮蔽结构：片段线索、责任复杂性、不能公开的原因、研究员如何确认私人保护动机。 | PRD-S09, PRD-S10 | PRD-INFO-03, PRD-INFO-05 | HLD 必须通过保护动作和碎片确认关联，不得把原因改成技术故障或抽象善恶。HLD 必须保留完整原因不进入正式上报，并让研究员的隐瞒承担人际后果。 | HLD 需定义被保护者为何与重大事件有关，又为何不能被写成简单加害者。 | 不得把私人保护原因改成抽象大义。 | scene:PRD-S09, scene:PRD-S10, claim:CLAIM-05 |
| HLD-REQ-07 | 危机情报转化机制：可用情报、完整原因、行动指挥、处理后报告。 | PRD-S11, PRD-S12 | PRD-INFO-04 | HLD 必须让研究员与数字生命体经由有限打开取得可用情报，并保持与完整原因分层。 | HLD 需回答什么信息足以化解重大事件，哪些信息被研究员主动保留。 | 不得让危机解决绕开数字生命体和研究员。 | scene:PRD-S11, scene:PRD-S12, claim:CLAIM-06 |
| HLD-REQ-08 | 结案审查与保存权限：报告格式、追问机制、隔离系统保存窗口、数字生命体对研究员投射的识别。 | PRD-S13, PRD-S14 | PRD-INFO-05 | HLD 必须保留完整原因不进入正式上报，并让研究员的隐瞒承担人际后果。 | HLD 需定义研究员如何在上报、保护、保存和旧情之间被制度挤压。 | 不得让结案无代价完成，也不得把保存写成单纯技术延期。 | scene:PRD-S13, scene:PRD-S14, claim:CLAIM-07 |
| HLD-REQ-09 | 数字生命体终止设计：权限可见范围、误导研究员的路径、终止界面、最后对话和事后可识别线索。 | PRD-S15, PRD-S16 | PRD-INFO-06 | HLD 必须让终止骗局在既有权限、日志和确认流程内成立，并在事后揭示其主体选择。 | HLD 需回答数字生命体如何理解三方风险，并让研究员在误判中执行终止。 | 不得把终止改成组织命令、研究员单方决定或系统故障。 | scene:PRD-S15, scene:PRD-S16, claim:CLAIM-08 |
| HLD-REQ-10 | 事后余波：空置对话室、组织档案、日常生活表面、研究员无法赦免自己的长期心理代价。 | PRD-S17, PRD-S18 | none | none | HLD 需定义研究员如何逐渐理解骗局，以及安全世界如何与未公开真相并存。 | 不得让真正原因完整公开、数字生命继续存活或研究员立即释然。 | scene:PRD-S17, scene:PRD-S18, claim:CLAIM-09 |
| HLD-REQ-11 | 可用情报与完整原因分层机制：哪些字段可进入行动报告，哪些字段会暴露被保护者。 | PRD-S11, PRD-S12 | PRD-INFO-04 | HLD 必须让研究员与数字生命体经由有限打开取得可用情报，并保持与完整原因分层。 | HLD 需定义时间、地点、触发条件、阻断方式和行动窗口如何足以化解危机，以及身份、关系和私人动机为什么属于完整原因。 | 不得让被保护者身份成为阻断危机的必要条件，也不得让完整原因被自然完整上报。 | scene:PRD-S11, scene:PRD-S12, claim:CLAIM-06 |
| HLD-REQ-12 | 被保护者卷入机制：被胁迫或被误导卷入触发链的具体方式、暴露后果和学长保护强度。 | PRD-S09, PRD-S10 | PRD-INFO-03, PRD-INFO-05 | HLD 必须通过保护动作和碎片确认关联，不得把原因改成技术故障或抽象善恶。HLD 必须保留完整原因不进入正式上报，并让研究员的隐瞒承担人际后果。 | HLD 需定义被保护者如何与重大事件有关，为什么不是简单加害者，为什么暴露会导致组织处置、审查或重新卷入，以及被保护者与学长之间的私人关系或亏欠关系。 | 不得改成抽象伦理理由、无关旁支或纯粹加害者。 | scene:PRD-S09, scene:PRD-S10, claim:CLAIM-05 |
| HLD-REQ-13 | 终止骗局能力边界：既有告警、日志、系统提示、对话节奏、研究员误判和终止流程多重确认如何组成可执行骗局。 | PRD-S15, PRD-S16 | PRD-INFO-06 | HLD 必须让终止骗局在既有权限、日志和确认流程内成立，并在事后揭示其主体选择。 | HLD 需定义数字生命体可见但不可控制的系统范围，以及它如何在不伪造权限、不控制外部系统的前提下诱导终止。 | 不得把终止骗局写成无约束超能力、组织命令或系统故障。 | scene:PRD-S15, scene:PRD-S16, claim:CLAIM-08 |
| HLD-REQ-14 | 组织压力和限制：危机解除后的结案审查、情报缺口追问、数字生命体资产评估，以及组织不能直接复制或接管数字生命体的制度或技术限制。 | PRD-S13, PRD-S14, PRD-S15 | PRD-INFO-05 | HLD 必须保留完整原因不进入正式上报，并让研究员的隐瞒承担人际后果。 | HLD 需定义组织为什么仍然施压，又为什么受隔离保存窗口、审查流程和终止权限限制而无法直接夺走终局选择。 | 不得让组织压力消失，也不得让组织直接抢走数字生命体终止选择。 | scene:PRD-S13, scene:PRD-S14, scene:PRD-S15, claim:CLAIM-07 |

## Story logic requirement coverage

| Boundary id | HLD requirement id | Inherited frozen answer |
|---|---|---|
| PRD-LOGIC-01 | HLD-REQ-11 | 可用情报只包含阻止重大事件所需的时间、地点、触发条件、阻断方式和行动窗口；完整原因才包含被保护者身份、关系和私人动机，因此研究员可以化解危机但隐去完整原因。 |
| PRD-LOGIC-02 | HLD-REQ-12 | 被保护者是被胁迫或被误导卷入触发链的人，不是简单加害者；暴露身份会导致组织处置、审查或重新卷入，并且被保护者与学长存在私人关系或亏欠关系，足以支撑学长封闭记忆和研究员隐瞒。 |
| PRD-LOGIC-03 | HLD-REQ-13 | 数字生命体不能控制外部系统、不能凭空伪造权限，也不能改写权限；它只能利用既有告警、日志、系统提示、对话节奏、研究员误判和终止流程多重确认，让终止看似风险控制。 |
| PRD-LOGIC-04 | HLD-REQ-14 | 组织在危机解除后仍会结案审查、追问情报缺口和评估数字生命体资产价值，但受隔离保存窗口、审查流程和终止权限限制，不能直接复制或接管数字生命体。 |

## Upstream required HLD entities

| Upstream fact id | Source fact field | Upstream fact atom | Required HLD entity | Required entity type | Source refs |
|---|---|---|---|---|---|
| UPF-PRD-S00-01 | Entry state | 情报员已经接近重大事件真相，必须在倒计时前完成关键情报交接。 | 情报员 | character | scene:PRD-S00, claim:CLAIM-10 |
| UPF-PRD-S00-02 | Causal output | 关键情报未能正常交接，组织确认最后线索只能转入死者记忆读取路径。 | 关键情报 | event | scene:PRD-S00, claim:CLAIM-10 |
| UPF-PRD-S01-01 | Roles | 研究员、组织值班负责人、急救人员、逝者遗体。 | 研究员 | character | scene:PRD-S01, claim:CLAIM-01 |
| UPF-PRD-S01-02 | Environment | 抢救室转入生命维持实验室的交界空间，医学死亡和情报任务在同一张床边相撞。 | 生命维持实验室 | environment | scene:PRD-S01, claim:CLAIM-01 |
| UPF-PRD-S01-03 | Event | 组织在逝者死亡后以生命维持系统维持脑活动，并以脑波分析尝试读取记忆。 | 组织 | group | scene:PRD-S01, claim:CLAIM-01 |
| UPF-PRD-S02-01 | Entry state | 逝者脑活动被维持，脑波分析进入第一轮读取。 | 脑波分析 | event | scene:PRD-S02, claim:CLAIM-01 |
| UPF-PRD-S03-01 | Event | 与重大事件相关的关键记忆完全自闭，常规刺激、诱导和算法重构均无法打开。 | 关键记忆完全自闭 | information object | scene:PRD-S03, claim:CLAIM-02 |
| UPF-PRD-S04-01 | Causal output | 数字生命方案成为唯一可执行候选，但伦理和技术风险被同时抬高。 | 数字生命方案 | rule | scene:PRD-S04, claim:CLAIM-03 |
| UPF-PRD-S05-01 | Environment | 临时授权室，权限确认、责任豁免和注入协议被压缩在同一流程里。 | 注入协议 | information object | scene:PRD-S05, claim:CLAIM-03 |
| UPF-PRD-S06-01 | Causal output | 数字生命体醒来，但没有直接给出情报，研究员必须通过对话进入记忆。 | 数字生命体 | character | scene:PRD-S06, claim:CLAIM-03 |
| UPF-PRD-S07-01 | Roles | 研究员、数字生命体、逝者学生时代资料、旧校友记录。 | 逝者学生时代资料 | information object | scene:PRD-S07, claim:CLAIM-04 |
| UPF-PRD-S07-02 | Scene content | 她在资料中看到旧校徽、毕业照和一个熟悉的名字，才确认逝者就是学生时代暗恋过的学长。数字生命体随后复述一句旧日口头禅，研究员短暂停顿，被监听员记录为“情绪波动”。 | 学长 | character | scene:PRD-S07, claim:CLAIM-04 |
| UPF-PRD-S08-01 | Causal output | 研究员的诱导方式从技术审讯转向私人试探，数字生命体开始识别她的投射。 | 研究员 | style/pov rule | scene:PRD-S08, claim:CLAIM-04 |
| UPF-PRD-S09-01 | Roles | 研究员、数字生命体、学长潜意识保护、被保护者线索。 | 被保护者线索 | information object | scene:PRD-S09, claim:CLAIM-05 |
| UPF-PRD-S09-02 | Roles | 研究员、数字生命体、学长潜意识保护、被保护者线索。 | 研究员 | character | scene:PRD-S09, claim:CLAIM-05 |
| UPF-PRD-S09-04 | Roles | 研究员、数字生命体、学长潜意识保护、被保护者线索。 | 学长 | character | scene:PRD-S09, claim:CLAIM-05 |
| UPF-PRD-S10-01 | Scene content | 组织催促她提交可用情报，她却从片段中拼出被保护者与重大事件的关系：那个人不是简单凶手，而是被胁迫或被误导卷入触发链的人，身份一旦以原始原因上报就会遭到组织处置和审查。研究员明白，学长锁住记忆不是为了原则，而是为了一个具体的人。 | 被保护者 | character | scene:PRD-S10, claim:CLAIM-05 |
| UPF-PRD-S10-03 | Roles | 研究员、数字生命体、组织催办者、被保护者隐约档案。 | 组织 | group | scene:PRD-S10, claim:CLAIM-05 |
| UPF-PRD-S11-01 | Event | 研究员借助数字生命体理解学长潜意识后打开记忆，取得情报并化解重大事件。 | 打开记忆 | event | scene:PRD-S11, claim:CLAIM-06 |
| UPF-PRD-S11-02 | Roles | 研究员、数字生命体、学长潜意识、危机处置组。 | 研究员 | character | scene:PRD-S11, claim:CLAIM-06 |
| UPF-PRD-S11-03 | Roles | 研究员、数字生命体、学长潜意识、危机处置组。 | 数字生命体 | character | scene:PRD-S11, claim:CLAIM-06 |
| UPF-PRD-S11-04 | Scene content | 研究员不再强行撬锁，而是让数字生命体顺着学长保护那个人的逻辑说下去。她只提取能阻止重大事件的时间、地点、触发条件和阻断方式，暂时避开被保护者身份、关系和私人动机。数字生命体开始理解她不是只想完成任务。 | 被保护者 | character | scene:PRD-S11, claim:CLAIM-06 |
| UPF-PRD-S12-01 | Roles | 研究员、组织危机处置组、数字生命体、处理后的情报。 | 处理后的情报 | information object | scene:PRD-S12, claim:CLAIM-06 |
| UPF-PRD-S12-02 | Roles | 研究员、组织危机处置组、数字生命体、处理后的情报。 | 组织 | group | scene:PRD-S12, claim:CLAIM-06 |
| UPF-PRD-S13-01 | Entry state | 重大事件被化解，组织进入结案审查。 | 结案审查 | rule | scene:PRD-S13, claim:CLAIM-07 |
| UPF-PRD-S14-01 | Scene content | 研究员申请延长隔离保存时间，理由是仍需复核记忆稳定性。数字生命体指出她没有问“我想不想继续存在”，而是在问“我还能不能留下你”。这句话让她无法回答。 | 隔离保存时间 | time layer | scene:PRD-S14, claim:CLAIM-07 |
| UPF-PRD-S15-01 | Causal output | 数字生命体决定设计自己的终止，而不是等待研究员或组织决定。 | 终止 | rule | scene:PRD-S15, claim:CLAIM-08 |
| UPF-PRD-S15-02 | Roles | 数字生命体、研究员、系统权限记录、被保护者风险影子。 | 研究员 | character | scene:PRD-S15, claim:CLAIM-08 |
| UPF-PRD-S15-03 | Roles | 数字生命体、研究员、系统权限记录、被保护者风险影子。 | 数字生命体 | character | scene:PRD-S15, claim:CLAIM-08 |
| UPF-PRD-S15-04 | Scene content | 数字生命体把已有信息连起来：组织会追问，研究员会继续犹豫，被保护者仍可能被拖出。它不能控制外部系统，也不能凭空伪造权限，只能利用既有告警、日志、对话节奏和研究员误判，让终止看似系统风险控制，而不是它自己的安排。 | 组织 | group | scene:PRD-S15, claim:CLAIM-08 |
| UPF-PRD-S16-01 | Environment | 隔离系统终止界面，警报、确认框和数字生命体最后的对话叠在一起。 | 终止界面 | environment | scene:PRD-S16, claim:CLAIM-08 |
| UPF-PRD-S17-01 | Scene content | 她复查终止前日志，发现那些“系统风险提示”其实来自数字生命体对她性格的精确判断。组织只要求归档，她却在空白对话窗口前意识到，自己执行的不是关闭程序，而是一次告别。 | 终止前日志 | information object | scene:PRD-S17, claim:CLAIM-09 |
| UPF-PRD-S18-01 | Causal output | 本段以研究员长期承担后果收束，HLD 后续只能扩展余波，不能改写终止和秘密。 | 研究员 | thread | scene:PRD-S18, claim:CLAIM-09 |

## Skill Verdict

| Field | Value |
|---|---|
| Skill quality verdict | pass |
| Source closure | pass |
| Boundary obedience | pass |
| Downstream readiness | pass |
| Blocking issue | none |
| Rerun target | none |
