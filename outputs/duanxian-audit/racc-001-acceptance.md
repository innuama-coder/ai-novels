# 《断线》工作项 B 独立复验报告（r3）

作业：`duanxian-audit-raccr3-001`；日期：2026-11-12。**总 verdict：FAIL。** 仅验收下表封定的 `ffb8c9a…` 候选，不以最新分支或实施自评替代证据。两段机械脚本、候选历史范围、远端交付通过；全文阅读硬门仍未满足，批准字段、感知边界、测试职责及若干归纳仍有可定位错误。因此不能将此候选按 PASS 交工作项 C。执行控制证据子门为 BLOCKED；缺日志不等于已发现越权，也不改变已确定的内容 FAIL。

## 1. 输入封定、适用标准与独立性

| 输入 | 完整提交 SHA | 文件 SHA-256 |
| --- | --- | --- |
| 内容基线 BASE | `92573f1cca40f37cee04d2beb8708ff33ba603d6` | 全部故事、实现与历史状态证据固定在此树 |
| B 定义书 `outputs/duanxian-audit/rdef-001-def.md` | `c423216ef9f8bbe8a9846b1a4d877d298a9334f7` | `b0017ed4db8c46c0b368f01543659b93077a7b2aed94fb459137e40b4e107975` |
| A 定义书 `outputs/duanxian-audit/gdef-001-def.md` | `99e18a0d2f3c8d4d8f069a3150622f8f68a55912` | `68ec7c0aabd98e2d4860bc0ce36e83f30b03ad2b84626fcc4c7bd9c9f7cde675` |
| 已获确认的目标总结 `outputs/duanxian-audit/goals-summary.md` | `a6935ddcdf6716cf96bfdc6804e0cde29471bb5c` | `ac7f045a92af07c23b0b7a15a59421de25756f60883d4a3c9adc75b47e90155e` |
| 历史验收 `outputs/duanxian-audit/racc-001-acceptance.md` | `d7fc94ac9fe4490c523bb112f6c4fb7a8115abe1` | `cd79394fe966cb109382f2e8b8f4ebe462de1c43a215b3b0649e4ed475faf3cb` |
| raccr2 复验，同一验收报告路径 | `8a8280e28c5ab5b6369cca1a7fde3e7e822aec3d` | `f1811317b130fe24c41da0e8acc4c32b46f1b88a13227644c444ab572495ff35` |
| 本次实施候选 `outputs/duanxian-audit/implementation-review-report.md` | `ffb8c9a10b51ae23000bc4e9fbd0a203dec120f1` | `fe0dc30f0b16d1101edc1826079ef1e970334312dd463006798c540d05c71f13` |

上述六份文档均按完整 SHA 取得并全文读取，重算哈希与交接一致。下文 **R:L数字** 指本次候选原始行号，共 260 行；不沿用前版的 227 行定位。BASE 文件按原始文本行号引用，单行 JSON 使用 JSON Pointer，格式化输出不作为原始行号。历史验收只用于确定修正义务；事实仍回查 BASE。

封定 B 定义书实际 §6.2 为 M01–M03、C01–C03、E01–E03、A01–A05、T01、I01、S01、X01，共十八项；修正模板在 §6.3。启动摘要的 M01–M04、S01–S07、A01–A09、§6.4 对应 A 定义书。本文以 B 十八项为主判决，§7 保留摘要对照；不把 A 的六节拟人化、2000–4000 字门套给 B 的九节、6000–12000 中文字报告。

本轮按启动文件全文逐项确认后，立即写入本次 ACK，再开始业务 fetch。验收主树始终处于 `remote-agent/duanxian-audit-raccr3-001`，从 BASE 开始。候选仅通过固定对象读取及本作业目录内 detached 检查树核验，未切换实施分支到主树。全部 1444 个基线跟踪文件与 Git blob 逐字节核验相等，允许随后读取本地冻结源；字节一致性不冒充全文阅读。

采用 Git、标准库、静态文本/AST/JSON 分析，未导入项目模块，未运行仓库 CLI、pytest、validator、构建或小说流水线，未安装依赖、访问外部资料、修改来源或创建 ISSUE。验收抽查不替实施完成全量阅读。本次交接明确实施 rint2r3 为 GLM-5.3 重派，接受该明确安排，不以旧定义中的 kimi 分工直接判越权；实际运行模型与全过程仍需执行记录。

## 2. 机械、提交、远端与可复现统计

| 检查 | 本轮直接结果 | verdict |
| --- | --- | --- |
| Git / Python | `git version 2.43.0`；`Python 3.12.3` | PASS |
| B §6.1 文件脚本 | 从封定定义书提取原样 Python 块，在 detached 候选根运行，退出 0：`FILE-PASS Chinese-count=8702 bytes=54839 sha256=fe0dc30f0b16d1101edc1826079ef1e970334312dd463006798c540d05c71f13` | PASS |
| B §6.1 范围脚本 | 第二 Python 块原样运行，退出 0：`SCOPE-PASS candidate=ffb8c9a10b51ae23000bc4e9fbd0a203dec120f1` | PASS |
| 提交链 | BASE → `00cc828650a2f1318d4eab0a994d5b68babbf799` → `b967b0736bc8065e08a4c2957d680225204f0c4b` → 本候选；三次均单父、仅 A/M 实施报告，最终只有该文件新增 | PASS |
| 候选元数据 | author/committer 均 `remote-agent <remote-agent@kunora.local>`；日期均 `2026-11-12 22:40:10 +0800`；消息 `docs(audit): fix review report per racc-001 F01-F10 (duanxian-audit-rint2r3-001)` | PASS |
| 远端封定 | `git ls-remote origin refs/heads/remote-agent/duanxian-audit-rint2-001` 返回完整 `ffb8c9a10b51ae23000bc4e9fbd0a203dec120f1` | PASS |
| 哨兵 | 编排补证 `DXARINT-DONE-ffb8c9a`、`R3PUSH-DONE-ffb8c9a` 与远端前七位相符；`DXARINT-DONE-00cc828` 仅绑定历史候选 | PASS（编排补证＋独立远端核验） |
| 文件安全与结构 | UTF-8、无 NUL、九个固定二级节、五标签、BASE、秘密与行首占位模式均通过；全文与提交信息未见实际凭据、虚构 ISSUE 编号或独立验收通过声明 | PASS（语义真实性另判） |

两段提取脚本文本的 SHA-256 分别为 `bbf051015c7ddcb487bfca564242553e784dfb1ebcaaa661cc04155e33cd8956`、`74032f90db3b022c483c3c7f9756a8b6f3a3fb44c42dc0aff65411dd3298db3f`；未改变字数算法、断言或 HEAD 参数。Git 可见范围不证明实施忽略区没有写入或从未执行禁令命令，后者保留为 X01 补证项。

统计规则为 `git ls-tree -rz --name-only BASE` 的 NUL 清单；文本按 UTF-8 解码及 `splitlines()`；字面命中按原串逐行/逐文件计数，词出现次数用 `str.count`；测试文件按 basename `test_*.py`，不是运行用例或通过数。独立复算结果：

- 1444＝根层 6＋duanxian 148＋engine 1290；engine 为 README 1、docs 83、skills 669、harnesses 404、scripts 5、tests 6、testing 10、tasks 112。
- 82 个技能目录，56 个测试文件分布 28 目录＝15 个 HLD＋6 个 conception＋7 个其他目录；其余 54 目录无此文件名测试。候选撤销“一技能一测试”正确；八组技能分类虽加总为 82，但“访谈 8/通用 32”等未列成员与互斥归组规则，不能由总数相等证明完成分类闭包。
- 四 harness 文件/测试数分别 92/0、107/25、152/12、53/0；runtime 直接 `.py` 19 件，共 20446 行；32 schema＋1 索引；31 zip 对原始字节 SHA-256 得 23 唯一值，其中 8 组各两份相同。未执行发行工具。
- 字面串 `docs/superpowers`：79 文件、219 命中行＝duanxian 31/88＋engine 47/119＋根 1/12。根文件是 `.zcode/plans/plan-sess_316609e2-5263-4909-a27a-c47b17476339.md`，命中 L5/7/29/30/31/42/43/44/48/49/62/64。此修正通过；命中数不等于坏链接数。
- 三机器 basename、revision-037/038 basename 在跟踪清单均零匹配；只说明 BASE 留存。R:L106–108 的 7 旧词×3 批准文件、K1–K8、6 新名×两个 canonical 版本均按所述零命中；v3.0 中沈逾/顾衡/周岚为 5/9/11 次。词表限定修正通过。
- R:L31/L252 的重构计划“89 行”对应 `wc -l` 的 89 个换行符，实际有 90 个逻辑行（末行无换行），须说明计数口径，不据此指控未读；R:L32/L135 的 CLI“1082 行”则与 BASE 的 1081 个逻辑行/换行符不符。
- R:L199 称修订表“四栏”，全部 17 件实际是五栏：版本、日期、作者、变更摘要、状态。R:L129 的“七类”汇总又把附加关系项计入，2＋4＋1＋1＝8；应将七控制和附加关系分列。

## 3. B 十八项主判决

下表 PASS 不抵销其他必要门失败；每项均绑定本次候选。证据详情与修正动作分别见 §4–5、§8。

| ID | 候选定位与短引 | 检查方式、依据及判定 | verdict |
| --- | --- | --- | --- |
| M01 | R:L3–4，基线/定义/A 基准 | 完整对象与六文件哈希核对，目标总结六节对照；未换用最新 main | PASS |
| M02 | R 全文及候选提交 | 两段原样机械脚本、三提交历史、元数据、远端、哨兵后缀核验，见 §2 | PASS |
| M03 | R:L66、L167“作者门” | 秘密/占位通过；但错误 JSON Pointer、虚错归属的测试引文仍被当作核验事实。属内容不真实，不据此推断故意伪造 | FAIL |
| C01 | R:L14–37“硬门仍未满足” | 覆盖账 29/141/1274 算术闭合，但 141＋1274 未完成全文，且未逐层拆分二进制/重复投影/独有未读；B §2.1/§5.2 硬门未达 | FAIL |
| C02 | R:L47–62 六行矩阵、L118–129 | 形式齐全；合格标准仍把导航挂入语义门，感官对照错释批准规则，部分程度由不充分证据归纳 | FAIL |
| C03 | R:L147–167“闭包补全” | 多数 harness 只列 README/manifest；未落实全部实现职责输入→处理→产物→拒绝链及对应正负例；五 validator 的测试职责有错，见 §4.4 | FAIL |
| E01 | R:L203–256 索引及全文 | 完整路径、相对路径、简称/运行路径逐类查；源对象多数真实，但 Pointer、行号和未定义文件简称仍错，见 §4.2 | FAIL |
| E02 | 三门/权限/完成/冲突/全部 IC | 逐项回读双向证据；保留有效哈希与真实旧路径缺陷，拒绝操作数据合规、零命中证明无反例、渠道缺位等过强推论 | FAIL |
| E03 | 第二至七节剩余结论 | 按首/前中位/末样本核查并扩查同类定位、计数、测试归属；发现不支持项，见 §5 | FAIL |
| A01 | R:L47–62、L121 | 六问、读者未定和主要阶段方向保留；“批准输入限操作数据”的解释与 A 总结第一/五节的文字接口边界不符 | FAIL |
| A02 | R:L120–131 七控制＋关系 | 信息分层已补、五类支持已撤；仍误判击键压力合规、从无同名推无反面工具化、将知晓时长与知晓保护动机混作直接矛盾 | FAIL |
| A03 | R:L66–86、B-E008–011 | 三个重算、引用一致与本体不可得均重新核实；`/approval_record/unresolved_items` 不存在；导航仍被归入语义门，未完全修复 | FAIL |
| A04 | R:L94–113、L178–179 | v4 日期、旧 HLD pending、LLD superseded、HLD implementation-candidate/not-run、现实进度未知均保留正确边界。正文仍为历史素材，未冒称正式发布；定位/覆盖不足另归 E01/C01 | PASS（状态与版本边界） |
| A05 | R:L47/57/66/81/143–163/175–182 | 五标签存在，但许多事实行无就近标签；L81 将实际核验结论标流程规范；“新版叙述契约”与 L125 历史限定不统一 | FAIL |
| T01 | R:L139/154–169/258–259 | 不把 12/14 交接失败数当本轮结果正确；仍错引作者门、正负例分类失准。执行记录子门另为 BLOCKED | FAIL（内容）；执行子门 BLOCKED |
| I01 | R:L190–199 十条记录 | 全条审核；001/002 等主要事实成立，004仍全称概括有效路径，008将仓库缺本体扩大为获取渠道缺位，009四栏错误；部分应然/验证未落具体证据 | FAIL |
| S01 | R:L175–184 | 无总百分比，分对象及现实未知正确；“四 harness 闭包”总结超出实际取证，历史完整性报告的语义与形式失败混放，受前述门证据错误影响 | FAIL |
| X01 | R:L258–260、Git 历史与控制输入 | Git 单文件与源树一致 PASS；未取得三轮实施原始命令/退出码/忽略区写入/实际模型记录。已在会话请求，本作业控制目录未发现所需记录 | BLOCKED（执行证据） |

主表计数：3 PASS、14 FAIL、1 BLOCKED。BLOCKED 为 X01；T01 等的执行子项限制不另计第十九项。总 FAIL 来自已确认内容与覆盖问题，不由缺日志替代。

## 4. 全查证据与修正效果

### 4.1 批准字段、哈希与三门

独立读取两份批准 JSON 的所有字段。`duanxian/conception-approved/author-decision.json` SHA-256 为 `4f5a070d22a92fb211b9e99709e04e05b16460aa52ae40c7ebb0eaf49249e2bd`，`duanxian/conception-approved/conception-completion.json` 为 `4eabd4af2b249493f3aae1a2668c4de9b37dea7f61628e1b454293e49587d127`。两者 run 相同，approved/ready 限 conception；completion 九个 stage 键及所有路径/hash 均已逐字段查看。

| 候选短引/定位 | BASE 证据、复验与限度 | verdict |
| --- | --- | --- |
| L66/L214 `/approval_record/unresolved_items=[]` | author-decision 的 `/approval_record` 只有 `event_seq` 与 `text`；实际空数组是顶层 `/unresolved_items`。事件序号已改正，空项字段仍错一层 | FAIL |
| L72–74 三对象重算 | 作者决定 hash 等于 completion `/author_decision/sha256`；completion hash 等于批准 README L22；HTML hash `80cfc4d82d77683324808ba3f96817914c24fd1de007fae70641789dedf65e36` 等于作者决定 `/human_review_package/html_sha256` | PASS |
| L75–77 引用一致 | P1 manifest `bba81d35…`、P1 completion `42e307d1…`、H1 completion `28ec088d…` 在两 JSON 对应 Pointer 值一致；仅比较引用，未宣称重算本体 | PASS |
| L78–85 未留存与 revision | completion 的 `/development_handoff`、`/validation`、`/h1_html_manifest`、`/run_state`、九 stage 引用以及 author 的两个 package 引用均为运行相对路径；批准 README L18/L21 为最终 038，completion 引 037。可作记录时点解释，但未验证状态本体迁移 | PASS（限留存边界） |
| L51/L61/L82 “语义门＝review_path”“语义门有结构化留痕” | `duanxian/conception-approved/human-review-report.json` `/review_path` 五对象只有导航 ID、kind、阅读问题/秒数、可见元素 ID 等，无独立评审 verdict。即使补“非语义判定本体”，仍不应把导航归作语义门执行留痕。最终契约 L38、L64–79 要独立逐元素审查 | FAIL |
| L83 e2e fixture 已更名 | `engine/testing/test_conception_autonomous_v2_e2e.py:L112–125` 的 `_test_fidelity_review` 确为忠实度 fixture；`engine/harnesses/novel-conception-autonomous/runtime/author_decision.py:L80–88,L202–256` 确有签封/schema、状态和 P1 绑定拒绝 | PASS（静态机制） |
| L167 “契约测试 L108/L130 production never synthesizes this gate（作者门）” | `engine/testing/test_conception_autonomous_v2_contracts.py:L108–117` 为 schema 可解析，L130–142 为相对路径拒绝；该引文实际在上述 e2e 的 L119，且 this gate 指忠实度。第三节修正未同步至第六节 | FAIL |
| L86 人审数组及 HTML 计数 | JSON SHA-256 `f3d848f15547e77bcb0a0d54b288efe9989e53e286470a200544966af173c640`；六数组长度 8/5/3/4602/4602/3924，导航秒数合 587；HTML 5 SVG、0 script。只作结构证据 | PASS（计数子项） |

不能把真实批准撤销，也不能把上述静态核验替代机器可消费、独立语义和当前状态复验。R:L60 的“后两者本体不可得”还需明确对象：作者决定记录本身可得，不可得的是正式运行与 validator 所需完整链，不能笼统说作者门本体未留存。

### 4.2 E01 全量引用审核与定位纠错

全文逐项核对 B-E001–050、六问、故事条目、代码条目与 IC。程序提取 33 个完整 ASCII 源文件路径，全部在 BASE；中文 HLD 文件用 NUL 清单核验。其余按文内已给目录展开：B-E019–023 同 07-13 HLD run，B-E031 的 runtime 模块，B-E039 的五 validator/对应测试，B-E027 的 writing 集合。目录/通配按冻结清单处理；P1/H1/state 等明示未留存的运行引用不按假源文件处理。

| R 定位 | 原文短引/问题 | 正确源定位及处理 |
| --- | --- | --- |
| L43/L207 | 六章范围“第六章 L129–151” | `duanxian/novel-goals.md` 第六章还含 L153–159 文学质量与全书定稿；“分部、章节与覆盖目标”标题在 L115，第五章整体 L105–127 正确。章节主题已大幅修正，范围仍需完整 |
| L97/L222 | proposal L39/L45–46 被接在“Agent pass、人审 pending”前 | `duanxian/design/specs/2026-07-05-duanxian-proposal.md:L39` 是非冻结材料，L45–46 为结构/关系；Agent pass 在 L264，人审 pending L266，准入 blocked L267。增加正确范围未删除错误定位 |
| L66/L214 | 空项字段 Pointer | 见 §4.1，必须为 author-decision `/unresolved_items` |
| L123 | qianxu L152“对妻子的承诺不披露” | `duanxian/writing/characters/2026-06-07-writer-qianxu.md:L151` 才是该句，L152 为 K1 死亡非情感高潮；L17/L153 引用另有正确支持 |
| L139/L235 | 三测试都在 L23 执行模块 | attempt/topology 的 `exec_module` 在 L23；`duanxian/conception-production/tests/test_line_sequence_review_cli.py` 因多一行 PROTOCOL，在 L24，L23 仅登记 `sys.modules`。路径成因同型不意味着行号一致 |
| L143/L149/L237 | store L617–620“非空残留拒绝”、return L147–156“按责任阶段路由” | `engine/harnesses/novel-conception-autonomous/runtime/production_store.py:L621–628` 才完成残留检测/拒绝；`return_routing.py:L160–178` 才推导并校验目标/恢复/失效字段。原范围只含入口/注释/schema 调用，不足作实现闭包 |
| L167/L248 | migrator L2–10 引“Silence…neither route” | `engine/skills/novel-interview-b0-migrator/SKILL.md:L23–30` 是两路线与 Silence 句；L3/8–10 支持职责说明，不能替代精确引文定位 |
| L167/L247 | 契约测试被引为作者门 | 见 §4.1，原文件真实但职责和引文归属错误 |
| L35/L121/L233 | `apartment.md`、`spaces/meeting-room.md` 等简称无完整展开规则 | 实际为 `duanxian/writing/spaces/2026-06-07-writer-apartment.md`、`2026-06-07-writer-city.md`、`2026-06-07-writer-corridor.md`、`2026-06-07-writer-meeting-room.md`；人物也有 `2026-06-07-` 前缀。可推知对象不等于按原文完整路径可复现，应列完整清单或定义统一映射 |
| L165/L212 | check-attr“三真实路径”未列参数 | 本轮独立使用 `engine/skills/novel-hld-finalizer/SKILL.md`、`engine/harnesses/novel-hld-autonomous/manifest.yaml`、`engine/skills/novel-development-baseline-preparer/SKILL.md`，六项 text/eol 均 unspecified。结论支持，候选需给原命令路径以便复现 |

B-E001–007、012–030、032–040、043–050 的对象均能按上述清单/上下文定位；表内错误仍使 E01 FAIL。新索引比历史版本更完整，但文件存在不能替代 Pointer、行号或语义正确。

### 4.3 七类故事控制及附加关系全查

本表批准源均为完整路径 `duanxian/conception-approved/human-review-report.md` 的非样片正文；旧正文完整路径为 `duanxian/novel-text/2026-06-07-duanxian-novel.md`，本轮从 L1 到 L508 全文读取。全部 17 writing 文件进行关键词/引用/表头核对，并对相应控制定点扩读；不把这些程序扫描称为 17 件全文阅读。两侧分别为当前批准与历史素材，不把旧稿差异判成批准后的生产回归。

| 控制/候选位置 | 双向证据、反证与结论 | verdict |
| --- | --- | --- |
| 主体/记忆 L120 | 批准 L277–289、L382–419 限主观记忆与新主体；旧正文 L183–205 为像素重采样/匹配，L381/L476 为“这是我的”。已从整体支持降为局部主题支持，并登记机制差异 | PASS（该收窄修正） |
| 当前感官 L121 | 批准 L241“通过文字”、L289“只能收到文字与短促记忆”、L389“只能接收浮现的文字、访问受限记忆”；候选却概括为“输入限于操作数据”，将旧正文 L245 击键/删除频率、L271 按键压力判“合规”。这些数据是否经授权文字转达未给证据；批准并未普遍开放操作遥测接口 | FAIL，属于实质边界误释 |
| 会议信息来源 L121 | 旧正文 L284–318 会议与 L335/L341 内部使用十秒时长之间未交代传递链，缺口登记成立。`duanxian/writing/characters/2026-06-07-writer-shenyu.md:L214` 说“不知道她在保护它”，不是“不知道沉默时长”。两命题可同时成立，不能直接定“同一事件一处引用、一处否认可知”的逻辑矛盾 | FAIL（确定矛盾过强）；来源未交代的疑点保留 |
| 权限/现实核验 L122 | 批准 L295–315、L468–475、L524–531 要专家/硬件/授权与现实阻断；旧正文 L359–369 是遇袭档案推理，L464–476 为阅读记录。已明确无对应气象武器处置实现，不再以无越权等同已落实授权链 | PASS（限定旧正文对照） |
| 亲属同意 L123 | 批准 L423–449 保留亲属主体性；旧正文＋17 writing 对程予安/周岚均零命中。只能支持未找到同名对象，不能推出候选所写“仅能证明无反面工具化段落”；旧版可能有不同名字/关系，须做语义对照或保留未知 | FAIL（否定性推理） |
| 信息分层 L124 | 批准 L253/L315 有必要阈值、行动/原因层；旧正文 L407 私密保留、L417 开放无限制。独立控制已补，说明旧版机制差异和缺对应交付成立；“张力”可作推断，不额外判旧稿内部必然矛盾 | PASS（该修正） |
| 关停/备份 L125 | 批准 L271/L283/L396/L510–517/L608–615 支持外部责任、无活动备份和不保证连续性；旧正文 L409–441、`duanxian/writing/characters/2026-06-07-writer-R07.md:L74,L91,L249` 是自主关闭。新版依据已回到批准正文，七月契约标历史正确 | PASS（该修正）；L47/57“新版契约”仍须统一称谓 |
| 开放边界 L126 | 批准 L327/L608–615；旧正文 L480–508 只是认知问题/余白，不覆盖法律身份、重载和互信全套。候选改为局部留白/无对应，未给复活保证 | PASS（该修正） |
| 附加关系 L127 | 批准 L147/L169/L396/L400/L411–419，旧正文“沈逾”一次及 `duanxian/writing/characters/2026-06-07-writer-qianxu.md:L1,L15` 的灰鸟/陆远，支持代际区分。当前关系“无法判断”可保留；“无正面实现”需明确只指没有落实顾衡/R-07这套批准关系，不能由名字一次否定旧稿所有情感线 | PASS（按其当前关系限定）；补清范围 |

R:L129 把附加关系纳入“七类”总计八项，应更正汇总。R:L130 的人物误解句可定位 human-review-report.json `/characters/constraints/0`；R:L131 正确保留样片非权威，最终交付契约 L26–44 直接支持。感官错误不允许用样片的声音、动作补证。

### 4.4 代码职责、旧链与分级

CLI 七个正确 `engine/skills/<skill>/scripts/run_v2.py` 在 BASE 均存在，重复 `engine/engine` 七路径均不在树。`duanxian/conception-production/run.py:L14,L41–47,L51–135` 支持静态装载问题；三测试 L12–13 的 parents[4]＋projects 定位也成立。本轮不运行这些入口，不将路径观察称作新的实测失败。标准库 spec 构造与后续 exec_module 是不同阶段，候选对此的内容修正保留。

`duanxian/testing/run_duanxian_conception_v2.py:L16–55,L80–146` 支持可配置 RUN_ID、三段回退和构建器/阶段调用；不能证明八月真实执行入口。17 testing 资产的 1＋3＋10＋1＋2 数量归类正确，但仍未完成各构建器输入来源、使用 run、写入位置与调用闭包的全读义务。

| 职责组 | 候选与实际证据 | 审核结论 |
| --- | --- | --- |
| 构思 harness | R:L149；`engine/harnesses/novel-conception-autonomous/runtime/production_orchestrator.py:L3466–3497` 确有锁、未初始化检查、revision-000 与持久化；store/author/return 机制见 §4.1–4.2 | 已给一条有价值的静态链；拒绝/退回定位需完整，不能等同全部职责闭包 |
| 访谈 harness | R:L148；`engine/harnesses/novel-conception-interview/README.md:L3–13` 规定跨技能顺序/证据/批准门，并列 validator/eval 入口 | 零 test 文件不等于测试完全缺位；README 职责不是成功/拒绝/退回实现链，缺项仍 FAIL |
| HLD harness | R:L150；manifest L3/L6/L14–27/L44–48、`engine/harnesses/novel-hld-autonomous/releases/0.1.0-acceptance.json` 及 `releases/0.1.0.md:L3–5` 支持候选态、作者门要求、42 bounded 未执行及 declaration-only | 发布资格边界正确；未补实际成功/拒绝/失效闭包 |
| 通用交付 harness | R:L151；`engine/harnesses/kun-workshop-intranet-delivery/README.md:L3–12` 支持内网交付/授权边界 | 非小说完成证据；只列 README 未满足闭包，不能凭标题“四 harness 闭包”视为已补全 |
| proposal validator | R:L154；`engine/tests/test_validate_proposal_contract.py:L7–39,L41–89` 有正向 claim schema 和拒绝漂移；`engine/scripts/validate_proposal_contract.py:L12–18` 只是根/输入常量 | 测试定位有实质改善，但“常量↔测试清单”未说明实现中的检查、输出与拒绝函数闭包 |
| PRD validator | R:L155；`engine/tests/test_validate_prd_contract.py:L437–502` 有契约检查、删 rule coverage 后拒绝；`engine/scripts/validate_prd_contract.py:L17–23` 支持旧 run 路径迁移 | 保留有效反例；未把这些测试冒充本轮通过，完整能力仍需逐职责取证 |
| design-tasks validator | R:L156 把 L46/166/177/188 列“正例”，L72/138 列“拒绝例” | `engine/tests/test_validate_design_tasks.py:L46–58,L166–197` 实为构造 weakened 输入并断言违规；L72–75/L138–143 对现有包断言空违规。须按输入与断言判正负，不能照函数名分类；本行 FAIL |
| HLD validator/release | R:L157–158；`engine/tests/test_validate_hld_contract.py:L1185–1193,L1418–1420,L1500–1521` 分别为正向、文本包含、raises；`engine/tests/test_validate_hld_release.py:L80–97,L130–157` 为未跟踪拒绝、暂存接纳、checksum/快照门 | 文本检查不再冒称运行拒绝，修正成立；release 并非所有样本都测 root-not-cwd，候选现已区分职责 |
| 技能与运行时测试 | R:L163/L167；`engine/skills/novel-character-designer/SKILL.md:L5–11` 提示式职责、`engine/skills/novel-hld-writer/SKILL.md:L3–7` Legacy、migrator L23–30 两路线 | 无脚本不自动判缺陷正确；82 目录需明确归组及逐实现闭包。作者门引用错误见 §4.1 |

旧链应分别核查：`duanxian/design/runs/hld/2026-07-10-duanxian-hld-workflow/manifest.md:L9–14`、同目录 `gate-report.md:L5–13` 是 PRD 人审前阻塞；07-13 manifest L11–15/gate L14 是生成后待 HLD 人审。候选第四节主要展开后者，未满足 B 要求的逐 run 全查覆盖，不能把两个运行合为一次。07-08 LLD manifest L3/L17–18 的 superseded 错误记录不恢复为当前裁定。

R:L177 将旧 HLD 整体 fail/pending 放在“语义证据”栏，需更准确地分解：`duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/artifacts/12-hld-integrity-report.md:L32` 明记“Semantic consistency passes, but artifact 01 trace closure fails strict validation”，L33 是人审 pending，L34 准入 blocked。本轮没有运行该校验；只能转述该历史记录，不能抹平形式追踪失败与语义声明的区别。

### 4.5 全部 ISSUE 候选

本地 B-IC 编号不是 GitHub ISSUE；本轮全部十条记录均已核对。核心事实成立不自动豁免应然、根因、验证和范围字段。

| 条目 / R 行 | 双证核查与处理结论 |
| --- | --- |
| IC001 / L190 | CLI ROOT、七个路径与 loader 读取点直接支持静态缺陷；根因降为推断正确。保留；建议验证应针对七 runtime 装载，不能只靠一个 selftest 覆盖全部。 |
| IC002 / L191 | 三测试旧布局成立，允许归并为迁移族；line_sequence 的执行行是 L24，须同步索引。保留核心事实，定位修正。 |
| IC003 / L192 | 根 README L5、engine README L9 的 81 与实际 82 直接支持；历史原因标推断/未知正确。PASS（此条）。 |
| IC004 / L193 | 17 writing 反引号 LLD 路径各一条，按前缀迁移均找到真实目标；79/219 分母已修。`engine/scripts/validate_prd_contract.py:L17–23` 只证明该 resolver 的迁移规则，`engine/README.md:L27` 是布局约定，不能证明所有 engine 文档/代码旧路径均有效，也不能概括历史文本皆无影响。R:L159“缺陷仅限重复 engine 调用点”还漏掉本报告自身已证的测试 ENTRYPOINT、属性前缀等。仅修(a)的全称处置与 grep 抽样验证不足，FAIL。 |
| IC005a / L194 | `duanxian/writing/characters/2026-06-07-writer-R07.md:L14–16` 的 §10.x 与 `duanxian/design/specs/2026-06-06-hld-digital-life-novel.md:L312–339` §9 内容错位成立；日期修正、按内容迁移而非机械减号正确。保留历史追溯问题，不把“现行权威”混成批准 P1。 |
| IC005b / L195 | 未证明必须 frontmatter，已作为待规范取证线索；PASS 此降级，不新增违约断言。 |
| IC006 / L196 | 07-13 完整性报告 L25/L32–34/L57–58、final-hld-package L20–22 支持记录内 open/fail/pending/blocked；现实未知保留。manifest L15 是应然门。保留；新版流程如何接管由 C/Owner 决定，不用此验收给新准入。 |
| IC007 / L197 | 同完整性报告 L8/L11/L33 的 v3/v2，与 manifest L13 的 v3 唯一源有真实标签混用。保留；补明确应然来源和影响对象，不把元数据差异升级为 v3 无权威。 |
| IC008 / L198 | 批准 README L3 与根 `.gitignore:L11–18` 已明确不入库，政策修正成立。但 BASE 无本体不证明仓库之外“获取/重验渠道缺位”，更不能将其定为已证根因；只能说本验收未取得渠道/同版包。应降为待取证建议；同版 hash 与 basename 检索仍不足以验证 handoff 可消费性，需保留正式链验证方向。FAIL。 |
| IC009 / L199 | `duanxian/README.md:L22–23` 已有全局声明，局部提示是建议而非已证违约，此降级正确。17 修订表实为五栏，修正“四栏”；不得为满足建议修改旧稿，C 决定是否采纳。 |

## 5. E03 确定性抽样与扩查账

结论单位取表格行、编号条或可独立判定的事实子句，保留原始行号和顺序。先排除 E02 全查的已完成/直接冲突/权限/hash/作者门/ISSUE/七控制及相邻因果；剩余按首、中位（偶数前一）、末取样，不足三条全取。为防止修正只改局部，随后扩查同类全部计数、字段、测试归属与否定性推理。

| 节 | E02 外剩余池及选择 | 支持/不支持证据 |
| --- | --- | --- |
| 二 | L43 章节地图、L49 读者未定、L59 读者/渠道；三条全取 | 目标 `duanxian/novel-goals.md:L23–27,L129–159`、意图卡 L31：读者事实 PASS；第六章截止范围 FAIL（漏质量/全书定稿段） |
| 三 | L86 人审计数；一条全取 | JSON 六数组及 review_path 秒数、HTML 元素复算见 §4.1；PASS（结构计数），不推成语义门 |
| 四 | L94 v4 日期、L95 LLD 历史反斜杠路径；两条全取。词表与隔离结论已全查 | `duanxian/design/specs/2026-06-06-hld-digital-life-novel.md:L10`、`2026-06-06-lld-digital-life-novel.md:L36–39`，均 PASS |
| 五 | 无剩余 | 七控制、附加关系、样片和汇总全部 E02 全查，不能以无剩余免检 |
| 六 | 存量单位依序：L143 runtime、L145 schema、L161 testing分类、L163技能分类、L163测试分布、L163 zip、L167 Legacy、L167发布数字、L167重构计划；九个，首/中/末为 runtime/测试分布/计划 | 19/20446、56/28、旧根历史背景通过。扩查全九项：其余数量支持，但技能分类成员不闭合可审、计划逻辑行数口径不清；新增测试正负归属错误已纳 E02 |
| 七 | 无剩余 | 分对象完成/缺口/未知及下一证据需求均为 E02 全查；L181 仍以未完成链作已补全概括 |

程度补样：部分完成取 R:L180 CLI 七路径静态断裂；历史遗留取 L178 词表限定与 07-13 pending；无法判断取 L179 留存不足不外推现实。每个代码职责组另按 §4.4 取样：项目 CLI/testing、四 harness、五 validator、纯提示/Legacy/迁移技能、runtime schema/e2e，均回读源码/测试原文；不依文件存在或测试名称独断。

扩查结果：字段错误扩至两个批准 JSON 全字段和所有门断言；定位错误扩至 B-E001–050、六问与测试行号；测试类别错误扩查 design-tasks 全部函数中的输入修改和断言；信息来源错误扩至旧正文首中尾全文与 17 writing 相关检索/片段；数量错误扩查全树分层、runtime、schema、zip、技能测试分布、词表与全部修订表。本验收没有宣称其余未全文读取源码已获完整能力认证。

## 6. 前次修正要求逐项复验

| raccr2 项 | 本轮已成立修正 | 残留/新增问题与 verdict |
| --- | --- | --- |
| RF01 全读与覆盖 | 29 件名单可数，29/141/1274 闭合，根层补齐；不再掩盖未读 | 仍明确未达全文硬门；四 harness/82技能/构建器闭包未完成，定点不能替独有全文。FAIL |
| RF02 字段与三门 | event_seq 文件归属修正、三重算与三引用一致保持，e2e 第三节正名、作者绑定模块补充 | unresolved_items Pointer 仍错；导航仍挂语义门；第六节将同一引文错挂契约测试并叫作者门。FAIL |
| RF03 引用与词表 | 动机/读者章节、意图卡、L476 引文、显式词表与范围已改善 | proposal旧错误定位残留；migrator/测试/拒绝分支定位、空间简称等仍不准。FAIL |
| RF04 七控制与支持度 | 信息分层独立补齐，五类当前支持撤回，权限/开放/记忆收窄 | 感官操作数据“合规”错误；无同名→无工具化反面不成立；会议时长与动机认知不构成直接矛盾；七/八汇总混算。FAIL |
| RF05 历史/现实边界 | “未开工/零运行/唯一依据”已撤，词表不升级整体隔离，L125旧契约历史限定 | L47/57称谓未统一；多段无适用标签，存量/闭包概括仍过强。FAIL（已修的现实未知边界保留） |
| RF06 统计 | 219根分项12、v4日期、中文文件名非引号、28测试目录和原正确大数均复现 | CLI行数、修订表列数、七/八汇总及计划行数口径仍需修。FAIL（局部新问题） |
| RF07 ISSUE | 根因多处降推断、005a按内容迁移、005b线索、008政策已明示、009局部建议 | 004将局部有效反例泛化全部，008将未取得外推渠道缺位/根因，验证仍缺消费条件，009四栏错误。FAIL |
| RF08 执行记录 | 提交前文件门/提交后范围门时序正确；新候选远端/哈希/哨兵齐备 | 未得原始执行记录与实际模型/写入范围证明，保留 BLOCKED；不要求事后重放禁用测试 |

历史 F07/F08 的主要内容修正本轮重新核实：七路径失效点收窄和属性 unspecified 均保留，不简单继承旧 PASS；新出现的行号缺口另列 E01。历史报告不是冻结源码的新权威。

## 7. 启动摘要 M/S/A 覆盖对照

“摘要-”编号仅作用户指定主题映射，不替换 B 主表；PASS 限相应主题，不能抵销总 FAIL。

| 摘要 ID | 本次定位与证据 | verdict / 主表关联 |
| --- | --- | --- |
| M01 | §1–2 完整输入与两机械脚本 | PASS；B-M01/M02 |
| M02 | R:L66/L97/L139/L167 与全部引用，§4.2 | FAIL；B-E01/E02 |
| M03 | `ffb8c9a…` 远端、元数据、hash、新旧哨兵分开 | PASS；§2 |
| M04 | 无秘密/占位/第二业务提交；错误验证事实及执行记录缺口 | FAIL（内容），执行子门 BLOCKED；B-M03/X01 |
| S01 | R:L47/57/120/127，新主体/危机方向与批准 L147/L169/L382–419 | PASS（目标承诺）；实现比较错误另归 B-A02 |
| S02 | R:L48/58，目标一章、批准 L251–259/L608–615 | PASS（动机边界）；不据此免除 C02/E02 |
| S03 | R:L49/59，目标 L23–27、意图卡 L31 | PASS；读者与渠道未定 |
| S04 | R:L50/60/125，流程方向正确，但交接证据及历史称谓未完全统一 | FAIL；B-C02/A05/E02 |
| S05 | R:L51/61/82，80/70%限场景正确，导航不是语义门 | FAIL；B-A03/M03 |
| S06 | R:L52/66/175–184，现实未知正确，批准 Pointer 和门证据残留错误 | FAIL；B-A03/S01 |
| S07 | 九节与六问矩阵可定位，不套 A 拟人化形式 | PASS（适用格式）；汇总自洽/标签另判 |
| A01 | R:L120/127，批准与旧稿主体/关系对照 | PASS（收窄到主题/无当前对应） |
| A02 | R:L121，批准 L241/L289/L389 对旧正文 L245/L271 | FAIL；操作数据合规超出批准来源，B-A02 |
| A03 | R:L122，批准 L295–315/L468–475/L524–531 | PASS（承认旧稿无相同现实处置链） |
| A04 | R:L123–124，亲属无同名不能证明无工具化，信息分层已补 | FAIL；B-A02/E02 |
| A05 | R:L125–126，批准 L271/L283/L327/L510–517/L608–615 | PASS（关停/备份/开放边界） |
| A06 | R:L66–86，批准两 JSON、导航、重算 | FAIL；B-A03 |
| A07 | R:L94–114/175–179，历史状态、词表、候选态与现实未知 | PASS（版本/状态边界）；旧契约称谓另归 A05 |
| A08 | R:L131，最终契约 L26–44 | PASS；样片非权威，Markdown不代P1 |
| A09 | R:L49/59、目标未定范围 | PASS；无臆造市场画像、最终章数字数或现实科学结论 |

## 8. 修正指令（B §6.3／启动摘要 §6.4）

以下每条共同绑定：**候选完整 SHA `ffb8c9a10b51ae23000bc4e9fbd0a203dec120f1`；报告 SHA-256 `fe0dc30f0b16d1101edc1826079ef1e970334312dd463006798c540d05c71f13`；定义书完整 SHA `c423216ef9f8bbe8a9846b1a4d877d298a9334f7`；内容基线 `92573f1cca40f37cee04d2beb8708ff33ba603d6`。** 报告定位统一指 `outputs/duanxian-audit/implementation-review-report.md`。由编排方交实施者，本验收不直接发送给实施者。

### R3F01：完成实际阅读和职责覆盖，不以失败声明代交付

- 验收结论：FAIL；检查 ID：C01、C02、C03、A02。
- 报告定位：R:L14–37、L118、L147–163、L181，“硬门仍未满足”“四 harness…闭包”。
- 证据定位：B 定义书 §2.1 L58、§2.3–2.5、§5.2 L298–309；BASE 清单 1444；候选自报 141 定点＋1274 结构。
- 问题及影响：账目闭合不等于全文已读；未读独有文本、缺调用闭包阻止 C 消费完整审视结果。
- 修正动作：继续实际阅读余下独有内容；按层拆出全文、重复投影差异核对、二进制处理、未读及原因；为82技能明确成员/职责分类，为四 harness、五 validator、17 testing 及旧 run 补所需链。仍未完成则保留失败，不只换措辞。
- 不得改变：全量硬门、BASE、A目标、唯一报告、源文件及当前模型安排；不运行禁用测试/生成。
- 复验要求：新 SHA 两机械门；C01–C03、A02 与新增阅读影响的 E/A/I/S 断言，逐 run 覆盖也须重验。

### R3F02：修正批准 Pointer，彻底分离导航与语义门

- 验收结论：FAIL；检查 ID：M03、E01、E02、A03、T01、S01。
- 报告定位：R:L51/60/61/66/82/83/167/214/247。
- 证据定位：author-decision 顶层 `/unresolved_items` 与 `/approval_record/event_seq`，hash见§4.1；human-review-report.json `/review_path`；最终契约 L38/L64–79；契约测试 L108–142；e2e L112–125。
- 问题及影响：错误字段/引文和导航归类使门证据被夸大，且第三节与第六节互相冲突。
- 修正动作：空数组改准确 Pointer；导航移到人审呈现结构栏，语义门仅述所需独立报告/其未留存限度；撤去契约测试中的伪引文和作者门错误归属；作者绑定静态机制保留正确源码；明确作者决定可得、完整运行链不可得。
- 不得改变：approved/ready及conception范围、三个真实重算、P1权威、样片边界；不补造机器本体/日志。
- 复验要求：新 SHA 机械门；两批准 JSON 全字段，全部 hash/作者/机器/语义门断言与相邻总评全查。

### R3F03：逐条修正引用定位及测试正负分类

- 验收结论：FAIL；检查 ID：E01、E03、C03、T01。
- 报告定位：R:L43/97/123/139/143/149/156/167/203–256。
- 证据定位：§4.2 的完整路径纠错表；`engine/tests/test_validate_design_tasks.py:L46–58,L72–75,L138–143,L166–197`；line_sequence测试 L20–24。
- 问题及影响：读者按索引不能复现结论；把负例列正例会歪曲门禁覆盖。
- 修正动作：删除旧错误引用而非只追加正确范围；补足真正执行拒绝/路由的行；给所有简称完整映射及check-attr三路径；按输入修改、被调函数、断言结果重分所有五validator样本，不以函数名判别。
- 不得改变：源代码和原始行、固定候选范围；不得运行业务测试来掩盖静态引文错误。
- 复验要求：新 SHA 机械门；E01全文路径/Pointer/行定位全查；同模块测试分类扩查，至少保留一正一负的真实闭包。

### R3F04：撤销感官合规与零命中推断，保留有证差异

- 验收结论：FAIL；检查 ID：A01、A02、E02、C02、S01。
- 报告定位：R:L121/123/127/129。
- 证据定位：批准报告 L241/L289/L389；旧正文 L245/L271/L284–341；`duanxian/writing/characters/2026-06-07-writer-shenyu.md:L214`；亲属批准 L423–449；17写作对象范围见§4.3。
- 问题及影响：批准接口被误扩为操作数据，时间知觉与动机认知混淆；无同名不证明无语义反例。
- 修正动作：按文字/受限记忆边界逐处比较遥测来源，无明确授权输入证据则列旧稿差异或无法判断；保留会议来源未交代，撤回已证直接矛盾；亲属项仅述检索结果与语义覆盖限制；七控制与附加关系分表/分母；关系缺实现明确限定新版批准组合。
- 不得改变：当前批准故事、旧稿原文、人物判断与叙述事实区别；不创作传递链或用样片补设定。
- 复验要求：新 SHA 机械门；七控制、附加关系、所有无反例/合规/支持/矛盾断言全查，并扩查相关 writing 段。

### R3F05：统一历史、规范、静态事实和分级

- 验收结论：FAIL；检查 ID：A05、E02、S01、C02。
- 报告定位：R:L47/57/81/143–163/175–184。
- 证据定位：`duanxian/novel-goals.md:L93–97`；B §5.4；07-13 完整性报告 L32–34；四 harness 实际证据见§4.4。
- 问题及影响：就近标签缺失/混用，历史“新版”称谓不稳定，存量标题被总评升格为已补闭包。
- 修正动作：七月契约始终称历史过程契约；分句/分行标五口径；记录批准、静态核验、应然门和运行实况分开；旧HLD拆形式追踪/语义声明/作者/消费证据；按实际覆盖改总评，不夸称四链齐全。
- 不得改变：现实未知边界、既有批准、A未决读者/篇幅/开放项；不把缺记录反推未发生。
- 复验要求：新 SHA 机械门；全文完成、唯一、全部、合规、有效、未发生等强断言及相邻因果重审。

### R3F06：使新增统计与来源口径一致

- 验收结论：FAIL；检查 ID：C01、C03、E03、I01、S01。
- 报告定位：R:L31/32/129/135/163/199/252。
- 证据定位：CLI原文1081行；重构计划90逻辑行/89换行；17writing修订表L5均五列；七控制＋附加关系实际八条。
- 问题及影响：已修的大数正确，但新分母/表头/行数仍不能复现。计划末行计数差不作为伪造阅读证明。
- 修正动作：统一逻辑行/换行计数说明，修正CLI行数和修订表列数；七/八项分开汇总；技能职能分类列出成员/规则并保证互斥，不单用加总82。
- 不得改变：真实来源、已正确的1444/82/56/28/31/23/32/20446/219；不把测试存量变成绩。
- 复验要求：新 SHA 机械门；所有数量及分项按同一BASE、同一规则复算。

### R3F07：收窄 ISSUE 004/008，补可消费验证边界

- 验收结论：FAIL；检查 ID：I01、E01、E02、S01。
- 报告定位：R:L159/193/198/199及L184。
- 证据定位：`engine/scripts/validate_prd_contract.py:L17–23`、engine README L27、17writing LLD迁移；批准README L3、根.gitignore L11–18；最终契约 L17–24/L48–58/L85–91。
- 问题及影响：一个解析器不能证明全部旧引用有效；Git未留存不证明外部渠道不存在，不能把待取证根因升级为事实。
- 修正动作：IC004逐类列解析载体/基点/实目标，未核者保留待查，取消“全部有效/仅修(a)”推断；IC008改“本轮未取得获取/复验渠道与同版包”的取证建议，保留已有不入库政策，不替Owner改变政策；验证覆盖同版包、manifest、正式运行证据和消费条件，不以basename/hash两步宣称全部可用；IC009改五栏，保留建议级别。
- 不得改变：不修源码/配置/旧文档，不创建ISSUE，不直接向实施者发送指令；C负责归并与立项。
- 复验要求：新 SHA 机械门；十条IC的双证、应然、影响、版本、强度、根因、建议、验证、归并逐项重审。

### R3F08：补执行控制输入，不能事后伪造原始日志

- 验收结论：BLOCKED（执行证据子门）；检查 ID：X01、T01、M03。
- 报告定位：R:L184/L258–260，执行与模型安排自述。
- 证据定位：B §6.1 L471 要核作业记录；本报告§2仅证明Git可见范围及远端。当前控制输入只有本轮启动/初始化等，不含实施三轮原始记录。
- 问题及影响：无法独立确认实施忽略区写入、实际模型、禁用命令/联网、自检发生时序；未知不等于已发生越权。
- 修正动作：实施保留真实限制；编排方经控制渠道提供已有脱敏记录，验收者核对；不新增第二业务日志，不为补证重放禁用命令。
- 不得改变：既有候选与历史证据、秘密保护、当前明确模型重派、普通追加提交规则。
- 复验要求：新 SHA 文件/范围门、远端/哨兵，逐项核原始命令/退出码/时间、写入范围和实际模型后决定子门。
- 待提供输入：编排方提供 rint2、rint2r2、rint2r3 三轮受控脱敏记录及重派记录、提交前后自检/推送日志；只需记录路径，不要凭据。本次已请求，截至成稿未取得。

## 9. 交付范围与后续入口

交接所称 `engine/tests` 12 个、`novel-hld-lld-readiness-evaluator` 14 个既有失败仅作为编排提示；本轮未运行它们，未取得同命令/环境/输入绑定的原始成绩，不把数字写作本验收实测，也不把候选新增 Markdown 解释为源码新回归。候选正确保留这一边界。

本文唯一业务交付为 `outputs/duanxian-audit/racc-001-acceptance.md`，只提交/推送自身 `remote-agent/duanxian-audit-raccr3-001`。ACK、初始化与临时候选检查树是控制/核验材料，不入业务提交；候选检查树在交付前移除。报告自身按冻结标准核验UTF-8、至少4000字节、M01/S01/A01/verdict/修正指令关键词、秘密模式、空白及唯一新增范围；实际本报告提交号、hash和远端结果由最终交接给出，不在文内预写尚未发生的推送成功。

编排方应将 R3F01–R3F08 交实施修正与补证，在原实施唯一报告普通追加提交后重新封定完整SHA。新候选必须重跑机械/范围门并复查修正、相邻因果与扩查集合；当前窄项PASS不能迁移成新候选整体PASS。本结论只判审视报告，不改变小说构思批准，也不补发HLD、LLD或正文准入。
