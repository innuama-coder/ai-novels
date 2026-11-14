# v1.2 最终复验发现

design_verdict=FAIL。三项已证实的实现问题；待批和缺证状态不充当失败理由。

定义提交：4ce28e8a903adce69579fe08b51bf2b6ff3d842d；定义文件SHA-256：f2474997981699f5ad0cae9f6ee5b924238b2619536171e6830dcb7364844a52。

候选：v1.2，implementation_commit=311b29af7fec928ea987c5e469d2389442cd6348；manifest_sha256=56c60ae773c66aa15bdfdeaaaa7a7bc5777919b8b0a793e8353f50addeba7a53。BASE=92573f1cca40f37cee04d2beb8708ff33ba603d6。U/ 表示 duanxian/design/upgrades/duanxian-upg-impl-001/；A2/ 表示本目录。E01–E17的完整路径/定位见 evidence-index.json 的 sources（沿用定义书证据编号）。JSON Pointer数组索引从0开始，CSV行号含表头，U/定位绑定上述候选。

loop_index=3；remaining_revision_budget=0；manual-review=OWNER_PENDING。

## ACC2-001

12 /control_trace/entries/71把CONN-1的告别前悬念控制解释为IO-11私人转述通道；/entries/50把LIFE的实验价值及伦理控制推成意图确认唯一时点S6。04:117声称八条聚合图边覆盖23条REL并证明每人最短层级；实算只有18条REL，少5条。

```json
{
  "finding_id": "ACC2-001",
  "prior_finding": "ACC-001",
  "severity": "high",
  "issue_refs": [
    5
  ],
  "failed_checks": [
    "6.1-1",
    "6.1-2",
    "6.1-6",
    "REG-05"
  ],
  "expected": "定义书§2.2、§3.2、§5步骤4/8、§6.1-6：逐字段从批准源回读推导，人物层级按关系最短距离，不能只证明ID集合相同。",
  "observed": "12 /control_trace/entries/71把CONN-1的告别前悬念控制解释为IO-11私人转述通道；/entries/50把LIFE的实验价值及伦理控制推成意图确认唯一时点S6。04:117声称八条聚合图边覆盖23条REL并证明每人最短层级；实算只有18条REL，少5条。",
  "root_owner": "第二步控制追踪与人物关系覆盖；把相关文档出现当作语义推导，把聚合图距离当作完整人物关系距离。",
  "evidence": [
    "E02 /storylines/connections/1 ↔ U/12 /control_trace/entries/71 (约1140行)",
    "E02 /world/event_conditions/0 ↔ U/12 /control_trace/entries/50 (约848行)",
    "E02 /characters/relationship_networks/0/source_ids、/visual_models/4/edges ↔ U/04:117–126；evidence-index.audit.graph"
  ],
  "retest": [
    "全75控制源Pointer/hash及目标语义",
    "23条关系覆盖与最短距离依据",
    "REG-05",
    "四个high全链",
    "NEG-AUTHORITY/STATE/PACKAGE",
    "独立消费",
    "全部全局硬约束"
  ],
  "definition_commit": "4ce28e8a903adce69579fe08b51bf2b6ff3d842d",
  "implementation_commit": "311b29af7fec928ea987c5e469d2389442cd6348",
  "manifest_sha256": "56c60ae773c66aa15bdfdeaaaa7a7bc5777919b8b0a793e8353f50addeba7a53",
  "owner_decision_required": false,
  "loop_index": 3,
  "remaining_revision_budget": 0,
  "execution_status": "NOT_AUTHORIZED_PENDING_OWNER",
  "correction": {
    "inputs": [
      "定义书§2.2、§3.2、§5步骤4/8、§6.1-6：逐字段从批准源回读推导，人物层级按关系最短距离，不能只证明ID集合相同。",
      "E02 /storylines/connections/1 ↔ U/12 /control_trace/entries/71 (约1140行)",
      "E02 /world/event_conditions/0 ↔ U/12 /control_trace/entries/50 (约848行)",
      "E02 /characters/relationship_networks/0/source_ids、/visual_models/4/edges ↔ U/04:117–126；evidence-index.audit.graph"
    ],
    "actions": [
      "逐条纠正CONN-1与LIFE的目标字段、场景义务及推导理由；CONN-1应回读真实悬念/视角义务，LIFE须覆盖实验过程与伦理责任，不能以S6替代全部控制。",
      "重新核对全部高风险及新增人物控制；核清FRAGMENTS-EVIDENCE是创作片段覆盖而非记忆能力。",
      "对23条REL建立可核验承接；以实际人物关系及明确算法计算层级，若材料不足则明确证据依赖，不能声称聚合图已证明逐人距离。",
      "同步04/06/09/12/13与manifest，保留旧批准、本体缺失和正式准入边界。"
    ],
    "expected_outputs": [
      "U/01-control-register.json",
      "U/04-character-responsibility.md",
      "U/06-causal-and-event-map.json",
      "U/09-scene-specs.md",
      "U/12-traceability-and-handoff.json",
      "U/13-regression-results.md",
      "U/manifest.json"
    ],
    "forbidden_shortcuts": [
      "只补控制计数或同名ID",
      "把18条源边写成覆盖23条",
      "虚构缺失canonical或改批准源"
    ]
  },
  "affected_consumers": [
    "全部人物控制",
    "终局视角控制",
    "12 handoff",
    "REG-05"
  ]
}
```

## ACC2-002

07:11 IO-09明确当前实例运行期E-02.2异常并留痕；06 /events/2在E-03才启动R-07，09:31 AWAKE前态是实例未启动。06 /events/3/cost与/events/5/preconditions又把审查源偏离放在E-04。同一当前实例既未启动又已生成运行异常。

```json
{
  "finding_id": "ACC2-002",
  "prior_finding": "ACC-002",
  "severity": "high",
  "issue_refs": [
    9,
    10
  ],
  "failed_checks": [
    "6.1-2",
    "6.1-7",
    "REG-09",
    "REG-10"
  ],
  "expected": "定义书§3.3/§3.4、REG-09/10及ACC-002修正actions第5项：材料所属运行、形成、接收与使用须有同一可执行时序。",
  "observed": "07:11 IO-09明确当前实例运行期E-02.2异常并留痕；06 /events/2在E-03才启动R-07，09:31 AWAKE前态是实例未启动。06 /events/3/cost与/events/5/preconditions又把审查源偏离放在E-04。同一当前实例既未启动又已生成运行异常。",
  "root_owner": "第二步06事件与07日志来源/时间、09场景前态同步不完整。",
  "evidence": [
    "U/07 IO-09 source/sent_at/received_at (行11)",
    "U/06 /events/2、/events/3/cost、/events/5/preconditions",
    "U/09 UPG-S-AWAKE 前状态 (行31)",
    "独立消费对照C1"
  ],
  "retest": [
    "实例启动≤该实例日志形成≤调取≤使用",
    "合法首输入/危机转达正例",
    "NEG-CHANNEL/LATE-RECEPTION/SENT-NO-RECEIVE/NO-RELAY",
    "独立密封消费",
    "全部全局硬约束"
  ],
  "definition_commit": "4ce28e8a903adce69579fe08b51bf2b6ff3d842d",
  "implementation_commit": "311b29af7fec928ea987c5e469d2389442cd6348",
  "manifest_sha256": "56c60ae773c66aa15bdfdeaaaa7a7bc5777919b8b0a793e8353f50addeba7a53",
  "owner_decision_required": false,
  "loop_index": 3,
  "remaining_revision_budget": 0,
  "execution_status": "NOT_AUTHORIZED_PENDING_OWNER",
  "correction": {
    "inputs": [
      "定义书§3.3/§3.4、REG-09/10及ACC-002修正actions第5项：材料所属运行、形成、接收与使用须有同一可执行时序。",
      "U/07 IO-09 source/sent_at/received_at (行11)",
      "U/06 /events/2、/events/3/cost、/events/5/preconditions",
      "U/09 UPG-S-AWAKE 前状态 (行31)",
      "独立消费对照C1"
    ],
    "actions": [
      "明确IO-09实际材料来源和所属运行，并将发生/记录/调取/使用时点与E-03启动及E-04行为偏离对齐。",
      "若确需启动前材料，区分其与当前实例运行日志，给出受控来源；不由消费方猜作旧实例或设备日志。",
      "从初醒到审查再到E-10逐边回放；同时保持IO-06.0首输入与IO-16.1危机结果转达的修复。",
      "同步06/07/09/10/12/13并实算manifest。"
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
      "仅把sent≤received≤use当作跨对象出生约束证明",
      "无依据称旧实例日志",
      "新增实例感官或日志直读能力"
    ]
  },
  "affected_consumers": [
    "AWAKE",
    "REVIEW",
    "E-10评估",
    "07信息台账",
    "REG-09/10/11"
  ]
}
```

## ACC2-003

06 /events/10/preconditions/1要求进入E-11前关停授权已完成；同事件/actions/1在E-11.2才授权，07/08把请求放E-11.1。/actions/2执行记录写IO-19 received E-11.3，而07:22 IO-19明确只是E-11.2授权且不含执行事实，07:23 IO-19.1才为执行。

```json
{
  "finding_id": "ACC2-003",
  "prior_finding": "ACC-002",
  "severity": "medium",
  "issue_refs": [
    10
  ],
  "failed_checks": [
    "6.1-2",
    "6.1-7",
    "REG-10"
  ],
  "expected": "定义书§3.3、REG-10及ACC-002授权/执行记录要求：请求→授权→执行分离且事件入口、子动作和信息对象一致。",
  "observed": "06 /events/10/preconditions/1要求进入E-11前关停授权已完成；同事件/actions/1在E-11.2才授权，07/08把请求放E-11.1。/actions/2执行记录写IO-19 received E-11.3，而07:22 IO-19明确只是E-11.2授权且不含执行事实，07:23 IO-19.1才为执行。",
  "root_owner": "第二步把执行子动作条件写成整个告别事件前提，拆分台账后未同步事件动作引用。",
  "evidence": [
    "U/06 /events/10/preconditions/1、/actions/1、/actions/2 (约203/208行)",
    "U/07 IO-17、IO-19、IO-19.1 (行20/22/23)",
    "U/08 §A S2/S3/S4",
    "独立消费对照C2"
  ],
  "retest": [
    "完整请求→授权→执行→核验偏序",
    "全06/07执行记录引用",
    "NEG-ENDING及SELF-STOP",
    "独立消费",
    "全部全局硬约束"
  ],
  "definition_commit": "4ce28e8a903adce69579fe08b51bf2b6ff3d842d",
  "implementation_commit": "311b29af7fec928ea987c5e469d2389442cd6348",
  "manifest_sha256": "56c60ae773c66aa15bdfdeaaaa7a7bc5777919b8b0a793e8353f50addeba7a53",
  "owner_decision_required": false,
  "loop_index": 3,
  "remaining_revision_budget": 0,
  "execution_status": "NOT_AUTHORIZED_PENDING_OWNER",
  "correction": {
    "inputs": [
      "定义书§3.3、REG-10及ACC-002授权/执行记录要求：请求→授权→执行分离且事件入口、子动作和信息对象一致。",
      "U/06 /events/10/preconditions/1、/actions/1、/actions/2 (约203/208行)",
      "U/07 IO-17、IO-19、IO-19.1 (行20/22/23)",
      "U/08 §A S2/S3/S4",
      "独立消费对照C2"
    ],
    "actions": [
      "分别定义E-11事件入口与执行子动作前提，使E-11.1请求先于E-11.2授权再至E-11.3执行。",
      "把执行留痕引用指向真实IO-19.1并核对sender/receiver/时间；授权记录保持IO-19。",
      "同步07/08/09/10/12/13，检验可从事件入口完整走到技术核验而不循环。"
    ],
    "expected_outputs": [
      "U/06-causal-and-event-map.json",
      "U/07-information-ledger.csv",
      "U/08-ending-and-pov.md",
      "U/09-scene-specs.md",
      "U/10-text-adaptation-map.csv",
      "U/12-traceability-and-handoff.json",
      "U/13-regression-results.md",
      "U/manifest.json"
    ],
    "forbidden_shortcuts": [
      "消费方静默改前提或ID",
      "编造未批准的预授权/正式授权双机制",
      "合并意愿、授权、执行"
    ]
  },
  "affected_consumers": [
    "FAREWELL",
    "终局S2–S5",
    "IO-19/19.1",
    "REG-10"
  ]
}
```

## 非决定性观察与证据边界

O1：11:50/53暂停IO24.1/24.2/24.3的候选接收/披露字段，11:82及12摘要称L0/L1“结构”可消费。结构与具体字段可以区分解释；尚不足证明新的无条件L2捷径。保守按正文暂停全部候选具体字段，Owner签认前不定稿。

O2：06 E07 evidence列IO13，后者E08.1才到达；E08又允许E07进行中。引用可能是后续关联而非已消费输入，不能仅凭编号认定事实先用后到。需明确事件重叠及evidence用途，不在本报告发明新传递。

O3：IO03把沈逾接收与可选择告知实例并列；实际采用前需明确选择已发生。当前E10必要输入不依赖IO03，未证明实例已越权使用。

O4：08 KO-1请求与KO-2意图已明列，不再按“没有分列”判FAIL。具体对白不得一边说“我已最终决定”一边宣称只呈请求；L2沈逾早知/读者迟知也需未来文本验证公平性，均属PENDING_WRITING，不能预判实现必然失败。

O5：11:61的D03问题摘要仍沿用“读者后知”概括六月方案，落后于08§H的准确对照。作为非决定性摘要残留记录；ACC-006指定的02/08/10/13/manifest本轮修复已成立，不据此抹掉通过项。
