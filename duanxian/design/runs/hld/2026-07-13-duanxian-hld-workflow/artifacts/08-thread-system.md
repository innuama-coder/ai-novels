## Artifact Metadata

| Field | Value |
|---|---|
| Artifact id | 08 |
| Owner skill | novel-thread-system-designer |
| Run id | 2026-07-13-duanxian-hld-workflow |
| Upstream package | final PRD package and canonical world facts v3.0 |
| Input artifacts | artifacts 01-07 |
| Output path | artifacts/08-thread-system.md |
| Version | v3.0 |

## Thread system table

| Thread id | Thread type | Thread function | Thread anchor refs | Required pressure refs | Core question | Node distribution | Thread progression | Crossover | Closure state | Closure outcome | Supports | Source | LLD handoff | Amendment request |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| HLD-08-01 | main | 维持外部危机的可执行倒计时。 | HLD-06-01,HLD-06-03,HLD-06-05,HLD-06-06 | HLD-07-04,HLD-04-06,HLD-04-09 | 能否阻止一场被伪旗推向战争的升级？ | D0,D+26,D+57,D+58 | 交接失败→专家劫持→领导层犹豫与联盟报复→救援纠偏→攻击失效。 | 与隐藏线共享顾衡情报，与制度线共享行动层报告。 | closed | 会面机会被保住，金融、科技与军事升级未越过阈值。 | HLD-02-05 | scene:PRD-S00,scene:PRD-S11,scene:PRD-S12,claim:CLAIM-06 | LLD-THREAD-01 | none |
| HLD-08-02 | hidden | 将技术异常转化为私人保护原因。 | HLD-06-02,HLD-07-01 | HLD-07-03,HLD-07-05 | 顾衡为何封闭记忆？ | D0,D+27,D+57,D+90 | 自闭失败→维护例外碎片→原因层有限理解→保持未公开。 | 与情感线共同触及顾衡，与主题线共同留下沉默。 | closed | 沈逾理解原因，却不替任何人判决。 | HLD-02-05 | scene:PRD-S03,scene:PRD-S09,scene:PRD-S10,claim:CLAIM-05 | LLD-THREAD-02 | none |
| HLD-08-03 | emotional | 区分怀念顾衡与对待R-07。 | HLD-04-01,HLD-04-03 | HLD-07-02,HLD-06-04 | 沈逾想留下的是谁？ | D+27,D+56,D+59,D+90 | 旧情触发→投射被识别→请求保存→终止后承认失去。 | 与身份线共享R-07独立选择。 | closed | 沈逾不再以顾衡替代R-07。 | HLD-02-03 | scene:PRD-S07,scene:PRD-S08,scene:PRD-S14,scene:PRD-S17,claim:CLAIM-04,claim:CLAIM-09 | LLD-THREAD-03 | none |
| HLD-08-04 | institutional | 让机构审查与利益集团的资产化冲动并存。 | HLD-04-05,HLD-04-09,HLD-03-04 | HLD-07-05,HLD-06-04,HLD-06-06 | 谁会把R-07和危机真相变成可获利资产？ | D0,D+26,D+57,D+59,D+90 | 紧急授权→联盟滥用遗留授权→行动层有效→原因层审查→保存价值被终止。 | 与主题线共同逼迫沈逾隐瞒。 | closed | 组织留下档案缺口，纬线利益链失去升级机会，均不能夺走终局。 | HLD-02-03 | scene:PRD-S04,scene:PRD-S13,scene:PRD-S15,claim:CLAIM-07,claim:CLAIM-08 | LLD-THREAD-04 | none |
| HLD-08-05 | identity | 将R-07从承载实例推进为主体。 | HLD-04-03,HLD-07-02 | HLD-06-04,HLD-07-06 | R-07是容器还是主体？ | D+27,D+57,D+59,D+90 | 受限醒来→自主判断→选择告警排序→日志被读回。 | 与情感线共享沈逾的误认与承认。 | closed | 它以不越权的离开证明独立。 | HLD-02-07 | scene:PRD-S06,scene:PRD-S15,scene:PRD-S17,claim:CLAIM-03,claim:CLAIM-08,claim:CLAIM-09 | LLD-THREAD-05 | none |
| HLD-08-06 | theme | 衡量保护与沉默的代价。 | HLD-04-02,HLD-04-04 | HLD-07-05,HLD-07-06 | 保护一个人是否必须制造新的沉默？ | D0,D+57,D+59,D+90 | 顾衡封闭→沈逾删节→R-07终止→余波承担。 | 汇合隐藏、制度和情感线。 | closed | 行动结果被保存，私人真相与责任未被消除。 | HLD-02-07 | scene:PRD-S10,scene:PRD-S13,scene:PRD-S18,claim:CLAIM-05,claim:CLAIM-09 | LLD-THREAD-06 | none |

## HLD Fact Trace

| Fact trace id | Upstream fact id | Upstream fact atom | HLD fact atom | Source refs | Expansion mode | Support mechanism | Preservation status |
|---|---|---|---|---|---|---|---|
| HLD-08-01 | UPF-PRD-S11-01 | 打开记忆并化解重大事件。 | Thread type main；Thread function 维持危机倒计时；Thread anchor refs HLD-06-01,HLD-06-03；Required pressure refs HLD-07-04,HLD-04-06；Core question 阻止双重伪旗；Node distribution D0,D+26,D+57,D+58；Thread progression 失败到攻击失效；Crossover 隐藏与制度线；Closure state closed；Closure outcome 会面机会保住；Supports HLD-02-05；LLD handoff LLD-THREAD-01；Amendment request none。 | scene:PRD-S00,scene:PRD-S11,scene:PRD-S12,claim:CLAIM-06 | sequence | 主线。 | bounded_expansion |
| HLD-08-02 | UPF-PRD-S10-01 | 被保护者不是简单凶手。 | Thread type hidden；Thread function 解释保护；Thread anchor refs HLD-06-02,HLD-07-01；Required pressure refs HLD-07-03,HLD-07-05；Core question 顾衡为何封闭；Node distribution D0,D+27,D+57,D+90；Thread progression 自闭到不公开；Crossover 情感主题线；Closure state closed；Closure outcome 沈逾理解不判决；Supports HLD-02-05；LLD handoff LLD-THREAD-02；Amendment request none。 | scene:PRD-S03,scene:PRD-S09,scene:PRD-S10,claim:CLAIM-05 | sequence | 隐藏线。 | bounded_expansion |
| HLD-08-03 | UPF-PRD-S07-01 | 研究员、数字生命体与旧校友资料。 | Thread type emotional；Thread function 区分怀念与主体；Thread anchor refs HLD-04-01,HLD-04-03；Required pressure refs HLD-07-02,HLD-06-04；Core question 沈逾想留下谁；Node distribution D+27,D+56,D+59,D+90；Thread progression 投射到承认；Crossover 身份线；Closure state closed；Closure outcome 不再替代；Supports HLD-02-03；LLD handoff LLD-THREAD-03；Amendment request none。 | scene:PRD-S07,scene:PRD-S08,scene:PRD-S14,scene:PRD-S17,claim:CLAIM-04,claim:CLAIM-09 | support | 情感线。 | bounded_expansion |
| HLD-08-04 | UPF-PRD-S13-01 | 危机化解后组织进入结案审查。 | Thread type institutional；Thread function 资产化压力；Thread anchor refs HLD-04-05,HLD-03-04；Required pressure refs HLD-07-05,HLD-06-04；Core question 组织会把R-07当什么；Node distribution D0,D+57,D+59,D+90；Thread progression 授权到终止；Crossover 主题线；Closure state closed；Closure outcome 档案缺口；Supports HLD-02-03；LLD handoff LLD-THREAD-04；Amendment request none。 | scene:PRD-S04,scene:PRD-S13,scene:PRD-S15,claim:CLAIM-07,claim:CLAIM-08 | support | 制度线。 | bounded_expansion |
| HLD-08-05 | UPF-PRD-S15-01 | 数字生命体决定设计自己的终止。 | Thread type identity；Thread function 主体判断；Thread anchor refs HLD-04-03,HLD-07-02；Required pressure refs HLD-06-04,HLD-07-06；Core question 容器还是主体；Node distribution D+27,D+57,D+59,D+90；Thread progression 醒来到日志读回；Crossover 情感线；Closure state closed；Closure outcome 不越权离开；Supports HLD-02-07；LLD handoff LLD-THREAD-05；Amendment request none。 | scene:PRD-S06,scene:PRD-S15,scene:PRD-S17,claim:CLAIM-03,claim:CLAIM-08,claim:CLAIM-09 | constrain | 身份线。 | preserved |
| HLD-08-06 | UPF-PRD-S18-01 | 研究员长期承担后果。 | Thread type theme；Thread function 保护与沉默；Thread anchor refs HLD-04-02,HLD-04-04；Required pressure refs HLD-07-05,HLD-07-06；Core question 保护是否制造沉默；Node distribution D0,D+57,D+59,D+90；Thread progression 封闭删节终止余波；Crossover 隐藏制度情感；Closure state closed；Closure outcome 结果保存责任未消；Supports HLD-02-07；LLD handoff LLD-THREAD-06；Amendment request none。 | scene:PRD-S10,scene:PRD-S13,scene:PRD-S18,claim:CLAIM-05,claim:CLAIM-09 | handoff | 主题线。 | preserved |

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
