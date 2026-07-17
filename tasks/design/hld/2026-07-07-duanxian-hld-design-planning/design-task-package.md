# HLD 设计任务规划包：情报路径断裂到数字生命终止段

## 修订表

| 版本 | 日期 | 修订人 | 修订说明 | 验证状态 |
|---|---|---|---|---|
| v1.0 | 2026-07-07 | Agent | 首版 HLD 设计任务规划包。依据最新 PRD 与 HLD 重构计划建立 planning-only 任务矩阵，不生成 HLD 业务内容。 | 已进入 `validate_design_tasks.py` 校验 |
| v1.1 | 2026-07-07 | Agent | 覆盖修订：补充 HLD-REQ、PRD-FREEZE、故事逻辑边界的 ID 级覆盖矩阵，修正 owner artifact 与 HLD 拓扑关系，并区分可先行执行的工程任务状态。 | 已进入 `validate_design_tasks.py` 校验 |
| v1.2 | 2026-07-07 | Agent | 闭环修订：补齐 HLD artifact 01/10/11/12 的任务级闭环要求，并将 PRD Required answer 事实原子纳入验收表述。 | 已进入 `validate_design_tasks.py` 硬校验 |
| v1.3 | 2026-07-07 | Agent | 任务级修订：补充 HLD contract rule、artifact schema、final HLD schema 覆盖矩阵，并将 12 个 HLD 独立技能拆成可独立验收的工程任务。 | 已进入 `validate_design_tasks.py` 硬校验 |
| v1.4 | 2026-07-07 | Agent | 语义绑定修订：补齐 artifact source obligations 的 HLD 拓扑依赖，将 contract/schema/final schema 矩阵升级为事实级绑定校验，并明确 validator/test coverage 为 planned。 | 已通过 `validate_design_tasks.py`、相关单测与 PRD/proposal contract 回归 |
| v1.5 | 2026-07-07 | Agent | 设计规划修订：补齐 HLD refactor plan 的全局规范修改任务，并接入 `$design-planning` canonical JSON、任务 fixture 和 final acceptance 输出契约。 | 已进入强化版 `validate_design_tasks.py` 与 design-planning validator 校验 |

## Package Metadata

| Field | Value |
|---|---|
| Workflow node | `hld-design-planning` |
| Source PRD package | `docs/superpowers/runs/prd/2026-07-07-duanxian-prd-workflow/artifacts/final-prd-package.md` |
| Source HLD refactor plan | `docs/superpowers/plans/2026-07-07-novel-hld-workflow-refactor.md` |
| PRD HLD entry verdict | `blocked_pending_human_review` |
| Execution policy | `planning_only_until_prd_human_confirmation` |
| Package conclusion | 当前只能规划 HLD 设计任务与 HLD workflow 工程任务。PRD 获得人类确认并将 HLD entry verdict 更新为 `pass_to_hld` 前，不得执行 HLD 业务 artifact 生成。 |

## 根因定位

| 问题 | 根本原因 | 修复策略 |
|---|---|---|
| 仓库没有实际设计任务包 | 之前只有 HLD 重构实施计划，没有把任务规划沉淀为受控 artifact | 新增 `tasks/design/hld/.../design-task-package.md` 作为正式规划交付物 |
| HLD 任务无法按 PRD 覆盖验收 | PRD 的 HLD 交接主题、HLD-REQ、PRD-FREEZE 和故事逻辑边界没有逐项绑定到任务、artifact owner 和验收条件 | 建立三层覆盖矩阵：主题级、HLD-REQ 级、freeze/story-logic 级 |
| 阻塞态容易被绕过 | PRD 的 `blocked_pending_human_review` 只出现在 PRD 风险报告，没有进入设计任务规划语义 | 在 metadata、业务任务状态和执行边界中明确 planning-only |
| HLD 规范存在双权威 | HLD 重构计划要求 12 个技能，旧 harness 规范曾停留在 9 个技能 | 以 12 artifact topology 为准，并在矩阵中校验 owner artifact 与 skill owner 的拓扑一致性 |

## 设计任务执行边界

| 边界 | 结论 |
|---|---|
| 当前允许 | 设计任务规划、覆盖矩阵建立、validator 与 regression test 建立、blocked-run fixture 设计、HLD workflow/contract/skill 工程重构准备 |
| 当前禁止 | 生成 HLD 世界规则、人物系统、环境系统、事件系统、时间信息系统、线索系统、风格 POV 或 final HLD package |
| 解锁条件 | 最新 PRD 的 `HLD entry verdict` 从 `blocked_pending_human_review` 更新为 `pass_to_hld` |
| 最高约束 | 不得改写 PRD-S00 至 PRD-S18 的顺序、事件、因果输出、故事逻辑边界和 HLD 扩展边界 |

## PRD/HLD Coverage Matrix

| Task id | PRD handoff theme | Supports | Owner artifact | Skill owner | Acceptance | Execution boundary | Status |
|---|---|---|---|---|---|---|---|
| HLD-DESIGN-01 | 情报交接与事故现场 | PRD-S00 | artifact 02, artifact 03, artifact 05, artifact 06 | `novel-prd-support-matrix-builder`, `novel-world-rule-designer`, `novel-environment-system-designer`, `novel-event-system-designer` | 映射情报交接支撑项，并在规则、环境、事件层分别定义事故条件、交接失败原因、残片不可复原原因。 | 不得改写 PRD 的事故死亡、交接失败和最后线索转入死者记忆；不得把情报改成已经正常交接、已被组织完整掌握或可从残片直接复原。 | `planning_ready_blocked` |
| HLD-DESIGN-02 | 死亡边缘读取体系 | PRD-S01, PRD-S02 | artifact 03, artifact 05, artifact 07 | `novel-world-rule-designer`, `novel-environment-system-designer`, `novel-time-information-system-designer` | 定义脑活动维持、脑波分析、空间转换、外围记忆可见与关键记忆不可达的规则闭环。 | 不得改写 PRD 的读取失败方向，不得把技术写成成熟读取产品；不得让脑波分析直接成功读取关键记忆。 | `planning_ready_blocked` |
| HLD-DESIGN-03 | 记忆自闭机制 | PRD-S03 | artifact 03, artifact 07 | `novel-world-rule-designer`, `novel-time-information-system-designer` | 说明完全自闭在数据表现、算法日志、人物判断和信息遮蔽层级中的证据链。 | 不得改写 PRD，不得提前解释成技术故障或普通加密。 | `planning_ready_blocked` |
| HLD-DESIGN-04 | 数字生命决策和初醒 | PRD-S04, PRD-S05, PRD-S06 | artifact 03, artifact 04, artifact 07 | `novel-world-rule-designer`, `novel-character-system-designer`, `novel-time-information-system-designer` | 设计授权结构、组织分歧、执行责任、初醒受控方式和风险未消失的规则边界。 | 不得改写 PRD，不得写成成熟产品，也不得把数字生命方案写成成熟产品或无风险流程。 | `planning_ready_blocked` |
| HLD-DESIGN-05 | 旧情与焦点视角 | PRD-S07, PRD-S08 | artifact 04, artifact 07, artifact 09 | `novel-character-system-designer`, `novel-time-information-system-designer`, `novel-style-pov-system-designer` | 定义研究员确认学长身份的触发链、旧情压力、信息权限和数字生命体不是学长复活的呈现边界。 | 不得改写 PRD，不得把数字生命体写成学长复活或让视角失去研究员焦点。 | `planning_ready_blocked` |
| HLD-DESIGN-06 | 被保护者遮蔽结构 | PRD-S09, PRD-S10 | artifact 04, artifact 06, artifact 07 | `novel-character-system-designer`, `novel-event-system-designer`, `novel-time-information-system-designer` | 定义被保护者身份类型、卷入方式、暴露后果、与学长的私人关系或亏欠关系，以及遮蔽层级。 | 不得改写 PRD，不得改成抽象大义、无关旁支或纯粹加害者。 | `planning_ready_blocked` |
| HLD-DESIGN-07 | 危机情报转化 | PRD-S11, PRD-S12 | artifact 03, artifact 06, artifact 07 | `novel-world-rule-designer`, `novel-event-system-designer`, `novel-time-information-system-designer` | 设计可用情报如何转化为时间、地点、触发条件、阻断方式和行动窗口，并保留完整原因。 | 不得改写 PRD，不得绕开数字生命体和研究员，也不得让被保护者身份成为阻断危机的必要条件。 | `planning_ready_blocked` |
| HLD-DESIGN-08 | 结案与保存权限 | PRD-S13, PRD-S14 | artifact 03, artifact 04, artifact 07 | `novel-world-rule-designer`, `novel-character-system-designer`, `novel-time-information-system-designer` | 定义报告格式、结案审查、保存权限、隔离窗口、旧情投射和研究员承压机制。 | 不得改写 PRD，不得让结案无代价完成或让组织压力消失。 | `planning_ready_blocked` |
| HLD-DESIGN-09 | 终止设计 | PRD-S15, PRD-S16 | artifact 03, artifact 06, artifact 07, artifact 09 | `novel-world-rule-designer`, `novel-event-system-designer`, `novel-time-information-system-designer`, `novel-style-pov-system-designer` | 定义数字生命体如何利用既有告警、日志、系统提示、对话节奏、误判和多重确认完成终止骗局。 | 不得改写 PRD，不得改成组织命令、研究员单方决定、系统故障或无约束超能力。 | `planning_ready_blocked` |
| HLD-DESIGN-10 | 组织压力和限制 | PRD-S13, PRD-S14, PRD-S15 | artifact 03, artifact 06, artifact 07 | `novel-world-rule-designer`, `novel-event-system-designer`, `novel-time-information-system-designer` | 定义组织审查、资产评估、接管限制、复制限制、保存窗口和内部分歧。 | 不得改写 PRD，不得让组织压力消失，不得让组织直接复制、接管或抢走数字生命体终止选择，不得让组织直接抢走数字生命体终止选择，也不得让组织直接抢走终局选择权。 | `planning_ready_blocked` |
| HLD-DESIGN-11 | 事后余波 | PRD-S17, PRD-S18 | artifact 04, artifact 08, artifact 09 | `novel-character-system-designer`, `novel-thread-system-designer`, `novel-style-pov-system-designer` | 定义研究员如何理解骗局、秘密如何转为长期余痛、主线与情感线如何闭合。 | 不得改写 PRD，不得让真正原因完整公开或让研究员立即释然。 | `planning_ready_blocked` |

## HLD Requirement Coverage Matrix

| Requirement id | Design task ids | Owner artifacts | Skill owners | Supports | Acceptance | Boundary | Status |
|---|---|---|---|---|---|---|---|
| HLD-REQ-01 | HLD-DESIGN-01 | artifact 02, artifact 03, artifact 05, artifact 06 | `novel-prd-support-matrix-builder`, `novel-world-rule-designer`, `novel-environment-system-designer`, `novel-event-system-designer` | PRD-S00 | 回答接应机制、传输残片、事故发生条件、情报员在什么情况下死亡、组织如何判断正常情报路径断裂；说明为什么关键情报未能交接，为什么最后线索只能转入死者记忆。 | 不得把情报改成已经正常交接、已被组织完整掌握或可从残片直接复原。 | `planning_ready_blocked` |
| HLD-REQ-02 | HLD-DESIGN-02 | artifact 03, artifact 05, artifact 07 | `novel-world-rule-designer`, `novel-environment-system-designer`, `novel-time-information-system-designer` | PRD-S01, PRD-S02 | 回答医学状态、脑活动如何被维持、生命维持权限、脑波分析界面、抢救室到实验室的空间转换、外围记忆为何可见，以及研究员如何在场景中感到“死亡已发生但任务未结束”。 | 不得让脑波分析直接成功读取关键记忆。 | `planning_ready_blocked` |
| HLD-REQ-03 | HLD-DESIGN-03 | artifact 03, artifact 07 | `novel-world-rule-designer`, `novel-time-information-system-designer` | PRD-S03 | 回答失败证据、算法日志、刺激诱导表现、组织失败结论、“完全自闭”在画面、数据和人物判断中的表现。 | 不得把自闭原因提前解释成技术故障或普通加密。 | `planning_ready_blocked` |
| HLD-REQ-04 | HLD-DESIGN-04 | artifact 03, artifact 04, artifact 07 | `novel-world-rule-designer`, `novel-character-system-designer`, `novel-time-information-system-designer` | PRD-S04, PRD-S05, PRD-S06 | 回答谁能批准注入、支持派、反对派、为什么反对无效、授权记录、未成熟技术风险、研究员执行责任，以及数字生命体初醒时系统如何限制它。 | 不得把方案写成成熟产品，也不得消除伦理和技术不确定性。 | `planning_ready_blocked` |
| HLD-REQ-05 | HLD-DESIGN-05 | artifact 04, artifact 07, artifact 09 | `novel-character-system-designer`, `novel-time-information-system-designer`, `novel-style-pov-system-designer` | PRD-S07, PRD-S08 | 回答哪些资料或对话细节让研究员确认学长身份、学生时代资料、记忆触发物、语言习惯、研究员焦点视角规则，以及旧情如何改变提问方式。 | 不得切换成数字生命体长篇内心独白，也不得把数字生命体写成学长复活。 | `planning_ready_blocked` |
| HLD-REQ-06 | HLD-DESIGN-06 | artifact 04, artifact 06, artifact 07 | `novel-character-system-designer`, `novel-event-system-designer`, `novel-time-information-system-designer` | PRD-S09, PRD-S10 | 回答被保护者为何与重大事件有关、片段线索、责任复杂性、不能公开的原因、研究员如何确认私人保护动机，以及被保护者又为何不能被写成简单加害者。 | 不得把私人保护原因改成抽象大义。 | `planning_ready_blocked` |
| HLD-REQ-07 | HLD-DESIGN-07 | artifact 03, artifact 06, artifact 07 | `novel-world-rule-designer`, `novel-event-system-designer`, `novel-time-information-system-designer` | PRD-S11, PRD-S12 | 回答什么信息足以化解重大事件、可用情报、完整原因、行动指挥、处理后报告，以及哪些信息被研究员主动保留。 | 不得让危机解决绕开数字生命体和研究员。 | `planning_ready_blocked` |
| HLD-REQ-08 | HLD-DESIGN-08 | artifact 03, artifact 04, artifact 07 | `novel-world-rule-designer`, `novel-character-system-designer`, `novel-time-information-system-designer` | PRD-S13, PRD-S14 | 回答研究员如何在上报、保护、保存和旧情之间被制度挤压、结案审查、保存权限、隔离系统保存窗口、数字生命体对研究员投射的识别。 | 不得让结案无代价完成，也不得把保存写成单纯技术延期。 | `planning_ready_blocked` |
| HLD-REQ-09 | HLD-DESIGN-09 | artifact 03, artifact 06, artifact 07, artifact 09 | `novel-world-rule-designer`, `novel-event-system-designer`, `novel-time-information-system-designer`, `novel-style-pov-system-designer` | PRD-S15, PRD-S16 | 回答数字生命体如何理解三方风险、权限可见范围、误导研究员的路径、终止界面、最后对话、事后可识别线索，并让研究员在误判中执行终止。 | 不得把终止改成组织命令、研究员单方决定或系统故障。 | `planning_ready_blocked` |
| HLD-REQ-10 | HLD-DESIGN-11 | artifact 04, artifact 08, artifact 09 | `novel-character-system-designer`, `novel-thread-system-designer`, `novel-style-pov-system-designer` | PRD-S17, PRD-S18 | 回答研究员如何逐渐理解骗局、空置对话室、组织档案、日常生活表面、研究员长期心理代价，以及安全世界如何与未公开真相并存。 | 不得让真正原因完整公开、数字生命继续存活或研究员立即释然。 | `planning_ready_blocked` |
| HLD-REQ-11 | HLD-DESIGN-07 | artifact 03, artifact 06, artifact 07 | `novel-world-rule-designer`, `novel-event-system-designer`, `novel-time-information-system-designer` | PRD-S11, PRD-S12 | 定义时间、地点、触发条件、阻断方式和行动窗口如何足以化解危机，以及身份、关系和私人动机为什么属于完整原因。 | 不得让被保护者身份成为阻断危机的必要条件，也不得让完整原因被自然完整上报。 | `planning_ready_blocked` |
| HLD-REQ-12 | HLD-DESIGN-06 | artifact 04, artifact 06, artifact 07 | `novel-character-system-designer`, `novel-event-system-designer`, `novel-time-information-system-designer` | PRD-S09, PRD-S10 | 定义被保护者如何与重大事件有关，为什么不是简单加害者，为什么暴露会导致组织处置、审查或重新卷入，以及被保护者与学长之间的私人关系或亏欠关系。 | 不得改成抽象伦理理由、无关旁支或纯粹加害者。 | `planning_ready_blocked` |
| HLD-REQ-13 | HLD-DESIGN-09 | artifact 03, artifact 06, artifact 07, artifact 09 | `novel-world-rule-designer`, `novel-event-system-designer`, `novel-time-information-system-designer`, `novel-style-pov-system-designer` | PRD-S15, PRD-S16 | 回答数字生命体可见但不可控制的系统范围、既有告警、日志、系统提示、对话节奏、研究员误判、终止流程多重确认如何组成骗局，以及它如何在不伪造权限、不控制外部系统的前提下诱导终止。 | 不得把终止骗局写成无约束超能力、组织命令或系统故障。 | `planning_ready_blocked` |
| HLD-REQ-14 | HLD-DESIGN-10 | artifact 03, artifact 06, artifact 07 | `novel-world-rule-designer`, `novel-event-system-designer`, `novel-time-information-system-designer` | PRD-S13, PRD-S14, PRD-S15 | 回答组织为什么仍然施压、结案审查、情报缺口追问、资产评估、复制限制、接管限制，又为什么受隔离保存窗口、审查流程和终止权限限制而无法直接夺走终局选择。 | 不得让组织压力消失，也不得让组织直接抢走数字生命体终止选择。 | `planning_ready_blocked` |

## Freeze and Story Logic Coverage Matrix

| Source id | Source type | Supports | Design task ids | Owner artifacts | Skill owners | Preservation requirement | Status |
|---|---|---|---|---|---|---|---|
| PRD-FREEZE-01 | freeze_boundary | PRD-S00 | HLD-DESIGN-01 | artifact 02, artifact 03, artifact 05, artifact 06 | `novel-prd-support-matrix-builder`, `novel-world-rule-designer`, `novel-environment-system-designer`, `novel-event-system-designer` | 保留关键情报交接失败、事故死亡、最后线索转入死者记忆；不得改成情报已经正常交接、生前主动备份、主动上传或组织已经掌握完整情报。 | `planning_ready_blocked` |
| PRD-FREEZE-02 | freeze_boundary | PRD-S01, PRD-S02 | HLD-DESIGN-02 | artifact 03, artifact 05, artifact 07 | `novel-world-rule-designer`, `novel-environment-system-designer`, `novel-time-information-system-designer` | 保留死亡后生命维持、脑波分析启动、外围记忆可触碰但关键记忆不可达；不得把读取改成完全不可读或已经成功读取。 | `planning_ready_blocked` |
| PRD-FREEZE-03 | freeze_boundary | PRD-S03 | HLD-DESIGN-03 | artifact 03, artifact 07 | `novel-world-rule-designer`, `novel-time-information-system-designer` | 保留关键记忆完全自闭，常规刺激、诱导和算法重构均失败；不得让常规脑波分析直接读出关键情报。 | `planning_ready_blocked` |
| PRD-FREEZE-04 | freeze_boundary | PRD-S04, PRD-S05, PRD-S06 | HLD-DESIGN-04 | artifact 03, artifact 04, artifact 07 | `novel-world-rule-designer`, `novel-character-system-designer`, `novel-time-information-system-designer` | 保留数日倒计时、未成熟应用、授权争议和具体执行责任压力；不得把数字生命方案改成成熟、安全、常规工具。 | `planning_ready_blocked` |
| PRD-FREEZE-05 | freeze_boundary | PRD-S07, PRD-S08 | HLD-DESIGN-05 | artifact 04, artifact 07, artifact 09 | `novel-character-system-designer`, `novel-time-information-system-designer`, `novel-style-pov-system-designer` | 保留研究员发现逝者是学生时代暗恋学长，并持续受旧情冲击；不得删除旧情，也不得把旧情改成现任恋爱关系或普通同事情谊。 | `planning_ready_blocked` |
| PRD-FREEZE-06 | freeze_boundary | PRD-S09, PRD-S10 | HLD-DESIGN-06 | artifact 04, artifact 06, artifact 07 | `novel-character-system-designer`, `novel-event-system-designer`, `novel-time-information-system-designer` | 保留记忆自闭原因为学长保护与重大事件有关的人；不得把原因改成宏大伦理宣言、技术故障或抽象善恶。 | `planning_ready_blocked` |
| PRD-FREEZE-07 | freeze_boundary | PRD-S11, PRD-S12 | HLD-DESIGN-07 | artifact 03, artifact 06, artifact 07 | `novel-world-rule-designer`, `novel-event-system-designer`, `novel-time-information-system-designer` | 保留危机通过数字生命体理解学长潜意识后打开记忆而化解，完整原因未全部上报；不得让危机靠外部偶然情报或组织单独破解解决。 | `planning_ready_blocked` |
| PRD-FREEZE-08 | freeze_boundary | PRD-S13, PRD-S14 | HLD-DESIGN-08 | artifact 03, artifact 04, artifact 07 | `novel-world-rule-designer`, `novel-character-system-designer`, `novel-time-information-system-designer` | 保留上报完整原因和保存数字生命体的双重矛盾，以及保存欲望暴露旧情投射；不得让结案变成无代价成功，也不得让保存数字生命体只表现为技术决策。 | `planning_ready_blocked` |
| PRD-FREEZE-09 | freeze_boundary | PRD-S15, PRD-S16 | HLD-DESIGN-09 | artifact 03, artifact 06, artifact 07, artifact 09 | `novel-world-rule-designer`, `novel-event-system-designer`, `novel-time-information-system-designer`, `novel-style-pov-system-designer` | 保留终止由数字生命体形成主体性后设计，并由研究员在误判中执行；不得改成组织强制销毁、研究员单方面牺牲它或单纯系统关闭。 | `planning_ready_blocked` |
| PRD-FREEZE-10 | freeze_boundary | PRD-S17, PRD-S18 | HLD-DESIGN-11 | artifact 04, artifact 08, artifact 09 | `novel-character-system-designer`, `novel-thread-system-designer`, `novel-style-pov-system-designer` | 保留研究员事后理解骗局，并在真因未完整公开后带着痛苦和秘密继续生活；不得让真相完全公开、数字生命继续存活或研究员立即释然。 | `planning_ready_blocked` |
| PRD-FREEZE-11 | freeze_boundary | PRD-S11, PRD-S12 | HLD-DESIGN-07 | artifact 03, artifact 06, artifact 07 | `novel-world-rule-designer`, `novel-event-system-designer`, `novel-time-information-system-designer` | 保留可用情报与完整原因分层；不得让被保护者身份成为阻断危机的必要条件，也不得让完整原因被自然完整上报。 | `planning_ready_blocked` |
| PRD-FREEZE-12 | freeze_boundary | PRD-S09, PRD-S10 | HLD-DESIGN-06 | artifact 04, artifact 06, artifact 07 | `novel-character-system-designer`, `novel-event-system-designer`, `novel-time-information-system-designer` | 保留被保护者被胁迫或误导卷入触发链、暴露后果、私人关系或亏欠关系；不得把被保护者改成无关旁支、纯粹加害者或抽象伦理符号。 | `planning_ready_blocked` |
| PRD-FREEZE-13 | freeze_boundary | PRD-S15, PRD-S16 | HLD-DESIGN-09 | artifact 03, artifact 06, artifact 07, artifact 09 | `novel-world-rule-designer`, `novel-event-system-designer`, `novel-time-information-system-designer`, `novel-style-pov-system-designer` | 保留终止骗局能力边界：不能控制外部系统、不能凭空伪造权限、不能改写权限；不得把终止骗局写成无约束超能力、组织命令或系统故障。 | `planning_ready_blocked` |
| PRD-FREEZE-14 | freeze_boundary | PRD-S13, PRD-S14, PRD-S15 | HLD-DESIGN-10 | artifact 03, artifact 06, artifact 07 | `novel-world-rule-designer`, `novel-event-system-designer`, `novel-time-information-system-designer` | 保留组织施压、资产评估、保存窗口、审查流程、终止权限限制和不能直接复制或接管数字生命体；不得让组织压力消失，也不得让组织直接抢走数字生命体终止选择。 | `planning_ready_blocked` |
| 可用情报与完整原因分层 | story_logic_boundary | PRD-S11, PRD-S12 | HLD-DESIGN-07 | artifact 03, artifact 06, artifact 07 | `novel-world-rule-designer`, `novel-event-system-designer`, `novel-time-information-system-designer` | 保留可用情报包含阻止重大事件所需的时间、地点、触发条件、阻断方式和行动窗口；保留完整原因才包含被保护者身份、关系和私人动机，因此研究员可以化解危机，但仍能隐去完整原因。 | `planning_ready_blocked` |
| 被保护者因果关系 | story_logic_boundary | PRD-S09, PRD-S10 | HLD-DESIGN-06 | artifact 04, artifact 06, artifact 07 | `novel-character-system-designer`, `novel-event-system-designer`, `novel-time-information-system-designer` | 保留被保护者是被胁迫或被误导卷入触发链的人，不是简单加害者；保留暴露身份会导致组织处置、审查或重新卷入，并且被保护者与学长存在私人关系或亏欠关系，足以支撑学长封闭记忆和研究员隐瞒。 | `planning_ready_blocked` |
| 数字生命体终止骗局能力边界 | story_logic_boundary | PRD-S15, PRD-S16 | HLD-DESIGN-09 | artifact 03, artifact 06, artifact 07, artifact 09 | `novel-world-rule-designer`, `novel-event-system-designer`, `novel-time-information-system-designer`, `novel-style-pov-system-designer` | 保留数字生命体不能控制外部系统、不能凭空伪造权限、不能改写权限；它只能利用既有告警、日志、系统提示、对话节奏、研究员误判和终止流程多重确认，让终止看似风险控制。 | `planning_ready_blocked` |
| 组织追问压力边界 | story_logic_boundary | PRD-S13, PRD-S14, PRD-S15 | HLD-DESIGN-10 | artifact 03, artifact 06, artifact 07 | `novel-world-rule-designer`, `novel-event-system-designer`, `novel-time-information-system-designer` | 保留组织在危机解除后仍会结案审查、追问情报缺口和评估数字生命体资产价值；保留但受隔离保存窗口、审查流程和终止权限限制，不能直接复制或接管数字生命体。 | `planning_ready_blocked` |

## HLD Artifact Task Coverage Matrix

| Artifact id | Skill owner | Task id | Task purpose | Source obligations | Acceptance | Status |
|---|---|---|---|---|---|---|
| artifact 01 | `novel-world-entity-inventory-builder` | HLD-GLOBAL-01 | 建立 HLD 覆盖宇宙和初始 entity inventory。 | proposal claims, PRD-S00 至 PRD-S18, PRD-FREEZE-01 至 PRD-FREEZE-14, HLD-REQ-01 至 HLD-REQ-14, 4 条 story logic boundary | 枚举角色、组织、环境、事件、规则、信息对象、线索对象、风格/POV 约束和显式排除项；不得导入旧 HLD/LLD/writing 作为冻结事实。 | `planning_ready_blocked` |
| artifact 02 | `novel-prd-support-matrix-builder` | HLD-GLOBAL-02 | 建立 PRD support matrix。 | artifact 01, PRD-S00 至 PRD-S18, PRD-FREEZE-01 至 PRD-FREEZE-14, HLD-REQ-01 至 HLD-REQ-14, story logic boundary | 每个 scene、freeze、HLD-REQ、story logic boundary 和 inventory item 均有支撑项或显式排除项。 | `planning_ready_blocked` |
| artifact 03 | `novel-world-rule-designer` | HLD-GLOBAL-03 | 定义支撑 PRD 主干的世界规则。 | artifact 01, artifact 02, HLD-DESIGN-01, HLD-DESIGN-02, HLD-DESIGN-03, HLD-DESIGN-04, HLD-DESIGN-07, HLD-DESIGN-08, HLD-DESIGN-09, HLD-DESIGN-10 | 世界规则解释并约束 PRD 场景，不改写任何 PRD 事实。 | `planning_ready_blocked` |
| artifact 04 | `novel-character-system-designer` | HLD-GLOBAL-04 | 定义角色、关系、动机、权限和情感压力。 | artifact 01, artifact 02, artifact 03, HLD-DESIGN-04, HLD-DESIGN-05, HLD-DESIGN-06, HLD-DESIGN-08, HLD-DESIGN-11 | 角色系统覆盖研究员、学长、数字生命体、被保护者、组织相关角色，不进入 LLD 外貌或 prose。 | `planning_ready_blocked` |
| artifact 05 | `novel-environment-system-designer` | HLD-GLOBAL-05 | 定义叙事环境、空间关系和状态变化。 | artifact 01, artifact 02, artifact 03, HLD-DESIGN-01, HLD-DESIGN-02 | 环境系统支撑事故现场、生命维持、读取和数字生命隔离空间。 | `planning_ready_blocked` |
| artifact 06 | `novel-event-system-designer` | HLD-GLOBAL-06 | 定义可见、背景、隐藏和隐含事件链。 | artifact 01, artifact 02, artifact 03, artifact 04, artifact 05, HLD-DESIGN-01, HLD-DESIGN-06, HLD-DESIGN-07, HLD-DESIGN-09, HLD-DESIGN-10 | 事件链解释 PRD 因果，不删除、替换或重排 PRD 主干场景。 | `planning_ready_blocked` |
| artifact 07 | `novel-time-information-system-designer` | HLD-GLOBAL-07 | 定义时间结构、信息流、揭示/遮蔽机制和信息权限。 | artifact 01, artifact 02, artifact 03, artifact 04, artifact 06, HLD-DESIGN-02 至 HLD-DESIGN-10 | 信息系统保留 PRD 已冻结的信息可见性、可用情报/完整原因分层和终止骗局能力边界。 | `planning_ready_blocked` |
| artifact 08 | `novel-thread-system-designer` | HLD-GLOBAL-08 | 定义主线、支线、隐藏线、情感线和主题线的节点分布、交叉和闭合。 | artifact 01, artifact 02, artifact 04, artifact 06, artifact 07, HLD-DESIGN-11, story logic boundary | 线索系统支撑 PRD 主干并闭合，不新增改写 PRD 因果答案的主线或隐藏线。 | `planning_ready_blocked` |
| artifact 09 | `novel-style-pov-system-designer` | HLD-GLOBAL-09 | 定义语言风格、POV、叙述距离、对话/通信规则和禁用表达。 | artifact 01, artifact 02, artifact 04, artifact 05, artifact 07, artifact 08, HLD-DESIGN-05, HLD-DESIGN-09, HLD-DESIGN-11 | 风格/POV 支撑研究员 focal character 和数字生命主体性，不生成正文样章。 | `planning_ready_blocked` |
| artifact 10 | `novel-hld-inventory-reconciler` | HLD-GLOBAL-10 | 归并设计期 amendment request 并生成 final inventory。 | artifact 01 至 artifact 09, amendment request | 所有新增支撑实体必须接受进 final inventory 或拒绝并移除；未决 request 阻塞 HLD packaging。 | `planning_ready_blocked` |
| artifact 11 | `novel-hld-integrator` | HLD-GLOBAL-11 | 装配 final HLD 并产出事实级 HLD Source Map。 | artifact 01 至 artifact 10, PRD canonical facts, HLD-REQ, freeze, story logic boundary | HLD Source Map 逐 fact atom 映射，不以同 ID 改写 PRD 事实；不新增业务设计。 | `planning_ready_blocked` |
| artifact 12 | `novel-hld-integrity-checker` | HLD-GLOBAL-12 | 输出 HLD risk report、verdict consistency matrix 和 LLD entry verdict。 | artifact 01 至 artifact 11, HLD contract rules | P0/P1 阻塞 Agent quality pass、verdict consistency matrix 和 LLD entry verdict；风险报告只检查和路由，不直接修正文档。 | `planning_ready_blocked` |

## HLD Contract Rule Coverage Matrix

| Rule id | Design task ids | Engineering task ids | Planned validator coverage | Planned regression proof | Acceptance | Status |
|---|---|---|---|---|---|---|
| HLD-CONTRACT-01 | HLD-GLOBAL-01 至 HLD-GLOBAL-12 | HLD-ENG-01, HLD-ENG-05 | `validate_hld_contract.py::validate_hld_entry_gate` | `test_validate_hld_contract.py::test_hld_blocks_without_prd_pass_to_hld` | PRD 未确认时只能生成 blocked manifest，不得生成 HLD 业务 artifact。 | `ready_before_prd_confirmation` |
| HLD-CONTRACT-02 | HLD-GLOBAL-01 至 HLD-GLOBAL-12 | HLD-ENG-02 | `validate_hld_contract.py::validate_harness_purity` | `test_validate_hld_contract.py::test_harness_contains_no_business_design` | harness 只能校验、调度、路由、打包和处理 reopen，不写世界、人物、环境、事件、线索、风格或 POV 内容。 | `ready_before_prd_confirmation` |
| HLD-CONTRACT-03 | HLD-GLOBAL-01 至 HLD-GLOBAL-12 | HLD-SKILL-01 至 HLD-SKILL-12 | `validate_hld_contract.py::validate_independent_skill_owners` | `test_validate_hld_contract.py::test_every_hld_business_gate_has_independent_skill_owner` | 每个 HLD business gate 只有一个独立 skill owner，并可单独验收。 | `ready_before_prd_confirmation` |
| HLD-CONTRACT-04 | HLD-GLOBAL-11, HLD-GLOBAL-12 | HLD-ENG-01, HLD-ENG-02 | `validate_hld_contract.py::validate_artifact_dag` | `test_validate_hld_contract.py::test_artifact_11_does_not_depend_on_12` | artifact 11 不依赖 artifact 12；final package 只依赖 artifact 11 和 artifact 12。 | `ready_before_prd_confirmation` |
| HLD-CONTRACT-05 | HLD-GLOBAL-01 至 HLD-GLOBAL-12 | HLD-SKILL-01 至 HLD-SKILL-12 | `validate_hld_contract.py::validate_universal_skill_verdict_schema` | `test_validate_hld_contract.py::test_every_artifact_has_structured_skill_verdict` | artifact 01-12 均以结构化 `## Skill Verdict` 结尾，不允许 prose verdict。 | `ready_before_prd_confirmation` |
| HLD-CONTRACT-06 | HLD-GLOBAL-02, HLD-GLOBAL-11 | HLD-ENG-01, HLD-SKILL-02, HLD-SKILL-11 | `validate_hld_contract.py::validate_source_reference_grammar` | `test_validate_hld_contract.py::test_support_refs_use_allowed_source_grammar` | 所有 support item 只能追溯到 scene、freeze、hldreq、claim、storylogic 或 inventory 引用。 | `ready_before_prd_confirmation` |
| HLD-CONTRACT-07 | HLD-GLOBAL-02, HLD-GLOBAL-11 | HLD-ENG-01, HLD-SKILL-11 | `validate_hld_contract.py::validate_prd_canonical_fact_preservation` | `test_validate_hld_contract.py::test_same_source_scene_fact_rewrite_fails` | PRD scene id、顺序、事件、因果输出、故事逻辑边界和 HLD expansion boundary 不得被重写。 | `ready_before_prd_confirmation` |
| HLD-CONTRACT-08 | HLD-GLOBAL-03 至 HLD-GLOBAL-09 | HLD-SKILL-03 至 HLD-SKILL-09 | `validate_hld_contract.py::validate_supported_world_system_facts` | `test_validate_hld_contract.py::test_unsupported_core_hld_fact_fails` | 新增世界系统事实必须支撑 PRD/proposal，不得成为无源核心设定。 | `ready_before_prd_confirmation` |
| HLD-CONTRACT-09 | HLD-GLOBAL-01, HLD-GLOBAL-11 | HLD-ENG-01, HLD-ENG-04 | `validate_hld_contract.py::validate_legacy_input_rejection` | `test_validate_hld_contract.py::test_legacy_hld_lld_writing_are_not_frozen_inputs` | 旧 PRD/HLD/LLD/writing 只能作为 legacy reference，不得作为冻结事实输入。 | `ready_before_prd_confirmation` |
| HLD-CONTRACT-10 | HLD-GLOBAL-01 | HLD-SKILL-01 | `validate_hld_contract.py::validate_world_entity_inventory_coverage` | `test_validate_hld_contract.py::test_initial_inventory_covers_required_entity_types` | 初始 inventory 覆盖角色、组织、环境、事件、规则、信息对象、thread object、style/POV constraint 和显式排除项。 | `ready_before_prd_confirmation` |
| HLD-CONTRACT-11 | HLD-GLOBAL-02, HLD-GLOBAL-10 | HLD-SKILL-02, HLD-SKILL-10 | `validate_hld_contract.py::validate_support_matrix_coverage` | `test_validate_hld_contract.py::test_support_matrix_covers_scenes_freeze_hldreq_storylogic_inventory` | support matrix 覆盖 PRD-S00 至 PRD-S18、HLD-REQ、PRD-FREEZE、story logic boundary 和未排除 inventory item。 | `ready_before_prd_confirmation` |
| HLD-CONTRACT-12 | HLD-GLOBAL-12 | HLD-SKILL-12 | `validate_hld_contract.py::validate_p0_p1_verdict_gate` | `test_validate_hld_contract.py::test_unresolved_p0_p1_blocks_agent_quality_and_lld_entry` | 任何未关闭 P0/P1 均阻塞 Agent quality pass 和 LLD entry。 | `ready_before_prd_confirmation` |
| HLD-CONTRACT-13 | HLD-GLOBAL-03 至 HLD-GLOBAL-09 | HLD-SKILL-03 至 HLD-SKILL-09 | `validate_hld_contract.py::validate_business_artifact_closure` | `test_validate_hld_contract.py::test_business_artifacts_prove_inventory_support_boundary_and_no_prose_leakage` | world、character、environment、event、time/information、thread、style/POV artifact 均证明 inventory coverage、PRD support、boundary obedience 和 no LLD/prose leakage。 | `ready_before_prd_confirmation` |
| HLD-CONTRACT-14 | HLD-GLOBAL-11 | HLD-ENG-01, HLD-SKILL-11 | `validate_hld_contract.py::validate_final_hld_schema_and_source_map` | `test_validate_hld_contract.py::test_final_hld_missing_schema_or_fact_atoms_fails` | final HLD schema、Source Map fact atom、expansion mode 和 support mechanism 缺失时阻塞 packaging。 | `ready_before_prd_confirmation` |
| HLD-CONTRACT-15 | HLD-GLOBAL-12 | HLD-SKILL-12 | `validate_hld_contract.py::validate_lld_entry_state_machine` | `test_validate_hld_contract.py::test_lld_entry_verdict_state_machine_is_closed` | LLD entry verdict 必须由 Agent quality、human review state 和 P0/P1 状态机械推出。 | `ready_before_prd_confirmation` |
| HLD-CONTRACT-16 | HLD-GLOBAL-10, HLD-GLOBAL-11 | HLD-SKILL-10, HLD-SKILL-11 | `validate_hld_contract.py::validate_inventory_amendment_reconciliation` | `test_validate_hld_contract.py::test_unreconciled_or_rejected_used_amendment_fails` | 所有 amendment request 在 integration 前接受入 final inventory 或拒绝并移除，未决项阻塞。 | `ready_before_prd_confirmation` |
| HLD-CONTRACT-17 | HLD-GLOBAL-11 | HLD-SKILL-11 | `validate_hld_contract.py::validate_story_logic_source_map_preservation` | `test_validate_hld_contract.py::test_story_logic_boundary_missing_or_rewritten_fails` | 每条 PRD story logic boundary 必须在 HLD Source Map 中以 support mechanism 和 `preserved` 状态保留。 | `ready_before_prd_confirmation` |
| HLD-CONTRACT-18 | HLD-GLOBAL-12 | HLD-ENG-01, HLD-SKILL-12 | `validate_hld_contract.py::validate_contract_rule_executable_coverage_and_convergence` | `test_validate_hld_contract.py::test_contract_rules_and_convergence_have_executable_proof` | 每条 contract rule 具备 validator function 和 regression test；P0/P1 convergence row 具备 stable id、root cause、fix hypothesis、regression proof、attempt count、rerun target 和 status。 | `ready_before_prd_confirmation` |

## HLD Artifact Schema Coverage Matrix

| Artifact id | Required table | Required columns | Owner skill | Engineering task id | Validation target | Status |
|---|---|---|---|---|---|---|
| artifact 01 | `## Initial world entity inventory` | `Inventory id`, `Entity type`, `Entity name`, `Required HLD owner`, `Upstream evidence`, `Source`, `Initial status` | `novel-world-entity-inventory-builder` | HLD-SKILL-01 | `validate_hld_contract.py::validate_artifact_01_schema` | `ready_before_prd_confirmation` |
| artifact 02 | `## PRD support matrix` | `Support id`, `Supports`, `Support type`, `Required HLD owner`, `Required answer`, `Boundary`, `Source`, `Support status` | `novel-prd-support-matrix-builder` | HLD-SKILL-02 | `validate_hld_contract.py::validate_artifact_02_schema` | `ready_before_prd_confirmation` |
| artifact 03 | `## World rule design table` | `Rule id`, `Rule type`, `Design fact`, `Supports`, `Boundary`, `Source`, `LLD handoff`, `Amendment request` | `novel-world-rule-designer` | HLD-SKILL-03 | `validate_hld_contract.py::validate_artifact_03_schema` | `ready_before_prd_confirmation` |
| artifact 04 | `## Character system table` | `Character id`, `Role type`, `Function`, `Relationship/motivation`, `Information permission`, `Supports`, `Source`, `LLD handoff`, `Amendment request` | `novel-character-system-designer` | HLD-SKILL-04 | `validate_hld_contract.py::validate_artifact_04_schema` | `ready_before_prd_confirmation` |
| artifact 05 | `## Environment system table` | `Environment id`, `Environment type`, `Function`, `Spatial relation`, `State change`, `Supports`, `Source`, `LLD handoff`, `Amendment request` | `novel-environment-system-designer` | HLD-SKILL-05 | `validate_hld_contract.py::validate_artifact_05_schema` | `ready_before_prd_confirmation` |
| artifact 06 | `## Event system table` | `Event id`, `Event type`, `Causal role`, `Visibility`, `Participants`, `Consequences`, `Supports`, `Source`, `LLD handoff`, `Amendment request` | `novel-event-system-designer` | HLD-SKILL-06 | `validate_hld_contract.py::validate_artifact_06_schema` | `ready_before_prd_confirmation` |
| artifact 07 | `## Time and information table` | `Info id`, `Time layer`, `Information object`, `Known by`, `Hidden from`, `Reveal condition`, `Supports`, `Source`, `LLD handoff`, `Amendment request` | `novel-time-information-system-designer` | HLD-SKILL-07 | `validate_hld_contract.py::validate_artifact_07_schema` | `ready_before_prd_confirmation` |
| artifact 08 | `## Thread system table` | `Thread id`, `Thread type`, `Thread function`, `Thread anchor refs`, `Required pressure refs`, `Core question`, `Node distribution`, `Thread progression`, `Crossover`, `Closure state`, `Closure outcome`, `Supports`, `Source`, `LLD handoff`, `Amendment request` | `novel-thread-system-designer` | HLD-SKILL-08 | `validate_hld_contract.py::validate_artifact_08_schema` | `ready_before_prd_confirmation` |
| artifact 09 | `## Style and POV table` | `Style/POV id`, `Rule type`, `Access policy`, `Information refs`, `Thread refs`, `Reader disclosure mode`, `Language profile`, `Design fact`, `POV permission`, `Prohibited expression`, `Supports`, `Source`, `LLD handoff`, `Amendment request` | `novel-style-pov-system-designer` | HLD-SKILL-09 | `validate_hld_contract.py::validate_artifact_09_schema` | `ready_before_prd_confirmation` |
| artifact 10 | `## Inventory amendment disposition` | `Request id`, `Requested entity`, `Requested by artifact`, `Decision`, `Final inventory id`, `Reason`, `Source`, `Support status` | `novel-hld-inventory-reconciler` | HLD-SKILL-10 | `validate_hld_contract.py::validate_artifact_10_schema` | `ready_before_prd_confirmation` |
| artifact 11 | `## HLD Source Map` | `HLD fact id`, `Fact type`, `Upstream fact atom`, `HLD fact atom`, `Source refs`, `Owner artifact`, `Final inventory id`, `Expansion mode`, `Support mechanism`, `LLD handoff target`, `Preservation status` | `novel-hld-integrator` | HLD-SKILL-11 | `validate_hld_contract.py::validate_artifact_11_schema` | `ready_before_prd_confirmation` |
| artifact 12 | `## Output; ## Risks; ## Verdict consistency matrix; ## Environment closure checks; ## Event closure checks; ## Information closure checks; ## Thread closure checks; ## Style/POV closure checks; ## HLD Convergence Log` | `Field`, `Value`, `Risk`, `Severity`, `Handling`, `Blocking verdict effect`, `Verdict`, `Required condition`, `Actual evidence`, `Consistency`, `Style/POV id`, `Rule type`, `Access policy`, `Information refs`, `Thread refs`, `Reader disclosure mode`, `Language profile`, `Design fact`, `POV permission`, `Prohibited expression`, `LLD handoff`, `Evidence`, `Stable issue id`, `Root cause`, `Fix hypothesis`, `Regression proof`, `Attempt count`, `Rerun target`, `Status` | `novel-hld-integrity-checker` | HLD-SKILL-12 | `validate_hld_contract.py::validate_artifact_12_schema` | `ready_before_prd_confirmation` |

## Final HLD Schema Coverage Matrix

| Section | Source artifact | Engineering task id | Validation target | Status |
|---|---|---|---|---|
| Revision table | harness package | HLD-ENG-02 | `validate_hld_contract.py::validate_final_schema_revision_table` | `ready_before_prd_confirmation` |
| Input gate proof | harness input gate | HLD-ENG-02 | `validate_hld_contract.py::validate_final_schema_input_gate_proof` | `ready_before_prd_confirmation` |
| HLD scope and exclusions | artifact 01 | HLD-SKILL-01 | `validate_hld_contract.py::validate_final_schema_scope_and_exclusions` | `ready_before_prd_confirmation` |
| World entity inventory | artifacts 01, 10 | HLD-SKILL-01, HLD-SKILL-10 | `validate_hld_contract.py::validate_final_schema_world_entity_inventory` | `ready_before_prd_confirmation` |
| PRD support matrix | artifacts 02, 10 | HLD-SKILL-02, HLD-SKILL-10 | `validate_hld_contract.py::validate_final_schema_prd_support_matrix` | `ready_before_prd_confirmation` |
| Worldview and world rules | artifact 03 | HLD-SKILL-03 | `validate_hld_contract.py::validate_final_schema_worldview_and_rules` | `ready_before_prd_confirmation` |
| World structure | artifacts 03, 05, 07 | HLD-SKILL-03, HLD-SKILL-05, HLD-SKILL-07 | `validate_hld_contract.py::validate_final_schema_world_structure` | `ready_before_prd_confirmation` |
| Character system | artifact 04 | HLD-SKILL-04 | `validate_hld_contract.py::validate_final_schema_character_system` | `ready_before_prd_confirmation` |
| Environment system | artifact 05 | HLD-SKILL-05 | `validate_hld_contract.py::validate_final_schema_environment_system` | `ready_before_prd_confirmation` |
| Event system | artifact 06 | HLD-SKILL-06 | `validate_hld_contract.py::validate_final_schema_event_system` | `ready_before_prd_confirmation` |
| Time and information system | artifact 07 | HLD-SKILL-07 | `validate_hld_contract.py::validate_final_schema_time_information_system` | `ready_before_prd_confirmation` |
| Thread system | artifact 08 | HLD-SKILL-08 | `validate_hld_contract.py::validate_final_schema_thread_system` | `ready_before_prd_confirmation` |
| Style and POV system | artifact 09 | HLD-SKILL-09 | `validate_hld_contract.py::validate_final_schema_style_pov_system` | `ready_before_prd_confirmation` |
| HLD Source Map | artifact 11 | HLD-SKILL-11 | `validate_hld_contract.py::validate_final_schema_hld_source_map` | `ready_before_prd_confirmation` |
| LLD handoff index | artifact 11 | HLD-SKILL-11 | `validate_hld_contract.py::validate_final_schema_lld_handoff_index` | `ready_before_prd_confirmation` |
| HLD risk report and LLD entry verdict | artifact 12 | HLD-SKILL-12 | `validate_hld_contract.py::validate_final_schema_risk_report_and_lld_verdict` | `ready_before_prd_confirmation` |

## HLD Workflow Engineering Task Matrix

| Task id | Task | Output | Acceptance | Status |
|---|---|---|---|---|
| HLD-ENG-01 | 建立 HLD contract 与 validator | `2026-07-07-novel-hld-contract.json`、`validate_hld_contract.py`、测试 | 能检查 12 artifact topology、Source Map、risk verdict、convergence log 和 PRD gate | `ready_before_prd_confirmation` |
| HLD-ENG-02 | 创建 `novel-hld-workflow` harness | `skills/novel-hld-workflow/SKILL.md` | harness 只调度、登记、路由、打包和验收，不写业务内容 | `ready_before_prd_confirmation` |
| HLD-ENG-03 | 同步全局 workflow 规范中的 HLD 节点定义 | `docs/superpowers/specs/2026-07-05-novel-harness-workflows-and-skills-design.md`、`docs/superpowers/specs/2026-07-05-novel-creation-workflow-design.md` | 两份全局规范必须与 12 artifact topology、HLD entry gate、optional human review、Source Map 和 convergence protocol 一致，消除旧 9-skill 或 key-scene HLD 权威。 | `ready_before_prd_confirmation` |
| HLD-SKILL-01 | 创建 world entity inventory 独立技能 | `skills/novel-world-entity-inventory-builder/SKILL.md` | 技能只负责 artifact 01，输出 initial inventory schema、source closure、exclusion rationale 和 Skill Verdict。 | `ready_before_prd_confirmation` |
| HLD-SKILL-02 | 创建 PRD support matrix 独立技能 | `skills/novel-prd-support-matrix-builder/SKILL.md` | 技能只负责 artifact 02，覆盖 scene、freeze、HLD-REQ、story logic boundary 和 inventory support。 | `ready_before_prd_confirmation` |
| HLD-SKILL-03 | 创建 world rule 独立技能 | `skills/novel-world-rule-designer/SKILL.md` | 技能只负责 artifact 03，定义世界规则并证明 PRD support、boundary obedience 和 no prose leakage。 | `ready_before_prd_confirmation` |
| HLD-SKILL-04 | 创建 character system 独立技能 | `skills/novel-character-system-designer/SKILL.md` | 技能只负责 artifact 04，定义角色、关系、动机、权限和 LLD handoff，不写小传或正文。 | `ready_before_prd_confirmation` |
| HLD-SKILL-05 | 创建 environment system 独立技能 | `skills/novel-environment-system-designer/SKILL.md` | 技能只负责 artifact 05，定义环境、空间关系、状态变化和 scene support。 | `ready_before_prd_confirmation` |
| HLD-SKILL-06 | 创建 event system 独立技能 | `skills/novel-event-system-designer/SKILL.md` | 技能只负责 artifact 06，定义 visible/background/hidden/implied event chain 和因果支撑。 | `ready_before_prd_confirmation` |
| HLD-SKILL-07 | 创建 time and information system 独立技能 | `skills/novel-time-information-system-designer/SKILL.md` | 技能只负责 artifact 07，定义时间结构、信息流、遮蔽/揭示机制和信息权限。 | `ready_before_prd_confirmation` |
| HLD-SKILL-08 | 创建 thread system 独立技能 | `skills/novel-thread-system-designer/SKILL.md` | 技能只负责 artifact 08，定义主线、支线、隐藏线、情感线、主题线、节点分布和闭合。 | `ready_before_prd_confirmation` |
| HLD-SKILL-09 | 创建 style and POV system 独立技能 | `skills/novel-style-pov-system-designer/SKILL.md` | 技能只负责 artifact 09，定义语言风格、POV、叙述距离、对话/通信规则和禁用表达。 | `ready_before_prd_confirmation` |
| HLD-SKILL-10 | 创建 inventory reconciler 独立技能 | `skills/novel-hld-inventory-reconciler/SKILL.md` | 技能只负责 artifact 10，接受或拒绝 amendment request，生成 final inventory 和 final support closure。 | `ready_before_prd_confirmation` |
| HLD-SKILL-11 | 创建 HLD integrator 独立技能 | `skills/novel-hld-integrator/SKILL.md` | 技能只负责 artifact 11，装配 final HLD、final schema coverage、fact-level Source Map 和 LLD handoff index，不新增业务事实。 | `ready_before_prd_confirmation` |
| HLD-SKILL-12 | 创建 HLD integrity checker 独立技能 | `skills/novel-hld-integrity-checker/SKILL.md` | 技能只负责 artifact 12，输出 risk report、verdict consistency matrix、LLD entry verdict 和 HLD Convergence Log。 | `ready_before_prd_confirmation` |
| HLD-ENG-04 | 降级 legacy `novel-hld-writer` | `skills/novel-hld-writer/SKILL.md` legacy warning 或 compatibility shim | 旧 writer 不再作为 HLD 活跃入口，并明确指向 `novel-hld-workflow`。 | `ready_before_prd_confirmation` |
| HLD-ENG-05 | 建立 blocked/pass fixture | `docs/superpowers/runs/hld/...` fixtures | PRD pending 时只允许 blocked manifest；PRD confirmed 后才要求 artifact 01-12 | `ready_before_prd_confirmation` |

## 验收规则

| 规则 | 必须满足 |
|---|---|
| 任务包存在性 | `tasks/design/hld/2026-07-07-duanxian-hld-design-planning/design-task-package.md` 必须存在 |
| PRD 阻塞语义 | metadata 必须记录 `blocked_pending_human_review` 与 `planning_only_until_prd_human_confirmation` |
| 主题覆盖完整性 | PRD `HLD 交接要求` 表中的 11 个主题必须全部出现在 `PRD/HLD Coverage Matrix` |
| HLD-REQ 覆盖完整性 | PRD artifact 07 中的 `HLD-REQ-01` 至 `HLD-REQ-14` 必须全部出现在 `HLD Requirement Coverage Matrix` |
| 冻结边界覆盖完整性 | PRD artifact 06 中的 `PRD-FREEZE-01` 至 `PRD-FREEZE-14` 必须全部出现在 `Freeze and Story Logic Coverage Matrix` |
| 故事逻辑覆盖完整性 | PRD 最终文档中的 4 条故事逻辑边界必须全部出现在 `Freeze and Story Logic Coverage Matrix` |
| owner topology | 每个 owner artifact 必须与 HLD 12 artifact topology 中的 skill owner 一致 |
| HLD contract rule 覆盖 | `HLD-CONTRACT-01` 至 `HLD-CONTRACT-18` 必须全部进入 `HLD Contract Rule Coverage Matrix`，并绑定 planned validator coverage 与 planned regression proof |
| Artifact schema 覆盖 | artifact 01-12 必须全部进入 `HLD Artifact Schema Coverage Matrix`，并声明 required table、required columns、owner skill 和 validation target |
| Final HLD schema 覆盖 | final HLD 的固定 sections 必须按规范顺序进入 `Final HLD Schema Coverage Matrix` |
| 独立技能工程任务 | 12 个 HLD 独立技能必须分别进入 `HLD Workflow Engineering Task Matrix`，不得用一个聚合任务替代 |
| 越界防护 | 阻塞态下所有 HLD 业务设计任务状态必须为 blocked 或 planning-ready-blocked，不得出现业务 HLD artifact 执行状态 |
| 工程任务状态 | workflow/contract/skill/fixture 工程任务可标记为 `ready_before_prd_confirmation`，但不得生成 HLD 业务内容 |
| PRD 不可改写 | 每个 coverage row 的执行边界必须显式声明不得改写 PRD |

## 参考文献

| 编号 | 文献 |
|---|---|
| R1 | `docs/superpowers/runs/prd/2026-07-07-duanxian-prd-workflow/artifacts/final-prd-package.md` |
| R2 | `docs/superpowers/runs/prd/2026-07-07-duanxian-prd-workflow/artifacts/09-prd-risk-report.md` |
| R3 | `docs/superpowers/runs/prd/2026-07-07-duanxian-prd-workflow/artifacts/06-freeze-boundaries.md` |
| R4 | `docs/superpowers/runs/prd/2026-07-07-duanxian-prd-workflow/artifacts/07-hld-expansion-requirements.md` |
| R5 | `docs/superpowers/plans/2026-07-07-novel-hld-workflow-refactor.md` |
| R6 | `docs/superpowers/specs/2026-07-05-novel-creation-workflow-design.md` |
| R7 | `docs/superpowers/specs/2026-07-05-novel-harness-workflows-and-skills-design.md` |
