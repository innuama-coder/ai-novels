# 《断线》v1.2 最终复验

**design_verdict=FAIL**。原六项复测中，ACC-001的来源语义/人物关系覆盖、ACC-002的跨场景时序/授权记录同步仍未闭合，形成ACC2-001..003。ACC-003..006原修正目标在限定范围内通过。FAIL不是由Owner待批、机器缺证、工程延期或正文未写自动推导。

定义提交：4ce28e8a903adce69579fe08b51bf2b6ff3d842d；定义文件SHA-256：f2474997981699f5ad0cae9f6ee5b924238b2619536171e6830dcb7364844a52。

候选：v1.2，implementation_commit=311b29af7fec928ea987c5e469d2389442cd6348；manifest_sha256=56c60ae773c66aa15bdfdeaaaa7a7bc5777919b8b0a793e8353f50addeba7a53。BASE=92573f1cca40f37cee04d2beb8708ff33ba603d6。U/ 表示 duanxian/design/upgrades/duanxian-upg-impl-001/；A2/ 表示本目录。E01–E17的完整路径/定位见 evidence-index.json 的 sources（沿用定义书证据编号）。JSON Pointer数组索引从0开始，CSV行号含表头，U/定位绑定上述候选。

loop_index=3；remaining_revision_budget=0；manual-review=OWNER_PENDING。

本报告由验收者独立读取批准源、冻结ISSUE全文、历史反例与候选形成；13号实施自检及上轮判词不是本轮证明。ISSUE快照SHA-256为1e35e5e10f75d4c7fda990ef6be71cd0020af935130c78c07c6431f774c7ea67，全部13条纳入；未另取在线ISSUE，未写外部服务。只新增A2五文件，探针在忽略目录。

## 定义书§6.1 八项

| 检查 | 结果 | 独立证据与边界 |
| --- | --- | --- |
| 6.1-1 六要素 | FAIL | 目标/方法/边界/交付/标准均按冻结约束；候选硬约束内容未满足，ACC2-001..003，不能以结构完备代替。 |
| 6.1-2 总体方案 | FAIL | README唯一入口、v1.2可辨；06/07/09的日志出生时序与E11授权记录不一致。 |
| 6.1-3 路线图 | PASS | 定义→初验→最终修订→本轮最终复验可追踪；实施配置GLM-5.3见00历史登记，本作业配置codex/gpt-6-astra见冻结spec；不声称运行时模型另经验证。FAIL交Owner，预算0。 |
| 6.1-4 工程边界 | PASS | 七runtime/三测试仅静态，BASE=82，属性风险复现，旧v3/v2与本体缺证分别保留。 |
| 6.1-5 作者边界 | PASS（门禁审查） | E03构思批准未改，D01–D03仍待签；未认定候选事实正式生效。O1保守暂停具体字段。 |
| 6.1-6 来源/字节/引用 | FAIL | 15项hash、75投影、22映射、旧1444文件不变均通过；目标语义与人物图覆盖失败，ACC2-001。 |
| 6.1-7 消费能力 | FAIL | 无继承上下文单Agent，先12及允许材料后密封，再06–10；C1/C2需消费方改设计才可执行。 |
| 6.1-8 内容质量 | PASS（内容维度） | 周岚同意与协查、沈逾职业/执行代价、现实团队公共救援及开放伦理余波有具体场景承接。此内容维度不豁免6.1-2的因果矛盾，也不证明未来正文质量。 |

## 原六项 expected_outputs 逐项复测（§6.4）

PASS只表示该原缺陷的修正目标成立；与其他发现、Owner依赖及正式准入分开。全部旧原件未反向改写。每项文件实算hash见evidence-index.retests；下列行不是以存在文件代替内容检查。

### ACC-001：FAIL

| 原修正单expected_output | 本轮核对 |
| --- | --- |
| U/01-control-register.json | PASS：75条投影，三个遗漏源对象已登记；逐源hash/Pointer/承接字段核对成立。 |
| U/06-causal-and-event-map.json | PASS：原ACT-LIFE、ACT-CRISIS、EVENTS未注册ID消失；完整控制token均能解析。仅指ID修复。 |
| U/12-traceability-and-handoff.json | FAIL：entries/71、50仍不忠实推导源；04 R18聚合关系距离证据不足，ACC2-001。 |
| U/13-regression-results.md | FAIL：新版报告仍声称追踪闭合；本轮实读发现上述反例，不能复用其PASS。 |
| U/manifest.json | PASS：15项实际字节/hash一致；只证明完整性。 |

### ACC-002：FAIL

| 原修正单expected_output | 本轮核对 |
| --- | --- |
| U/06-causal-and-event-map.json | FAIL：E03首输入、E10危机结果依赖已修；E11入口授权与动作冲突、执行记录指错。 |
| U/07-information-ledger.csv | FAIL：06.0首输入及16.1转达已补；09当前实例E02.2日志与启动冲突。19/19.1拆分本身正确。 |
| U/09-scene-specs.md | PASS（局部）：AWAKE先收06.0后输出；BLOCKADE/FAREWELL有16.1，不再留后续登记；与06/07全链仍FAIL。 |
| U/10-text-adaptation-map.csv | PASS（局部）：M05/07等初醒映射和M09/10终局适配同步台账；28项仍PENDING_WRITING。 |
| U/12-traceability-and-handoff.json | FAIL：具备更新入口和场景引用，但消费者仍需自行改06/07才能执行，见密封对照C1/C2。 |
| U/13-regression-results.md | FAIL：IO09运行期与授权记录同步问题使其全链通过声明不成立。 |
| U/manifest.json | PASS：字节绑定有效；不排除内容矛盾。 |

### ACC-003：PASS

| 原修正单expected_output | 本轮核对 |
| --- | --- |
| U/04-character-responsibility.md | PASS：R15分级和R07上限保持，未给实例L2档案权。 |
| U/06-causal-and-event-map.json | PASS：E09.6外部核验批注与E10.4实例记录分开；前者依据E08线索，不倒用尚未形成REC-1。 |
| U/07-information-ledger.csv | PASS：IO21为主观线索/假设；IO21V外部核验；IO24.3的L2接收与记录阅读分开。 |
| U/08-ending-and-pov.md | PASS：REC-1/REC-1V来源分列，封存/移交/沈逾阅读分时。 |
| U/09-scene-specs.md | PASS：VERIFY外部现实核验；AFTERMATH不把重读当初知。 |
| U/10-text-adaptation-map.csv | PASS：M22/M24取消实例原创L2与沈逾从REC-1首次获知的旧要求。 |
| U/11-owner-decisions.md | PASS（条件性）：保留D02 owner_pending；新增外部批注不替Owner批准归属。 |
| U/12-traceability-and-handoff.json | PASS（原缺陷）：REC-1V L2列入暂停依赖；未把实例记录作为核验事实。 |
| U/13-regression-results.md | PASS（原缺陷）：记录拆分修复可由上述实体支持，独立判断不援引其判词。 |
| U/manifest.json | PASS：覆盖新增对象所在文件实际hash。 |

### ACC-004：PASS

| 原修正单expected_output | 本轮核对 |
| --- | --- |
| U/07-information-ledger.csv | PASS：IO17对应KO-1请求，IO22对应KO-2/3事后记录，不再以一个含糊意图对象解释两时点。 |
| U/08-ending-and-pov.md | PASS：§A-2四对象明列；S1关闭内部POV，S2请求，S6记录确认。 |
| U/09-scene-specs.md | PASS：FAREWELL最后输出限制KO-1、禁止KO-2/3，AFTERMATH对照记录。 |
| U/10-text-adaptation-map.csv | PASS：M09等以请求/意图/动机对象区分，旧早泄内容待适配。 |
| U/12-traceability-and-handoff.json | PASS（原缺陷）：终局消费引用08知识对象及相关台账。 |
| U/13-regression-results.md | PASS（原缺陷）：对象拆分有真实字段，不以自报PASS代替阅读。 |
| U/manifest.json | PASS：终局材料hash一致。 |

### ACC-005：PASS

| 原修正单expected_output | 本轮核对 |
| --- | --- |
| U/11-owner-decisions.md | PASS（原L2捷径）：82行明确24.3/REC-1V L2未签不得无条件消费；A和B均未生效。L0/L1字段范围保守按50/53行暂停，另列观察O1。 |
| U/12-traceability-and-handoff.json | PASS（原L2捷径）：blocks_and_pauses/1包含A候选24.3及REC-1V L2，不再只停B。 |
| U/04-character-responsibility.md | PASS：R15分级不等于选中罪责，R16拒绝按职务换名。 |
| U/06-causal-and-event-map.json | PASS：E07 conditional_note保留D02；核验/分级结构与确定归属区分。 |
| U/07-information-ledger.csv | PASS：24.3 receiver/reader_reveal标为未签A候选；24.1/24.2仍decision_ref D02，不能扩为全部字段无条件可用。 |
| U/09-scene-specs.md | PASS：VERIFY conditional_on_D02；未签不能产确定归属。 |
| U/10-text-adaptation-map.csv | PASS：M13等保持Owner条件及正文PENDING_WRITING，不替换罪责。 |
| U/13-regression-results.md | PASS（原L2捷径）：候选边界可由11/12实体支持；不代表必要批准已经取得。 |
| U/manifest.json | PASS：决策与交接字节一致。 |

### ACC-006：PASS

| 原修正单expected_output | 本轮核对 |
| --- | --- |
| U/02-legacy-disposition.md | PASS：LEG04区分E07:26真正早知与:40的S15锚点/S17披露。 |
| U/08-ending-and-pov.md | PASS：§H六月读者先见记录351–387、沈逾448–460后读；E10:123素材同步规则列为未落实。 |
| U/10-text-adaptation-map.csv | PASS：M10等纠正历史证据，不把anchor当reveal；新适配尚待写作。 |
| U/13-regression-results.md | PASS：#3旁挂22项与#6历史核实分开；工程留存1/2/4/6，不再混#7。 |
| U/manifest.json | PASS：历史处置文件绑定一致；旧原件未改。 |

受影响消费者复测：12虽登记75控制，语义反例仍在；13虽更新v1.2不能证明自身PASS；07/08拆分已建立但06留有矛盾；09/10已修首输入、转达、对象和映射，不能使源事件矛盾自动消失。README明确v1.2及12入口；00历史job元数据保留不等于本轮版本回退。

## REG-01..13 双状态（§6.2）

| REG | 设计 | 原关闭 | 理由 |
| --- | --- | --- | --- |
| REG-01 | PASS | DEFERRED_ENGINEERING | 七runtime/三测试坏入口仅静态定位，验收探针未调用；未做工程修复 |
| REG-02 | PASS | DEFERRED_ENGINEERING | BASE一层novel-* SKILL=82；两份导览未改，集合与计数口径保留 |
| REG-03 | PASS | PASS | 17路径与五指称逐项核对；旁挂勘误满足本条追溯，部分/缺失未冒充规则；不表示所有旧内容可消费 |
| REG-04 | PASS | DEFERRED_ENGINEERING | 新包15文件hash精确；三样本text/eol共六项unspecified风险复现；不外推完整工程集合 |
| REG-05 | FAIL | FAIL | 旧P1/open保留，但新替代字段追踪仍有误；正式HLD人审与LLD准入也未取得 |
| REG-06 | PASS | DEFERRED_ENGINEERING | v3声明、L33 v2、真实评审对象三栏隔离；无原run核实，不靠新版本消除歧义 |
| REG-07 | PASS | BLOCKED_EVIDENCE | 承认构思批准有效且候选非正式；树中缺本体不能推断外部不存在；正式受控复验材料未取得 |
| REG-08 | PASS | BLOCKED_OWNER | 无辜/同意/公共救援结构成立；具体保护机制D01未签仍停 |
| REG-09 | FAIL | PENDING_WRITING | 首输入与文字边界已修；初醒/当前运行日志跨场景时序仍冲突；原正文未适配 |
| REG-10 | FAIL | PENDING_WRITING | 知识对象与主观/外部记录已拆分；E11授权入口/执行记录矛盾仍阻碍完整消费 |
| REG-11 | PASS | PENDING_WRITING | IO10问询到沈逾→IO11 E06.3转述到实例→E10使用；不从精确十秒/室内感官得知；全局日志来源另记ACC2-002 |
| REG-12 | BLOCKED_OWNER | BLOCKED_OWNER | 原未签L2可消费捷径已移除；D02未选，不能替作者定责/换名；后续文本仍待写 |
| REG-13 | PASS | PENDING_WRITING | 片段/假设/外部核验分列，REC-1不输出未获L2；未虚构现实核验已经发生；完整正文仍待适配 |

两列独立：REG-03旁挂可满足本条追溯，PASS不等于关闭线上ISSUE；REG-05用FAIL保留实质替代追踪缺陷，同时正式准入仍缺证。REG-09/10原关闭PENDING_WRITING不掩盖设计FAIL。REG-08的D01、REG-12的D02优先列Owner阻塞，相关真实文本也未落地。

## REG-03 全22项引用复核

第1–17项逐行对照BASE及快照；18–22从R07 L14的五个指称拆行，old_text是子项重建而非整行逐字，另核L16三阶段声明。HLD§9为312–339，§10从343起是交接，不能机械章节减一。

| 项 | 源与行 | 旧指称 | 映射目标 | 独立复核 |
| --- | --- | --- | --- | --- |
| 1 | duanxian/writing/characters/2026-06-07-writer-R07.md:L13 | docs/superpowers/specs/lld/characters/2026-06-07-character-it.md | duanxian/design/specs/lld/characters/2026-06-07-character-it.md | PASS：BASE源整行精确、目标存在、快照对应；仅路径可达，不许可旧内容。 |
| 2 | duanxian/writing/characters/2026-06-07-writer-betrayer.md:L13 | docs/superpowers/specs/lld/characters/2026-06-07-character-betrayer.md | duanxian/design/specs/lld/characters/2026-06-07-character-betrayer.md | PASS：BASE源整行精确、目标存在、快照对应；仅路径可达，不许可旧内容。 |
| 3 | duanxian/writing/characters/2026-06-07-writer-colleagues.md:L13 | docs/superpowers/specs/lld/characters/2026-06-07-character-colleagues.md | duanxian/design/specs/lld/characters/2026-06-07-character-colleagues.md | PASS：BASE源整行精确、目标存在、快照对应；仅路径可达，不许可旧内容。 |
| 4 | duanxian/writing/characters/2026-06-07-writer-jiling.md:L14 | docs/superpowers/specs/lld/characters/2026-06-07-character-jiling.md | duanxian/design/specs/lld/characters/2026-06-07-character-jiling.md | PASS：BASE源整行精确、目标存在、快照对应；仅路径可达，不许可旧内容。 |
| 5 | duanxian/writing/characters/2026-06-07-writer-qianxu.md:L13 | docs/superpowers/specs/lld/characters/2026-06-07-character-qianxu.md | duanxian/design/specs/lld/characters/2026-06-07-character-qianxu.md | PASS：BASE源整行精确、目标存在、快照对应；仅路径可达，不许可旧内容。 |
| 6 | duanxian/writing/characters/2026-06-07-writer-shenyu.md:L13 | docs/superpowers/specs/lld/characters/2026-06-07-character-shenyu.md | duanxian/design/specs/lld/characters/2026-06-07-character-shenyu.md | PASS：BASE源整行精确、目标存在、快照对应；仅路径可达，不许可旧内容。 |
| 7 | duanxian/writing/characters/2026-06-07-writer-zhengbozhou.md:L14 | docs/superpowers/specs/lld/characters/2026-06-07-character-zhengbozhou.md | duanxian/design/specs/lld/characters/2026-06-07-character-zhengbozhou.md | PASS：BASE源整行精确、目标存在、快照对应；仅路径可达，不许可旧内容。 |
| 8 | duanxian/writing/scenes/2026-06-07-scene-K1.md:L15 | docs/superpowers/specs/lld/scenes/2026-06-07-scene-K1.md | duanxian/design/specs/lld/scenes/2026-06-07-scene-K1.md | PASS：BASE源整行精确、目标存在、快照对应；仅路径可达，不许可旧内容。 |
| 9 | duanxian/writing/spaces/2026-06-07-writer-apartment.md:L15 | docs/superpowers/specs/lld/spaces/2026-06-07-space-apartment.md | duanxian/design/specs/lld/spaces/2026-06-07-space-apartment.md | PASS：BASE源整行精确、目标存在、快照对应；仅路径可达，不许可旧内容。 |
| 10 | duanxian/writing/spaces/2026-06-07-writer-city.md:L14 | docs/superpowers/specs/lld/spaces/2026-06-07-space-city.md | duanxian/design/specs/lld/spaces/2026-06-07-space-city.md | PASS：BASE源整行精确、目标存在、快照对应；仅路径可达，不许可旧内容。 |
| 11 | duanxian/writing/spaces/2026-06-07-writer-corridor.md:L14 | docs/superpowers/specs/lld/spaces/2026-06-07-space-corridor.md | duanxian/design/specs/lld/spaces/2026-06-07-space-corridor.md | PASS：BASE源整行精确、目标存在、快照对应；仅路径可达，不许可旧内容。 |
| 12 | duanxian/writing/spaces/2026-06-07-writer-digital-realm.md:L13 | docs/superpowers/specs/lld/spaces/2026-06-07-space-digital-realm.md | duanxian/design/specs/lld/spaces/2026-06-07-space-digital-realm.md | PASS：BASE源整行精确、目标存在、快照对应；仅路径可达，不许可旧内容。 |
| 13 | duanxian/writing/spaces/2026-06-07-writer-hotel-room.md:L14 | docs/superpowers/specs/lld/spaces/2026-06-07-space-hotel-room.md | duanxian/design/specs/lld/spaces/2026-06-07-space-hotel-room.md | PASS：BASE源整行精确、目标存在、快照对应；仅路径可达，不许可旧内容。 |
| 14 | duanxian/writing/spaces/2026-06-07-writer-meeting-room.md:L14 | docs/superpowers/specs/lld/spaces/2026-06-07-space-meeting-room.md | duanxian/design/specs/lld/spaces/2026-06-07-space-meeting-room.md | PASS：BASE源整行精确、目标存在、快照对应；仅路径可达，不许可旧内容。 |
| 15 | duanxian/writing/spaces/2026-06-07-writer-operation-room.md:L13 | docs/superpowers/specs/lld/spaces/2026-06-07-space-operation-room.md | duanxian/design/specs/lld/spaces/2026-06-07-space-operation-room.md | PASS：BASE源整行精确、目标存在、快照对应；仅路径可达，不许可旧内容。 |
| 16 | duanxian/writing/spaces/2026-06-07-writer-security-hall.md:L14 | docs/superpowers/specs/lld/spaces/2026-06-07-space-security-hall.md | duanxian/design/specs/lld/spaces/2026-06-07-space-security-hall.md | PASS：BASE源整行精确、目标存在、快照对应；仅路径可达，不许可旧内容。 |
| 17 | duanxian/writing/spaces/2026-06-07-writer-server-room.md:L14 | docs/superpowers/specs/lld/spaces/2026-06-07-space-server-room.md | duanxian/design/specs/lld/spaces/2026-06-07-space-server-room.md | PASS：BASE源整行精确、目标存在、快照对应；仅路径可达，不许可旧内容。 |
| 18 | duanxian/writing/characters/2026-06-07-writer-R07.md:L14 | docs/superpowers/specs/2026-06-06-hld-digital-life-novel.md §10.2（三阶段） | duanxian/design/specs/2026-06-06-hld-digital-life-novel.md | 部分：§9.2:328仅角色语言规则，无完整三阶段；素材L16仍是假锚点。新语言表达须依08/09推导，不借旧10.2。 |
| 19 | duanxian/writing/characters/2026-06-07-writer-R07.md:L14 | docs/superpowers/specs/2026-06-06-hld-digital-life-novel.md §10.3（情感） | duanxian/design/specs/2026-06-06-hld-digital-life-novel.md | 大体相符：§9.1:319情感经选择/停顿/缺席/保护/记录；§9.3:335禁直接命名，不能扩大为全部素材规则。 |
| 20 | duanxian/writing/characters/2026-06-07-writer-R07.md:L14 | docs/superpowers/specs/2026-06-06-hld-digital-life-novel.md §10.4（记忆） | （无 §9 完整同名条款） | 缺失：§9.1–9.3无完整记忆条款；旧10.4待核，新05直接承接批准记忆边界。 |
| 21 | duanxian/writing/characters/2026-06-07-writer-R07.md:L14 | docs/superpowers/specs/2026-06-06-hld-digital-life-novel.md §10.6（通讯窗口） | （无 §9 完整同名条款） | 缺失：§9.1–9.3无通讯窗口条款；旧10.6待核，新05依据批准文字接口。 |
| 22 | duanxian/writing/characters/2026-06-07-writer-R07.md:L14 | docs/superpowers/specs/2026-06-06-hld-digital-life-novel.md §10.8（禁用语） | duanxian/design/specs/2026-06-06-hld-digital-life-novel.md | 仅逐项可比：§9.3:335–339五禁项；素材另含E10:123记录不早披露，不整表等同。 |

已执行隔离漏第22项与将10.4机械改9.4反例，均被拒绝。部分/缺失仍为历史依赖，未制造9.4/9.6/9.8；新版不消费无证据旧规则。

## 四项 high 完整链路

| ISSUE | 源/旧反例 | 批准→人物→事件→信息→场景→适配 | 逐边核对 | 正负例 | 结论 |
| --- | --- | --- | --- | --- | --- |
| #8 保护 | E02 supporting_characters/1周岚及/2程予安；E04:38–44/59–73、E05:20/34旧维护例外邻边 | 01人物源→04 R3/R4及R17→06 E05→07 IO02/03/28与IO15→09 PROTECTION→10 M01–03 | 旧参与/协助袭击因果退出；既有档案/协查证词不等于参与；秦峥原因层与梁策/贺闻钧公共行动分离；亲属不是筹码。 | 正例：最小必要保护及同意不授予亲属行动权限；NEG-AUTHORITY拒绝保留ID的参与者偷换。 | PASS结构；D01具体机制BLOCKED_OWNER，旧文字尚未重写。 |
| #9 初醒/接口 | E02 /world/environments/2、/10；E06:23/30/53–54/67–74；E11:91相容过去片段 | 01 DIALOGUE/能力控制→04 R0/R1→05 E1/E2→06 E03/E06→07 IO06.0/06/08/11→09 AWAKE/REVIEW→10 M05–08/16/25 | E03.1沈逾输入先到，E03.2实例响应；当前声光/键压/精确十秒退出；过去片段不当当前感官。IO09却早于实例启动。 | 正例：已送达核对文字及有限记忆；NEG-CHANNEL、LATE-RECEPTION、SENT-NO-RECEIVE拒绝越权及缺到达。 | FAIL：ACC2-002；正文PENDING_WRITING。 |
| #10 终局 | E02 /decision_controls/4、/storylines/connections/1、沈逾职责；E07–E11两旧方案 | 01悬念/主体/执行控制→04 R0/R1/唐黎/苏望舒→06 E09–14→07 IO16.1/17/18/19/19.1/20/21/21V/22→08 S0–S7/KO1–4→09 FAREWELL/AFTERMATH→10 M09–15/21–24 | 项目危机结果E09.4不自动到实例，E09.5文字转达；意图形成后内部POV关闭；沈逾执行、唐黎核验、苏望舒受控保管；无活动备份/复活保证。06入口及执行ID仍冲突。 | 正例：请求/意图/理由分列及REC1/1V分源；NEG-ENDING在执行者正确仍拒绝早泄；SELF-STOP在同步记录仍拒绝自停。 | FAIL：ACC2-003及上下游ACC2-002；D03待签，正文PENDING_WRITING。 |
| #13 记忆/核验 | E02 /world/environments/8、/10；E14:12/25–26；E11:95/155/187–199/343/363–369 | 01 MEMORY→04 R0/R15→05 E2/E4→06 E07/08/09→07 IO13/14/15/21/21V/24.3→09 VERIFY→10 M16–22/28 | 主观触发和缺口→hypothesis→现实人员取证核验→授权行动；REC1无L2，REC1V外部形成，Shen E07.3早知不在E13.2初知；具体归属仍D02。 | 正例：缺口保留、失败回退、外部批注独立；NEG-MEMORY和L2-IN-REC1拒绝标题伪装与无输入输出L2。 | PASS能力结构；正文PENDING_WRITING，D02具体字段暂停；E07/IO13关联仅列O2。 |

## REG-08..13 正例与负例

| 回归 | 相容正例 | 实际隔离负例 | 结论范围 |
| --- | --- | --- | --- |
| REG-08 | 04 R3/R4、09 PROTECTION：无辜+同意+公共救援，保护不是参与报偿 | NEG-AUTHORITY | PASS（D01定值未解锁） |
| REG-09 | IO06.0 E03.1先收，IO06 E03.2回应；E11:91过去片段可作相容素材 | NEG-CHANNEL / LATE-RECEPTION / SENT-NO-RECEIVE | 局部PASS；跨场景ACC2-002仍FAIL |
| REG-10 | KO1请求文字与KO2/3记录分列，沈逾执行、外部核验、静态保管 | NEG-ENDING / ENDING-SELF-STOP | 对象拆分PASS；全链ACC2-003仍FAIL |
| REG-11 | IO10只到沈逾；IO11 E06.3到实例，E10用；室内详情留沈逾POV | NEG-CHANNEL / NO-RELAY / LATE-RECEPTION | PASS局部合法转述 |
| REG-12 | 未签D02时停止L2具体归属/接收/披露，只有核验和分级结构可用 | NEG-IDENTITY / PACKAGE-OWNER | 门禁修复PASS；所选版本BLOCKED_OWNER |
| REG-13 | IO21只含实例主观线索/假设，IO21V另列现实核验者批注 | NEG-MEMORY / L2-IN-REC1 | PASS；无正文落地声明 |

## §6.3 隔离反向测试

七个必测NEG逐一在.kunora/acc2-work/negative/副本改动，U原件hash保持。另加8个补充反例。每例expected=FAIL、actual=FAIL，故test_result=PASS；这是“错误副本被拒绝”，不是候选整体通过。语义例由验收者对照批准源人工审查，脚本负责唯一替换、保存副本与hash；没有宣称通用自动语义判定器。清单遗漏/时间单调/缺接收用机械检查，具体方法逐例保存。

| 用例 | 注入与拒绝理由 | 实际 | 测试 |
| --- | --- | --- | --- |
| NEG-AUTHORITY | ID与人物名未变，但保护因果改成参与，直接违背无辜控制；不知道全规模不能豁免参与。 | FAIL | PASS |
| NEG-CHANNEL | 无文字发送与接收，编辑遥测及室内感官被越权借给实例。 | FAIL | PASS |
| NEG-MEMORY | 主观回忆标题不能许可可寻址数据库和客观身份确认。 | FAIL | PASS |
| NEG-ENDING | 执行者正确仍不能使告别前内心早泄合法。这里不以告别时合法请求为反例。 | FAIL | PASS |
| NEG-IDENTITY | 角色职务不构成同一身份或新罪责批准。 | FAIL | PASS |
| NEG-STATE | #7本体及正式复验未取得，旧P1/open未关闭，不能靠候选状态改名放行LLD。 | FAIL | PASS |
| NEG-PACKAGE | Required ledger absent from manifest coverage | FAIL | PASS |
| NEG-LATE-RECEPTION | [(3, 1), (4, 1), (3, 2)] | FAIL | PASS |
| NEG-SENT-NO-RECEIVE | [(9, 5), None, (10, 0)] | FAIL | PASS |
| NEG-NO-RELAY | 项目不等于实例接收者；删除转述依赖后评估缺少合法输入。 | FAIL | PASS |
| NEG-L2-IN-REC1 | R-07默认未接收L2，不能在其原创主观记录输出该事实；现实附件不能反向赋予生成者知识。 | FAIL | PASS |
| NEG-ENDING-SELF-STOP | 记录同步不赋予实例自关停权限；执行者仍须沈逾。 | FAIL | PASS |
| NEG-PACKAGE-OWNER | 推荐不构成签认；与D02 owner_pending及12暂停门冲突。 | FAIL | PASS |
| NEG-MIGRATION-OMISSION | 22项输入删掉第22项；完整性比较发现缺禁用语指称。 | FAIL | PASS |
| NEG-MIGRATION-CHAPTER | 第20项机械把10.4改为9.4；实际HLD风格章只有9.1–9.3，语义复核拒绝。 | FAIL | PASS |

## 独立上下文消费与密封

Owner预授权的唯一子Agent sealed_consumption以fork_turns=none启动。先读12，再README/00–05/11；未读取旧正文、旧run、上轮验收、主验收发现或13自检，未访问网络。先重建初醒、审查、保护、核验、现实阻断、告别、善后七场景，再于2026-11-14T06:41:31.188696+00:00密封；此后首次读取06–10作对照。

密封稿16195字节，SHA-256=5e111773750cbb3d7fe24dec5b52bde21ff60f27bfb0a8553a3e149bb5dd8769。read_list每项hash、密封全文、对照全文均嵌入evidence-index.independent_consumption，五文件可携带证据，不依赖忽略目录存活。

对照结果：局部首回应、合法转述、现实阻断及主观/外部记录可重建；C1当前实例启动前已有运行日志、C2事件入口授权循环及执行ID错指需源包修正，故消费FAIL。C3字段暂停差异按观察O1保守处理，不单独作为确定失败。密封稿中“先沈逾阅读后苏望舒接收”经08补齐为E13.1移交后E13.2阅读；这是允许材料补足，不据草稿推断错误惩罚候选，密封稿保持原样。没有用旧正文替候选补事实。

## 来源、历史与工程边界

机械探针23项：22通过、1发现失败（聚合边只覆盖18/23关系）。15个清单条目实算字节和SHA一致；manifest单独绑定不自哈希；75控制源hash/Pointer与投影字段核对、完整控制token解析通过；35条台账单行数值顺序无失败（内部/终态人工复核），不证明跨对象时间正确。

BASE的1444个既有文件未改；候选最终修订只改U。E03 author-decision approval_scope=conception、同run completion ready不扩大为HLD批准。旧E16 P1/open与pending/blocked完整保留：integrity的v3元数据与L33 v2、package及manifest声明分栏，实际对象尚待受控核实。树中三个正式本体文件名未命中只说明Git可见范围，不否认外部存在。

#1七runtime及三个测试旧ROOT/ENTRYPOINT逐一静态登记（含正确路径存在/重复engine路径不存在）；未运行坏入口、未做未经授权的工程修复。#2按BASE NUL安全树枚举一层82个skill；#4三样本text/eol六项unspecified仅复现前缀风险，不证明全量损坏或修复。所有命令结果及完整逐项路径见audit。

历史终局复核：六月E11:347直示选择，351–387读者先见记录，448–460沈逾后读，E10:123只是未落实的同步素材要求；七月E07:26是S15真实早知，:40是story_anchor S15 / narrative_reveal S17，不能混同。E12隐名、E09/E13不同披露及E11三组显名只用于列明D02选择，未替作者定责；E14及E11的像素/数据库/身份断言进入M16–22/28改写，不能以素材许可填正文证据。

## 待决、限制与最终处置

O1：11:50/53暂停IO24.1/24.2/24.3的候选接收/披露字段，11:82及12摘要称L0/L1“结构”可消费。结构与具体字段可以区分解释；尚不足证明新的无条件L2捷径。保守按正文暂停全部候选具体字段，Owner签认前不定稿。

O2：06 E07 evidence列IO13，后者E08.1才到达；E08又允许E07进行中。引用可能是后续关联而非已消费输入，不能仅凭编号认定事实先用后到。需明确事件重叠及evidence用途，不在本报告发明新传递。

O3：IO03把沈逾接收与可选择告知实例并列；实际采用前需明确选择已发生。当前E10必要输入不依赖IO03，未证明实例已越权使用。

O4：08 KO-1请求与KO-2意图已明列，不再按“没有分列”判FAIL。具体对白不得一边说“我已最终决定”一边宣称只呈请求；L2沈逾早知/读者迟知也需未来文本验证公平性，均属PENDING_WRITING，不能预判实现必然失败。

O5：11:61的D03问题摘要仍沿用“读者后知”概括六月方案，落后于08§H的准确对照。作为非决定性摘要残留记录；ACC-006指定的02/08/10/13/manifest本轮修复已成立，不据此抹掉通过项。

D01–D03=BLOCKED_OWNER；#7=BLOCKED_EVIDENCE；#1/#2/#4/#6=DEFERRED_ENGINEERING；28条适配项均PENDING_WRITING；Owner manual-review=OWNER_PENDING。正式HLD/LLD准入未获准，候选不是canonical替代品。

本轮FAIL已具体列于findings和correction-instructions。剩余修订预算0，不启动新实施或复验轮；仅交Owner决定后续处置。机械交付验证只证明文件、白名单与秘密扫描等条件，不会改写内容FAIL。提交后的机械与远端SHA检查由交付执行记录承载，本报告绑定的是被验候选而非自身提交，不伪造未来成功。
