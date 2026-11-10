## Artifact Metadata

| Field | Value |
|---|---|
| Artifact id | 09 |
| Owner skill | novel-style-pov-system-designer |
| Run id | 2026-07-13-duanxian-hld-workflow |
| Upstream package | final PRD package and canonical world facts v3.0 |
| Input artifacts | artifacts 01-08 |
| Output path | artifacts/09-style-pov-system.md |
| Version | v3.0 |

## Style and POV table

| Style/POV id | Rule type | Access policy | Information refs | Thread refs | Reader disclosure mode | Language profile | Design fact | POV permission | Prohibited expression | Supports | Source | LLD handoff | Amendment request |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| HLD-09-01 | pov | evidence_bound | HLD-07-01,HLD-07-04,HLD-07-05 | HLD-08-01,HLD-08-02 | staged_focalized | 冷静、精确、只写可观察动作。 | scope=HLD-07-04; target=HLD-08-01; evidence=HLD-07-01; trigger=staged_focalized; focalizer=沈逾; effect=行动层先于原因层抵达读者。 | 允许贴近沈逾的判断和误判。 | 禁止全知解释周岚或顾衡的内心。 | HLD-02-07 | scene:PRD-S07,scene:PRD-S11,scene:PRD-S13,claim:CLAIM-04,claim:CLAIM-06 | LLD-STYLE-01 | none |
| HLD-09-02 | information_access | evidence_bound | HLD-07-02,HLD-07-06 | HLD-08-03,HLD-08-05 | staged_log_reveal | 日志、时间戳、删节字段优先。 | scope=HLD-07-06; target=HLD-08-05; evidence=HLD-07-02; trigger=staged_log_reveal; focalizer=沈逾; effect=R-07主体性由可验证差异显现。 | 允许解释可验证的日志差异。 | 禁止以顾衡记忆替代R-07选择。 | HLD-02-07 | scene:PRD-S08,scene:PRD-S15,scene:PRD-S17,claim:CLAIM-08,claim:CLAIM-09 | LLD-STYLE-02 | none |
| HLD-09-03 | dialogue | constrained_dialogue | HLD-07-02,HLD-07-03 | HLD-08-03,HLD-08-06 | subtext_before_explanation | 短问短答，停顿承担压力。 | scope=HLD-07-03; target=HLD-08-03; evidence=HLD-07-02; trigger=subtext_before_explanation; focalizer=沈逾; effect=旧情不命名而关系压力可感。 | 允许沈逾报告听到和未回答的句子。 | 禁止R-07用顾衡口吻告白。 | HLD-02-07 | scene:PRD-S07,scene:PRD-S08,scene:PRD-S10,claim:CLAIM-04,claim:CLAIM-05 | LLD-STYLE-03 | none |
| HLD-09-04 | image_system | material_detail | HLD-07-01,HLD-07-04 | HLD-08-01,HLD-08-04 | sensory_anchor | 医疗屏幕、确认框、双语核验音形成重复意象。 | scope=HLD-07-04; target=HLD-08-04; evidence=HLD-07-01; trigger=sensory_anchor; focalizer=沈逾; effect=制度压力落在可听见可触及的界面。 | 允许以物理细节映照权限变化。 | 禁止用抽象宏大口号代替环境。 | HLD-02-07 | scene:PRD-S01,scene:PRD-S12,scene:PRD-S16,claim:CLAIM-01,claim:CLAIM-06,claim:CLAIM-08 | LLD-STYLE-04 | none |
| HLD-09-05 | language_profile | formal_restraint | HLD-07-04,HLD-07-05,HLD-07-06 | HLD-08-02,HLD-08-06 | consequence_after_action | 技术语句短而可核验，情感句落在删节与未完成动作。 | scope=HLD-07-05; target=HLD-08-06; evidence=HLD-07-06; trigger=consequence_after_action; focalizer=沈逾; effect=行动结果与私人代价不互相抵消。 | 允许行动后再显现代价。 | 禁止以解释性独白替代后果。 | HLD-02-07 | scene:PRD-S10,scene:PRD-S12,scene:PRD-S18,claim:CLAIM-05,claim:CLAIM-06,claim:CLAIM-09 | LLD-STYLE-05 | none |

## HLD Fact Trace

| Fact trace id | Upstream fact id | Upstream fact atom | HLD fact atom | Source refs | Expansion mode | Support mechanism | Preservation status |
|---|---|---|---|---|---|---|---|
| HLD-09-01 | UPF-PRD-S08-01 | 研究员的诱导方式从技术审讯转向私人试探。 | Rule type pov；Access policy evidence_bound；Information refs HLD-07-01,HLD-07-04,HLD-07-05；Thread refs HLD-08-01,HLD-08-02；Reader disclosure mode staged_focalized；Language profile 冷静精确；Design fact scope=HLD-07-04 target=HLD-08-01 evidence=HLD-07-01 trigger=staged_focalized focalizer=沈逾 effect=行动层先于原因层；POV permission 贴近沈逾；Prohibited expression 全知内心；Supports HLD-02-07；LLD handoff LLD-STYLE-01；Amendment request none。 | scene:PRD-S07,scene:PRD-S11,scene:PRD-S13,claim:CLAIM-04,claim:CLAIM-06 | constrain | 沈逾限知。 | preserved |
| HLD-09-02 | UPF-PRD-S15-01 | 数字生命体决定设计自己的终止。 | Rule type information_access；Access policy evidence_bound；Information refs HLD-07-02,HLD-07-06；Thread refs HLD-08-03,HLD-08-05；Reader disclosure mode staged_log_reveal；Language profile 日志时间戳删节；Design fact scope=HLD-07-06 target=HLD-08-05 evidence=HLD-07-02 trigger=staged_log_reveal focalizer=沈逾 effect=主体性由日志显现；POV permission 可验证差异；Prohibited expression 顾衡替代R-07；Supports HLD-02-07；LLD handoff LLD-STYLE-02；Amendment request none。 | scene:PRD-S08,scene:PRD-S15,scene:PRD-S17,claim:CLAIM-08,claim:CLAIM-09 | constrain | 数字主体可见。 | preserved |
| HLD-09-03 | UPF-PRD-S07-02 | 她确认逝者是学生时代暗恋过的学长。 | Rule type dialogue；Access policy constrained_dialogue；Information refs HLD-07-02,HLD-07-03；Thread refs HLD-08-03,HLD-08-06；Reader disclosure mode subtext_before_explanation；Language profile 短问短答；Design fact scope=HLD-07-03 target=HLD-08-03 evidence=HLD-07-02 trigger=subtext_before_explanation focalizer=沈逾 effect=旧情不命名；POV permission 记录未回答；Prohibited expression R-07告白；Supports HLD-02-07；LLD handoff LLD-STYLE-03；Amendment request none。 | scene:PRD-S07,scene:PRD-S08,scene:PRD-S10,claim:CLAIM-04,claim:CLAIM-05 | support | 对话节制。 | bounded_expansion |
| HLD-09-04 | UPF-PRD-S01-02 | 医学死亡和情报任务在同一张床边相撞。 | Rule type image_system；Access policy material_detail；Information refs HLD-07-01,HLD-07-04；Thread refs HLD-08-01,HLD-08-04；Reader disclosure mode sensory_anchor；Language profile 屏幕确认框核验音；Design fact scope=HLD-07-04 target=HLD-08-04 evidence=HLD-07-01 trigger=sensory_anchor focalizer=沈逾 effect=制度压力落在界面；POV permission 物理细节；Prohibited expression 宏大口号；Supports HLD-02-07；LLD handoff LLD-STYLE-04；Amendment request none。 | scene:PRD-S01,scene:PRD-S12,scene:PRD-S16,claim:CLAIM-01,claim:CLAIM-06,claim:CLAIM-08 | explain | 意象系统。 | bounded_expansion |
| HLD-09-05 | UPF-PRD-S18-01 | 研究员长期承担后果。 | Rule type language_profile；Access policy formal_restraint；Information refs HLD-07-04,HLD-07-05,HLD-07-06；Thread refs HLD-08-02,HLD-08-06；Reader disclosure mode consequence_after_action；Language profile 技术可核验情感落在动作；Design fact scope=HLD-07-05 target=HLD-08-06 evidence=HLD-07-06 trigger=consequence_after_action focalizer=沈逾 effect=结果与代价不抵消；POV permission 行动后代价；Prohibited expression 解释性独白；Supports HLD-02-07；LLD handoff LLD-STYLE-05；Amendment request none。 | scene:PRD-S10,scene:PRD-S12,scene:PRD-S18,claim:CLAIM-05,claim:CLAIM-06,claim:CLAIM-09 | handoff | 语言执行。 | preserved |

## Skill Verdict

| Field | Value |
|---|---|
| Skill quality verdict | pass |
| Source closure | closed |
| Inventory coverage | not_applicable |
| Boundary obedience | pass |
| Downstream readiness | ready |
| Blocking issue | none |
| Rerun target | none |
