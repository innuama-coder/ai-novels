# 第二步定向修正指令

判决：`design_verdict=FAIL`。输入候选 `c30de6bb2f76342867b5c3e21c347e1162368265`，定义 `4ce28e8a903adce69579fe08b51bf2b6ff3d842d`，清单 `31dfbbd8b919f5851700cedbc64204c8344e793d9fb5ac5247483861091ce924`。`loop_index=2`，`remaining_revision_budget=1`。由编排方将本单交回第二步实施责任人，在其单独授权分支修订；本验收作业不改U/。不是自动启动新作业或自动修改预算。

执行顺序：先ACC-001建立真实来源和消费定位，再ACC-002/003修复信息链，ACC-004统一终局知识时序，ACC-005收紧条件消费，ACC-006校正回归口径；交叉影响需一起复验。D02的选项批准由Owner提供，等待不计为实现FAIL次数；其余独立修正可继续。修订后递增包版本并实算清单，旧候选结果失效。

各记录用JSON代码块表达定义书§6.4字段（结构与YAML等价）；完整路径的U/缩写定义同 findings.md。未要求新增凶手、袭击机制或正文。


## ACC-001

```json
{
  "finding_id": "ACC-001",
  "definition_commit": "4ce28e8a903adce69579fe08b51bf2b6ff3d842d",
  "implementation_commit": "c30de6bb2f76342867b5c3e21c347e1162368265",
  "manifest_sha256": "31dfbbd8b919f5851700cedbc64204c8344e793d9fb5ac5247483861091ce924",
  "severity": "high",
  "issue_refs": [
    5
  ],
  "failed_checks": [
    "6.1-1",
    "6.1-2",
    "6.1-6",
    "REG-05",
    "6.1-7"
  ],
  "expected": "定义书 §2.2、§3.2、§5 步骤4/8、§6.2 REG-05：全部人物控制有来源，设计字段逐项可回读，无悬空引用；ID集合相同不等于语义闭合。",
  "observed": "06:55,182 使用 UPG-CTRL-ACT-LIFE，06:163 使用 UPG-CTRL-ACT-CRISIS，06:170,259 使用 UPG-CTRL-EVENTS；01 的72条控制中三个ID均不存在。12 /control_trace/entries/47、48、69 实际登记的是 LIFE、CRISIS、MEVT-0。另 E02 /characters/relationship_networks/0、/characters/role_coverage/0、/characters/role_coverage/1 没有01条目；其中三层关系必须按最短距离计算的控制没有可核验设计落点。12 多项 design_fields 只指向“04”“06”“08 全文”，不能证明自然语言字段的逐项推导。",
  "root_owner": "第二步：01控制投影与06/12追踪组装。根因是已登记ID集合自洽被当作来源覆盖及目标字段闭合，旧命名残留未做消费端解析。",
  "correction": {
    "inputs": [
      "定义书 §3.2/§5步骤4、8/§6.2 REG-05",
      "E02 /characters/relationship_networks、/characters/role_coverage",
      "U/01、06、12、13"
    ],
    "actions": [
      "从批准源重新枚举人物控制，为三个遗漏源对象分别登记或给出精确等价承接证据；不得仅增加计数。",
      "逐个修正06的三个未注册ID，并反向扫描全部产物的完整ID及缩写引用。",
      "把12的宽泛文档级链接细化到具体字段/表行/场景义务及推导理由；对每个高风险控制及新增遗漏控制实做回读。",
      "更新13的覆盖声明、回归证据与manifest；不要把修复追踪解释为正式HLD准入。"
    ],
    "expected_outputs": [
      "U/01-control-register.json",
      "U/06-causal-and-event-map.json",
      "U/12-traceability-and-handoff.json",
      "U/13-regression-results.md",
      "U/manifest.json"
    ],
    "forbidden_shortcuts": [
      "给不存在的ID附同名标签但不绑定真实源",
      "只比较72对72便宣称逐字段闭合",
      "伪造缺失P1或直接更改批准源"
    ]
  },
  "affected_consumers": [
    "04全部人物控制",
    "06所有事件引用",
    "09八单元",
    "12控制追踪与独立消费"
  ],
  "retest": [
    "REG-05",
    "全量源Pointer/hash/ID与消费端引用",
    "四个high完整链路",
    "NEG-AUTHORITY",
    "NEG-STATE",
    "NEG-PACKAGE",
    "全局硬约束"
  ],
  "owner_decision_required": false,
  "loop_index": 2,
  "remaining_revision_budget": 1
}
```


## ACC-002

```json
{
  "finding_id": "ACC-002",
  "definition_commit": "4ce28e8a903adce69579fe08b51bf2b6ff3d842d",
  "implementation_commit": "c30de6bb2f76342867b5c3e21c347e1162368265",
  "manifest_sha256": "31dfbbd8b919f5851700cedbc64204c8344e793d9fb5ac5247483861091ce924",
  "severity": "high",
  "issue_refs": [
    9,
    10
  ],
  "failed_checks": [
    "6.1-2",
    "6.1-6",
    "REG-09",
    "REG-10",
    "6.1-7"
  ],
  "expected": "定义书 §1.10、§3.3、§3.4、§6.2 REG-09/10：每个知识增量有发送者、文字内容范围、接收者、权限和发送≤接收≤使用；不能以“文字已输入”补缺口。",
  "observed": "09:32,34-35 与10:6,8要求初醒对首条核对文字回应；07:7,9 的IO-06/08却都是R-07→沈逾，双向IO-07最早在E-04.1；没有E-03回应前的沈逾→R-07输入。09:103把IO-16称为R-07的合法告知文字，但07:17 receiver只有项目及两国、channel为正式通报；09:91明确写结果告知文字要另作后续行登记，31行台账中没有该行。06 /events/9 的危机后评估由此缺合法到达证据。",
  "root_owner": "第二步：06因果输入→07信息台账的展开遗漏，并由09把项目获知混同实例获知。",
  "correction": {
    "inputs": [
      "E02 /world/environments/2、/world/environments/10",
      "定义书 §3.3/§3.4",
      "U/06 E-03/E-09/E-10、07 IO-06/07/08/16、09 AWAKE/BLOCKADE/FAREWELL"
    ],
    "actions": [
      "在既有文字接口内明确首条核对输入的发送者、内容范围、授权、接收和回应依赖；不要求代写对白。",
      "把项目收到危机通报与实例经文字获知分为可核验的不同传递步骤；或取消实例对该事实的依赖并同步重设计因果。",
      "让09引用实际存在的07对象，移除“后续登记”占位；检查全部知识增量，不只补一个ID。",
      "以IO-11合法转述为对照，同时测试缺转述、接收晚于推断、只发送未接收等情形。",
      "结合独立消费G02/G03/G04/G05/G09/G12，澄清材料来源、分阶段退出、异常所属运行、证据最早使用、授权与执行记录；可明确并行或追加语义，不得由验收者指定故事新事实。"
    ],
    "expected_outputs": [
      "U/06-causal-and-event-map.json",
      "U/07-information-ledger.csv",
      "U/09-scene-specs.md",
      "U/10-text-adaptation-map.csv",
      "U/12-traceability-and-handoff.json",
      "U/13-regression-results.md",
      "U/manifest.json"
    ],
    "forbidden_shortcuts": [
      "把receiver=项目解释为实例自动收到",
      "新增视听、键压、日志直读等能力",
      "仅补“已输入”一句而无责任/权限/时序"
    ]
  },
  "affected_consumers": [
    "UPG-S-AWAKE",
    "UPG-S-BLOCKADE",
    "UPG-S-FAREWELL",
    "REG-09/10/11的接口审查"
  ],
  "retest": [
    "REG-09",
    "REG-10",
    "REG-11",
    "NEG-CHANNEL",
    "文字转述正例",
    "独立消费六重点",
    "全局硬约束"
  ],
  "owner_decision_required": false,
  "loop_index": 2,
  "remaining_revision_budget": 1
}
```


## ACC-003

```json
{
  "finding_id": "ACC-003",
  "definition_commit": "4ce28e8a903adce69579fe08b51bf2b6ff3d842d",
  "implementation_commit": "c30de6bb2f76342867b5c3e21c347e1162368265",
  "manifest_sha256": "31dfbbd8b919f5851700cedbc64204c8344e793d9fb5ac5247483861091ce924",
  "severity": "high",
  "issue_refs": [
    10,
    12,
    13
  ],
  "failed_checks": [
    "6.1-2",
    "6.1-6",
    "REG-10",
    "REG-12",
    "REG-13",
    "6.1-7"
  ],
  "expected": "定义书 §3.3、§6.2 REG-12/13：主观片段、假设、外部取证、核验结果分列；每次识别与披露有合法接收链；记录按形成、保存、接收、披露分别登记。",
  "observed": "04:88,91与07:27规定L2具体责任归属只在授权链和沈逾知晓，R-07默认不可知、推理最高hypothesis；07:22却把REC-1的sender定为R-07生前生成，并标externally_supported；10:23要求REC-1含L2归属描述，10:25让沈逾从该记录接收L2。全表无把L2合法转入R-07的对象，也没有将L2标为现实核验者在独立附件中的批注。即使D02-A获批，该来源矛盾仍存在。",
  "root_owner": "第二步：07记录对象的来源/认知状态设计与10身份适配动作未保持同一知识模型。",
  "correction": {
    "inputs": [
      "E02 /world/environments/8、/world/environments/10",
      "定义书 §3.3/§6.2 REG-12、REG-13",
      "U/04 R15、05 E2/E4、07 IO-21/24.3、08 REC-1、10 M-22/M-24",
      "U/11 D02"
    ],
    "actions": [
      "区分R-07生成的主观线索记录和现实人员形成的核验记录，为每个内容对象列作者、材料、认知状态和权限。",
      "统一L2的生成、接收和展示路径；在保持实例默认不可知的设计下，不允许其原创记录输出L2。若改角色知情或披露方案，提交D02提案并等待批准。",
      "校对沈逾E-07.3既已接收L2与E-13.2记录阅读的知识增量，不能把重复阅读写成首次获知。",
      "逐项验证externally_supported对应的现实材料和责任人，不用“可复核”替代已核验。"
    ],
    "expected_outputs": [
      "U/04-character-responsibility.md",
      "U/06-causal-and-event-map.json",
      "U/07-information-ledger.csv",
      "U/08-ending-and-pov.md",
      "U/09-scene-specs.md",
      "U/10-text-adaptation-map.csv",
      "U/11-owner-decisions.md（如需更改D02方案）",
      "U/12-traceability-and-handoff.json",
      "U/13-regression-results.md",
      "U/manifest.json"
    ],
    "forbidden_shortcuts": [
      "给实例偷偷增加外部档案或已核验结论读取权",
      "把externally_supported改名后保留同一无来源知识",
      "替Owner指定责任人/新证据事实"
    ]
  },
  "affected_consumers": [
    "UPG-S-VERIFY",
    "UPG-S-FAREWELL",
    "UPG-S-AFTERMATH",
    "REC-1",
    "M-22/M-24"
  ],
  "retest": [
    "REG-10",
    "REG-12",
    "REG-13",
    "NEG-MEMORY",
    "NEG-IDENTITY",
    "记录生成者无L2输入的反例",
    "现实核验批注与主观记录分离正例",
    "全局硬约束"
  ],
  "owner_decision_required": false,
  "loop_index": 2,
  "remaining_revision_budget": 1
}
```


## ACC-004

```json
{
  "finding_id": "ACC-004",
  "definition_commit": "4ce28e8a903adce69579fe08b51bf2b6ff3d842d",
  "implementation_commit": "c30de6bb2f76342867b5c3e21c347e1162368265",
  "manifest_sha256": "31dfbbd8b919f5851700cedbc64204c8344e793d9fb5ac5247483861091ce924",
  "severity": "medium",
  "issue_refs": [
    10
  ],
  "failed_checks": [
    "6.1-2",
    "REG-10",
    "6.1-7"
  ],
  "expected": "定义书 §3.3、§6.2 REG-10：区分决定形成、各方获知、执行及记录披露，呈现时序应有唯一可执行解释。",
  "observed": "08:12与07:18在S2/E-11.1公开“终止请求”，09:102使最后输出逐字可见；08:19却规定读者对“决定性意图”的确认只能在S6/REC-2（E-13.2），08:26及10:10继续把读者确认点推迟至S6。包未把S2请求表达的意图与S6确认的对象分开，消费者无法同时执行这两个规则。这里不把告别中的请求本身判为批准约束所禁的“告别前早泄”；失败点是同一包自定知识时序矛盾。",
  "root_owner": "第二步：08终局知识对象未细分，“请求”“决定性意图”“事后理解”被交替使用。",
  "correction": {
    "inputs": [
      "E02 /decision_controls/4、/storylines/connections/1",
      "定义书 §3.3",
      "U/07 IO-17/22、08 A/B/E、09 FAREWELL、10 M-09",
      "U/11 D03"
    ],
    "actions": [
      "分别定义请求内容、决定性终止意图、动机/评估内容及承诺知识差，列每个对象的最早可见点与接收者。",
      "消除S2即时公开与S6首次确认同一意图的矛盾，保持告别前不展示决定性意图及S1后不复开内部POV。",
      "同步07/08/09/10/12，不能只修改其中一句。若需要新增关键承诺或释放机制，按D03-B请求Owner决定。"
    ],
    "expected_outputs": [
      "U/07-information-ledger.csv",
      "U/08-ending-and-pov.md",
      "U/09-scene-specs.md",
      "U/10-text-adaptation-map.csv",
      "U/12-traceability-and-handoff.json",
      "U/13-regression-results.md",
      "U/manifest.json"
    ],
    "forbidden_shortcuts": [
      "禁止所有文字请求来消除角色自主性",
      "用假内心或新增告警机制绕过批准",
      "把告别时表达请求一概误报为告别前早泄"
    ]
  },
  "affected_consumers": [
    "终局S0–S7",
    "IO-17/22",
    "M-09",
    "FAREWELL/AFTERMATH"
  ],
  "retest": [
    "REG-10逐对象时序",
    "NEG-ENDING",
    "执行者正确但前场早泄反例",
    "合法告别文字请求正例",
    "全局硬约束"
  ],
  "owner_decision_required": false,
  "loop_index": 2,
  "remaining_revision_budget": 1
}
```


## ACC-005

```json
{
  "finding_id": "ACC-005",
  "definition_commit": "4ce28e8a903adce69579fe08b51bf2b6ff3d842d",
  "implementation_commit": "c30de6bb2f76342867b5c3e21c347e1162368265",
  "manifest_sha256": "31dfbbd8b919f5851700cedbc64204c8344e793d9fb5ac5247483861091ce924",
  "severity": "high",
  "issue_refs": [
    12
  ],
  "failed_checks": [
    "6.1-5",
    "REG-12"
  ],
  "expected": "定义书 §2.4-2、§3.5、§6.1-5：未签认的选择不得进入无条件可消费版；可推进的是分支无关的控制，不是默认选中推荐方案。",
  "observed": "11:3-4、55明确D02 owner_pending且未签；11:82却写“07-ID组按A上限定值即可消费，B差异仅登记”，12 /blocks_and_pauses/1/nodes仅列07的B分支差异。07:25-27的A候选已固定具体责任归属、沈逾E-07.3接收、读者告别后得知等值。总禁令与可消费清单冲突；推荐A不能代替选项批准。不是把等待本身判FAIL，而是交接可能把等待绕开。",
  "root_owner": "第二步：11依赖汇总与12暂停条件错误地把A候选当成分支无关结构。",
  "correction": {
    "inputs": [
      "定义书 §3.5 D02",
      "U/11 D02提案与依赖汇总",
      "U/07 IO-24.1/24.2/24.3",
      "U/12 /blocks_and_pauses/1"
    ],
    "actions": [
      "列明D02-A、D02-B各自的条件节点及字段；推荐A仍保持未生效。",
      "把两分支共同的核验门槛和分级结构，与所选责任事实/接收者/披露时点分开。",
      "统一11、12与04/06/07/09/10的消费许可；未经签认不得生成确定归属或删角。",
      "取得选项的Owner原始决定及签认引用后，才解锁对应字段并复验；未取得时保留BLOCKED_OWNER交付。"
    ],
    "expected_outputs": [
      "U/11-owner-decisions.md",
      "U/12-traceability-and-handoff.json",
      "U/04-character-responsibility.md",
      "U/06-causal-and-event-map.json",
      "U/07-information-ledger.csv",
      "U/09-scene-specs.md",
      "U/10-text-adaptation-map.csv",
      "U/13-regression-results.md",
      "U/manifest.json"
    ],
    "forbidden_shortcuts": [
      "把推荐、候选、无新增事实等措辞当成Owner签认",
      "由验收者选中A或B",
      "只改状态标签却保留无条件消费许可"
    ]
  },
  "affected_consumers": [
    "D02所有依赖字段",
    "UPG-S-VERIFY",
    "UPG-S-AFTERMATH",
    "07身份组",
    "12下游入口"
  ],
  "retest": [
    "REG-12",
    "NEG-IDENTITY",
    "NEG-PACKAGE-OWNER",
    "签认缺失时停止具体字段消费的正例",
    "全局硬约束"
  ],
  "owner_decision_required": true,
  "owner_decision_proposal": "U/11-owner-decisions.md:41–55 D02；门禁一致性修正可先做，选项生效仍待Owner原始决定与签认。",
  "loop_index": 2,
  "remaining_revision_budget": 1
}
```


## ACC-006

```json
{
  "finding_id": "ACC-006",
  "definition_commit": "4ce28e8a903adce69579fe08b51bf2b6ff3d842d",
  "implementation_commit": "c30de6bb2f76342867b5c3e21c347e1162368265",
  "manifest_sha256": "31dfbbd8b919f5851700cedbc64204c8344e793d9fb5ac5247483861091ce924",
  "severity": "medium",
  "issue_refs": [
    3,
    6,
    10
  ],
  "failed_checks": [
    "6.1-3",
    "6.1-4",
    "6.1-6",
    "REG-06",
    "REG-10"
  ],
  "expected": "定义书 §1.4、§1.7、§1.11、§6.2：旁挂映射可以满足#3；#6工程留存与#7分开；六月正文提前展开记录和七月PRD读者先知须分别保留真实证据。",
  "observed": "08:74将六月方案描述成“读者事后与其一起读/读者后知”，但E11:347已直示选择终止，351–387先展开记录，沈逾448–460才回来读。02:22、10:11将E07:40视为private_motive提前visible，实际该行Story anchor=S15、Narrative reveal=S17，真正早知证据是E07:26，不能把anchor当reveal。13:30把#3旁挂映射已满足的关闭条件再标DEFERRED_ENGINEERING，13:33,112,115把#6与#7同源并在工程清单错纳#3、漏#6，偏离定义/本次契约。",
  "root_owner": "第二步：02/08/10的历史比较与13回归摘要。把素材要求当正文已实现，把故事锚点当披露点，把原关闭留存类别混合。",
  "correction": {
    "inputs": [
      "定义书 §1.4/§1.7/§1.11/§6.2",
      "E07:26–28,39–40",
      "E10:123",
      "E11:331–387,448–476",
      "U/02、08、10、13"
    ],
    "actions": [
      "将六月正文“读者先见记录、沈逾后读”与E10素材“应同步阅读”分栏，明确未落实而非已有优点。",
      "按E07列名区分story_anchor与narrative_reveal，保留S15主行的真实早知反例，不给40行伪造同一错因。",
      "重算13双状态：#3按22项实际证据与定义的旁挂路线判定；#6原关闭保留DEFERRED_ENGINEERING，其责任为历史记录核实，不能断言依赖#7同一机器run。",
      "同步未决清单与消费禁令，旧原件保持不变。"
    ],
    "expected_outputs": [
      "U/02-legacy-disposition.md",
      "U/08-ending-and-pov.md",
      "U/10-text-adaptation-map.csv",
      "U/13-regression-results.md",
      "U/manifest.json"
    ],
    "forbidden_shortcuts": [
      "修改旧正文或历史报告使描述看似成立",
      "以#3未获原文件编辑权否定定义允许的旁挂路线",
      "以构思ready或新包标签证明旧HLD评审对象已核实"
    ]
  },
  "affected_consumers": [
    "历史终局两方案比较",
    "M-09/M-10/M-15",
    "REG-03/06/10",
    "工程与写作交接"
  ],
  "retest": [
    "REG-03完整22行",
    "REG-06三栏核对",
    "REG-10两版旧终局",
    "NEG-STATE",
    "全局硬约束"
  ],
  "owner_decision_required": false,
  "loop_index": 2,
  "remaining_revision_budget": 1
}
```


## 复验输入与不能提前宣布的状态

交回固定新提交、递增版本、manifest、六条修正响应（实际变化/未变/待决）、受影响引用清单与重跑证据。复验必须包含全部13条双列回归、REG-03的22行、四个high完整链路、REG-08..13各正负例、NEG七类及独立密封消费；不能只修关键词或只重算hash。

D01–D03的有效签认未取得前保留BLOCKED_OWNER；#7无受控本体及正式复验保留BLOCKED_EVIDENCE；#1/#2/#4/#6原关闭保留DEFERRED_ENGINEERING；实际写作未授权、未落地的关闭条件保留PENDING_WRITING。不得改旧批准、把候选当正式HLD/LLD、关闭或评论GitHub ISSUE。Owner manual-review 为 OWNER_PENDING，不计入本验收者FAIL；本次FAIL有独立的六条实现证据。
