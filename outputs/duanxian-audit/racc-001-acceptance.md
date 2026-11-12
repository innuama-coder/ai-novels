# 《断线》工作项 B 独立验收报告

作业：`duanxian-audit-racc-001`。验收日期：2026-11-12。**总 verdict：FAIL。** 判决仅针对下表封定候选，不针对最新 main，不否定小说既有构思批准。机械门通过不能抵销阅读覆盖、证据真实性和结论强度的失败；本候选不得按 PASS 交工作项 C。由编排方将本文修正指令交实施者，取得新候选后重验。

## 1. 封定输入、适用检查单与执行边界

| 对象 | 完整提交 SHA | 文件与实测 SHA-256 |
| --- | --- | --- |
| 内容基线 BASE | `92573f1cca40f37cee04d2beb8708ff33ba603d6` | 全部源文件以此 Git 树为准；不采用远端 main 的新内容 |
| B 定义书 | `c423216ef9f8bbe8a9846b1a4d877d298a9334f7` | `outputs/duanxian-audit/rdef-001-def.md`；`b0017ed4db8c46c0b368f01543659b93077a7b2aed94fb459137e40b4e107975` |
| A 定义书 | `99e18a0d2f3c8d4d8f069a3150622f8f68a55912` | `outputs/duanxian-audit/gdef-001-def.md`；`68ec7c0aabd98e2d4860bc0ce36e83f30b03ad2b84626fcc4c7bd9c9f7cde675` |
| Owner 已确认的目标总结 | `a6935ddcdf6716cf96bfdc6804e0cde29471bb5c` | `outputs/duanxian-audit/goals-summary.md`；`ac7f045a92af07c23b0b7a15a59421de25756f60883d4a3c9adc75b47e90155e` |
| 实施候选 | `00cc828650a2f1318d4eab0a994d5b68babbf799` | `outputs/duanxian-audit/implementation-review-report.md`；`25a93807ab8972c040cc325eb0dfb994d30985d5bbb7f41af0eabfd590153e19` |

实施来源为 `remote-agent/duanxian-audit-rint2-001`。启动交接明确本轮为 GLM-5.3 重派，并提供哨兵 `DXARINT-DONE-00cc828`；本验收接受本次明确交接，不把 B 定义书中旧 rint-001/kimi 分配机械当作此次未授权换模。无法从提交元数据独立证明实际模型或完整执行过程，限制见 X01。

编号差异已核明：封定 B 定义书 §6.2 实际为 M01–M03、C01–C03、E01–E03、A01–A05、T01、I01、S01、X01，修正模板在 §6.3；启动摘要写的 M01–M04、S01–S07、A01–A09 和 §6.4 对应 A 定义书的编号体系。本文以 B 原编号作主判决，同时在第 6 节补齐启动摘要要求的 M/S/A 对照，不遗漏任一实质主题，也不将 A 的六节拟人化格式套到 B 的九节报告。

两份定义书、A 总结和候选已全文读取。当前工作分支保持 `remote-agent/duanxian-audit-racc-001`。先读取本轮启动文件全文并逐项确认，再写 ACK `ack-c3bd7d677e63fa36`，之后才 fetch/取证。只读获取四条授权分支，按 SHA 读取对象。验收使用标准库、Git 和文本读取；没有导入业务模块，没有执行 pytest、仓库 validator、构建或小说生成流水线，没有安装依赖、修改来源或创建 ISSUE。

为原样复跑 B §6.1，临时在本作业目录创建 detached worktree `candidate-check-00cc828`，HEAD 固定为候选；只在其中运行两段标准库文件/范围检查，检查后正常移除。没有将实施分支 checkout 到验收主工作树。读取工作树源文件时，另逐字节比较 BASE 全部 1444 个跟踪文件，结果均与 Git 对象一致；字节比较是来源一致性检查，不冒充全文阅读或功能测试。

## 2. 机械、提交与远端检查

| 检查 | 实测结果 | verdict |
| --- | --- | --- |
| Git/Python | `git version 2.43.0`；`Python 3.12.3` | PASS |
| B §6.1 第一段原样脚本 | 退出 0；`FILE-PASS Chinese-count=6475 bytes=35291 sha256=25a93807ab8972c040cc325eb0dfb994d30985d5bbb7f41af0eabfd590153e19` | PASS |
| B §6.1 第二段原样脚本 | 退出 0；`SCOPE-PASS candidate=00cc828650a2f1318d4eab0a994d5b68babbf799` | PASS |
| 最终树与逐提交范围 | BASE 到候选只有一个普通单父提交；唯一差异为 `A outputs/duanxian-audit/implementation-review-report.md`；临时候选树无未提交文件 | PASS |
| 元数据 | author/committer 均为 `remote-agent <remote-agent@kunora.local>`；日期均为 `2026-11-12 19:30:16 +0800`；消息为 `docs(audit): add implementation review report (duanxian-audit-rint2-001)` | PASS |
| 远端 tip | `git ls-remote origin refs/heads/remote-agent/duanxian-audit-rint2-001` 返回完整候选 SHA | PASS |
| 哨兵绑定 | 编排交接的 `DXARINT-DONE-00cc828` 后缀与实测远端 tip 前七位一致；来源是编排补证，不虚构为本验收亲见实施终端 | PASS |
| 字节安全/占位 | 原样脚本验证 UTF-8、无 NUL、九节顺序、五标签、基线字符串和秘密/占位模式；人工读取候选、diff 与提交消息，未见实际凭据、伪造 GitHub ISSUE 链接或独立验收已通过声明 | PASS（内容真实性另判） |

脚本来自封定 B 定义书 §6.1 两个 `python3` 代码块，未改断言、字数算法或 HEAD 参数。复现文件树与统计使用 `git ls-tree -rz --name-only BASE`，按 NUL 分割；缺失文件按完整路径或精确 basename 匹配，不用 `git grep` 的内容命中冒充文件名清单。

## 3. B 定义书逐项判决

候选原文只有 39 行，多数章节全文位于单个长行。下文 `R:L7` 等均指候选原始行号，§2–§9 指其原二级节；本报告 F 编号是修正项编号。来源行号均为 BASE 原始文件，单行 JSON 使用 JSON Pointer，不使用美化输出的伪行号。

| ID | 候选位置/短引 | 核验方法与证据 | verdict |
| --- | --- | --- | --- |
| M01 | R:L3，BASE、B 定义及 A 两基准 | 四个对象哈希已重算并与交接比对，第 1 节完整绑定 | PASS |
| M02 | 九节全文与唯一新增 | 两段原样机械脚本、单提交历史、提交元数据及远端 tip，见第 2 节 | PASS |
| M03 | R:L15/L39“本地重算…五组”“本提交前…SCOPE-PASS” | 无秘密/占位，但“五组可直接重算”含未留存对象，不能视为可信验证记录；提交前范围检查的时序也缺原始日志，见 F02/F10 | FAIL |
| C01 | R:L7“非代表源码未逐字读毕”“13 份同构抽读” | B §2.1 L58、§2.4 L126/L128、§5.2 L298–309 要求全文与可对账覆盖；报告明确未满足，缺每层已读/未读数量 | FAIL |
| C02 | R:L11 六问连续段，L23/L27 五维 | 六问主题及九标题存在，但没有要求的六行矩阵；多问缺逐项实现路径、反证、程度/强度，见 F05 | FAIL |
| C03 | R:L27“17 件按职责分组”“82 个…约 12 个” | 有 CLI/驱动例子，却无 82 技能完整归类和每实现职责闭包、四 harness 成功/拒绝/退回链；未读与粗分类无法满足 B §2.3–2.5，另有数值错误 F06 | FAIL |
| E01 | R:L15 `.gitignore`；L35 省略路径；L39 B-E 索引 | 全文检查显式路径、目录相对项、运行引用和索引；一处实指路径不存在，多处键不能唯一落到完整路径/定位，见 F03 | FAIL |
| E02 | R:L11/L15/L19/L27/L31/L35 已完成、冲突、hash/权限、九候选 | 全查高风险断言及九条候选；保留真实路径缺陷，纠正 hash 重算、缺失即未发生、异常机制与属性生效断言，见第 4–5 节 | FAIL |
| E03 | R §2–§7 非 E02 结论 | 按出现顺序首/中/末抽查，并扩查同型计数、路径、投影与负向断言；Schema 数错误、属性规则不生效，见第 5 节 | FAIL |
| A01 | R:L11“其余…实现未发生”；L31“零运行” | A 总结第六节及 `duanxian/novel-goals.md:L49–51,L113–119` 只支持留存不足；候选却把它升级为现实未发生，F04 | FAIL |
| A02 | R:L11/L15/L23 七类故事控制、样片 | 当前主体、感官、亲属、关停和开放边界没有反向改写；但七类写作对照缺逐类双向路径，现实核验/权限对照过度集中于关停；正文与素材未全读，F01/F03/F09 | FAIL |
| A03 | R:L15 五组 hash、revision、缺失本体 | approved/ready 范围和 revision 037/038 先后解释基本正确；final-state/handoff 未留存却声称与跟踪文件相符，F02 | FAIL |
| A04 | R:L19 旧 HLD、superseded LLD、新版资格；L31 总评 | 历史门与 implementation-candidate 区分正确；“新版既未运行”超出证据，不能给本项整体 PASS，F04 | FAIL |
| A05 | 各节标签 | 标签出现满足机械门，但 R:L15 批准/hash事实、L27 静态机制、L31 分级未就近标注；R:L19 把设计规范标为当前权威故事口径，F05 | FAIL |
| T01 | R:L7/L27/L39“本轮未运行”及测试机制 | 未把 12/14 个既有失败冒充本轮新回归；但执行记录未交付、具体失败分支说错，不能据自述完成整个门，F07/F10 | FAIL |
| I01 | R:L35 B-IC001–009 | 全数核对。多条缺验证方向/完整路径/应然依据；IC005 混入无 frontmatter 不同问题；IC009 忽略已有历史隔离说明，F09 | FAIL |
| S01 | R:L31 分对象总评 | 没有总完成百分比，但“留存不足”与“零运行”并存，hash 与字节稳定策略有过强结论，总评须随 F02/F04/F08 重写 | FAIL |
| X01 | R:L39 未修改/未测试自述、候选历史 | Git 可见范围 PASS；未取得实施完整执行记录，无法核验忽略区写入、测试/联网及实际模型。未发现即不能证明从未发生，见 F10 | BLOCKED（执行记录子门） |

总判决为已确定内容违例的 FAIL；X01 的局部输入缺口另列，不以缺日志替代已经定位的失败，也不据缺日志指控实施者实际越权。

## 4. 全查证据：批准链、故事控制与全部 ISSUE 候选

### 4.1 批准与 hash：可复验、仅引用、不可取得分别登记

以下源 JSON 均只有原始一行：`duanxian/conception-approved/author-decision.json` 的 SHA-256 为 `4f5a070d22a92fb211b9e99709e04e05b16460aa52ae40c7ebb0eaf49249e2bd`；`duanxian/conception-approved/conception-completion.json` 为 `4eabd4af2b249493f3aae1a2668c4de9b37dea7f61628e1b454293e49587d127`。

| 候选短引/对象 | BASE 精确依据及本轮动作 | 结论 |
| --- | --- | --- |
| R:L15“html…等于跟踪 HTML” | author-decision `/human_review_package/html_sha256` 与 `duanxian/conception-approved/human-review-report.html` 实际 SHA-256 `80cfc4d82d77683324808ba3f96817914c24fd1de007fae70641789dedf65e36` 比对 | 支持；真实本体重算 |
| “author_decision 引用…等于…文件” | completion `/author_decision/sha256` 与上列作者决定原始字节重算 | 支持；真实本体重算 |
| “完成记录哈希…相符” | `duanxian/conception-approved/README.md:L22` 与上列 completion 原始字节重算 | 支持；真实本体重算 |
| “machine_package.manifest…等于…p1_manifest” | author-decision `/machine_package/manifest_sha256` 与 completion `/p1_manifest/sha256` 都为 `bba81d35a089320074eb8677911707052ba99b1265fbf19731c78785a1eef8ce` | 仅引用值一致，不是 P1 manifest 本体重算 |
| “终态哈希…development_handoff…与跟踪文件逐项相符” | README L18/L21 仅给 `state/revision-038.json` 和 `0679739ab8582227a25558164d56c9c4e608e8aeec96e5318252398a9babc942`；completion `/development_handoff` 仅给 `P1/development-handoff.json` 和 `d48194db32a43575c96ff2df0c9bccf0f8d95a98f2b7bc7bc601068078c33957`；全 BASE basename 清单两本体均无 | 不支持；R:L15/L39 的“五组留存文件重算”错误 |
| 九 stage 与其他绑定 | completion `/stage_completions/{B0,S1,W1,E1,T1,C1,Q1,P1,H1}`、`/run_state`（revision-037）、`/h1_html_manifest`、`/validation`；author-decision `/human_review_package/{completion_path,manifest_path}`、`/machine_package/{completion_path,manifest_path}` | 属运行相对引用；批准目录只留 6 文件；本轮未取得这些运行本体，不能复验其字节或链状态 |
| “人审约束合规”“三投影一致” | `duanxian/conception-approved/human-review-report.json` 的 `/review_path` 长度 5，187+113+89+175+23=587 秒；`/decision_controls` 8、`/visual_models` 5、`/fragments` 3、`/drilldown_index` 4602、`/reduction_ledger` 4602、`/source_coverage` 3924，均可静态核对 | 数量和预算支持；不是逐元素语义忠实、全链正式 validator 或所有独有字段对账的证明。最终交付契约 L64–79 明确数量/hash不能替代语义门 |

approved/ready 均限 conception，两个 `/run_id` 一致，`/approval_record/event_seq=1`、`/unresolved_items=[]` 属直接留存。revision-037 与 README 最终 revision-038 不因字面差异构成冲突；但没有状态本体就不能重放这次状态迁移。候选正确声明样片非权威和机器包缺失不推翻批准，这些正确边界应保留。

### 4.2 七类故事控制与写作对照

本表批准依据均为 `duanxian/conception-approved/human-review-report.md`，只用非样片正文。`duanxian/novel-goals.md:L79–89` 是七类控制的汇总入口。候选正确方向不等于其全文覆盖已经完成。

| 控制 | 候选原文位置→短引 | 批准依据与写作证据 | 验收判断 |
| --- | --- | --- | --- |
| 主体/记忆/关系 | R:L11/L23“R-07 不是顾衡复生”“同母题” | 批准 L147/L169、L382–419：顾衡已死，新主体及新感情；`duanxian/novel-text/2026-06-07-duanxian-novel.md:L464–476` 为旧稿“这是我的”，不能等同新批准角色全事实 | 当前口径无反向；旧稿仅支持主题同源，不能证明七类一致 |
| 当前感官 | R:L23“纯文字会话、无视听身体，一致” | 批准 L239–243、L277–289、L389；旧正文 L161/L183–199 是记忆回放，不应当作当前视觉 | 未发现候选借记忆增当前感官，但“写作层一致”缺全读和逐处依据，必须补证 |
| 权限与现实行动 | R:L23“无自行终止权限、关停由沈逾执行” | 批准 L271、L295–309、L396、L468–475、L524–531；旧正文 L409–441、`duanxian/writing/characters/2026-06-07-writer-R07.md:L67–91` 明示自主关闭 | 关停旧稿差异成立；不能用这一差异替代专家/硬件/授权链与现实阻断的逐项对照 |
| 亲属同意 | R:L11/L23“程予安…同意边界”“周岚不是情报筹码” | 批准 L423–449，妻子在世且无自动夫妻关系；旧稿对应主题缺失须给全文检索范围，不仅笼统“6 月无” | 当前边界正确；写作对照取证不足 |
| 信息分层 | R:L23“行动层/原因层制度分层” | 批准 L251–255、L303–315；旧正文 L201–205/L407/L417 的保留/释放是另一代信息机制 | 历史与现行区别方向合理；需分别说明救人、隐私及权限，不能把私密层直接当现行制度 |
| 关停/备份 | R:L15/L23“关停无活动备份” | 批准 L271/L283、L510–517、L608–615；旧稿自主关停见上 | 无复活保证或活动备份升级；保持沈逾执行与技术团队责任区别 |
| 开放边界/样片 | R:L15/L23“法律身份/连续性/互信”“非权威样片” | 批准 L325–329、L608–615；最终交付契约 `engine/harnesses/novel-conception-autonomous/docs/final-delivery-contract.md:L26–44` | 未发现以样片雨声等补新事实；正确保留开放项 |

### 4.3 九条 ISSUE 候选逐条核对

以下只评价报告是否给 C 提供合格问题证据；不创建 ISSUE，不代 C 定优先级，不修源码。

| 候选 | 双向核查与反证 | 本条 verdict / 修正 |
| --- | --- | --- |
| B-IC001 | `duanxian/conception-production/run.py:L14,L41–54,L58–99` 的 ROOT 已含 engine，S1/W1/E1/T1/C1 路径仍含 engine；全树存在正确路径、无双 engine 路径。扩查同文件 L123–135，Q1/P1 也同型 | 主要缺陷成立；范围应扩至同加载器入口，错误异常断言须修，F07；不得称本轮运行失败 |
| B-IC002 | `duanxian/conception-production/tests/test_attempt_selection_cli.py:L12–23` 及 `test_line_sequence_review_cli.py`、`test_topology_review_cli.py` 同型 ENTRYPOINT；parents[4] 超出仓库且拼旧 projects 布局 | 路径不自足成立；“fixture 的 spec 断言必失败”不成立，F07。补完整路径与具体验证方法 |
| B-IC003 | `README.md:L5` 与 `engine/README.md:L9` 写 81；BASE `engine/skills/` 一级目录 82，各有 SKILL.md | 计数漂移成立；仍须按 B §5.5 补应然依据、影响、验证与归并字段，F09 |
| B-IC004 | 全读索引中的旧根路径可确认存在失效例；17 份 writing 各 1 个反引号 LLD 路径，共 17 唯一项，替换为 `duanxian/design/specs/lld/` 后均可定位；如 R07 卡 L13 | 部分支持；“79 处”未给命令、分母、匹配清单与上下文。`engine/scripts/validate_hld_contract.py:L13–17` 的相似字符串是相对 engine 的有效路径，不能全树一律改链。F03/F09 |
| B-IC005 | `duanxian/writing/characters/2026-06-07-writer-R07.md:L14–16` 指 §10.x；`duanxian/design/specs/2026-06-06-hld-digital-life-novel.md:L312–337` 当前为 §9，L10 记 v4 重构 | 编号错位成立，根因只能标静态推断。无 frontmatter 与改号不是同一根因，且缺明确规范要求；拆分或降为线索，F09 |
| B-IC006 | `duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/artifacts/12-hld-integrity-report.md:L25,L32–34,L57–58` 留存 open；同目录 `final-hld-package.md:L20–22` fail/pending/blocked | 历史留存支持；“至今无处置”越过冻结来源，须限定 BASE 未见关闭证据并给检索范围，F04/F09 |
| B-IC007 | 上述完整性报告 L33 写 “v2.0 is newly presented”；该 run `manifest.md:L12–15` 定 v3.0 唯一源 | 确有标签混用；报告路径省略且缺验证步骤，补完整定位，不因此把 v2 重新当权威，F03/F09 |
| B-IC008 | 全 BASE 三机器 basename 均零匹配；根 `.gitignore:L11–18` 忽略运行账本；驱动 `duanxian/testing/run_duanxian_conception_v2.py:L27–35,L131–146` 读取迁移输入 | 留存缺口和依赖存在；引用忽略路径/Schema 数错误。留存政策与旧路径故障须分别说明，是否要求入库交 Owner，不能当已证违约，F02/F03/F06/F09 |
| B-IC009 | 旧稿自主关停相对新版差异成立；但 `duanxian/README.md:L22–23` 已明确历史链与批准优先，旧 proposal `duanxian/design/specs/2026-07-05-duanxian-proposal.md:L39,L276` 亦有非冻结说明 | “仓库…无历史口径声明”被反证；可改为写作目录局部提示增强建议，不能伪装现有全仓缺陷，F09 |

## 5. E01 路径与 E03 确定性抽样、同型扩查

### 5.1 引用可定位性

候选所有九节、B-E001/B-E004–013/B-E015–044 的实际引用以及 B-IC001–009 已逐项查看。编号缺 B-E002/003/014 本身不是失败；失败在于存在的键没有提供可独立解析的完整索引。R:L39 如“B-E012–B-E018 旧链五运行门禁”只给主题；它没有说明每个键对应哪条原路径、哪行/字段、哪项判断。验收者可以沿定义书重建一部分来源，但这不能替实施者补齐其交付物。

| 引用类 | 核对结果 |
| --- | --- |
| 实指完整文件/目录 | R:L7 的 `duanxian/`、`engine/`、`duanxian/design/specs/`、`duanxian/design/runs/`、`duanxian/testing/`；L15 的契约目录；L19 的校验器及纠正调度 manifest；L23 的 LLD 目录/风格参考；L27 的代码/测试目录、CLI、驱动；L35 的完整 CLI 路径均在 BASE 存在 |
| 确定错误路径 | R:L15 `duanxian/conception-approved/.gitignore` 不在 BASE；根 `.gitignore` 才包含相关规则。批准目录六文件没有该文件 |
| 明确作为缺失/历史/推导展示 | 三个机器 basename、`docs/superpowers/specs/lld/…`、`projects/duanxian/...`、`<repo>/engine/engine/...` 不应因不存在自动算引用造假；应保留其被查缺失的语境和实际迁移路径 |
| 可由上下文推断但索引不合格 | `workflow-docs/`、`design-tasks/`、`lld/characters|scenes|spaces/`、`tests/test_attempt_selection_cli.py:L12–13`、`writing/characters/*:L14–15`、`runs/hld/2026-07-13…/artifacts/...`，须规范成完整相对路径或严格定义唯一目录前缀/通配展开规则 |
| 运行相对路径/hash | P1/H1、state revision、compatibility-migrations 不能冒充仓库可读取文件；各引用本体可得性见 4.1 |

另核准 `engine/docs/superpowers/runs/design/2026-07-08-hld-lld-design-task-dispatch/manifest.md` 确实存在；不能因为旧 LLD 原文用 `docs/...` 就把候选给出的正确迁移路径误判为假路径。

### 5.2 抽样规则和样本账

为适应候选单行长段，按 §2–§7 章节正文中中文句号分隔并依出现顺序编号（带引号句号也分隔），各节片段数为 11、12、9、13、17、10。方法说明片段不作为实质结论；E02 已全查的批准/hash、完成总评、直接冲突、权限门及 ISSUE 相关片段先排除。对剩余结论按首、中、末取样，偶数取前中位。具体剩余集合及实际取样如下，明确分段只是可复现抽样索引，不以片段截断语义，核对时读取相邻完整句。

| 节 | E03 剩余结论片段（原顺序） | 首/中/末（不足三条全取） |
| --- | --- | --- |
| 二 | 6、8 | 6、8 |
| 三 | 8、10、11 | 8、10、11 |
| 四 | 4、6、7、9 | 4、6、9 |
| 五 | 1、5、9、10、11、12 | 1、9、12 |
| 六 | 1、2、3、7、9、11、12、14、15、16、17 | 1、11、17 |
| 七 | 1、3、6、8、9 | 1、6、9 |

| 样本 | 候选短引 | 完整源路径/定位与支持理由 | verdict |
| --- | --- | --- | --- |
| 二-6 | “目标读者未指定” | `duanxian/design/workflow-docs/duanxian-intent-card.md:L7–11,L31`；`duanxian/novel-goals.md:L25`；推断沟通对象未冒充作者决定 | PASS |
| 二-8 | “BASE 无新版运行留痕” | `duanxian/conception-approved/README.md:L3`；`.gitignore:L11–18`；全树 basename 查三机器对象为零 | 只支持留存不足，原句“各段无…留痕”范围过宽且未列检索规则，FAIL/F04 |
| 三-8 | “33 份 JSON Schema” | `engine/docs/ai-novel-workflow/contracts/autonomous-v2/` 全树清单：32 个 `.schema.json` + `contract-index.md`，总共 33 文件 | FAIL/F06 |
| 三-10 | “migrator 与…migration_handoff…B0” | `engine/skills/novel-interview-b0-migrator/SKILL.md:L3,L8–10,L23–30` 与 `engine/harnesses/novel-conception-autonomous/runtime/migration_handoff.py:L1–6` | 静态职责支持；本项目那次迁移执行详情仍不可复验 |
| 三-11 | “批准轮次…经环境变量切换…说明…多轮迭代” | `duanxian/testing/run_duanxian_conception_v2.py:L19–23` 仅支持默认值可被环境变量覆盖；作者决定 `/run_id` 支持批准 run 名 | 实际运行用了何入口、是否该变量、如何迭代不可由代码和命名推出，FAIL/F04 |
| 四-4 | “规则覆盖…全部通过…不能抵销绑定失败” | `duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/artifacts/12-hld-integrity-report.md:L32–57` | PASS，仅指该历史报告自述，不是本轮重跑 |
| 四-6 | “implementation-candidate…declaration-only…not-run” | `engine/harnesses/novel-hld-autonomous/manifest.yaml:L1–27,L44–48`；`engine/harnesses/novel-hld-autonomous/releases/0.1.0-acceptance.json` 的 `/status`、`/hld_e2e_fixture_status`、`/agentic_qualification`、`/bounded_agentic_case_count`；同目录 `0.1.0.md:L3–5` | 内容支持；应标历史发布记录/规范，不标故事当前权威；A05 仍 FAIL |
| 四-9 | “双向检索均为零” | 在 `duanxian/conception-approved/human-review-report.md/.json/.html` 逐个匹配原列七旧词，以及 `duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/canonical-world-facts-v3.0.md` 匹配程予安/许曼青/秦峥/梁策/伊利亚/德米特里，全部 0 | PASS（限所列词）；不能单独证明全部语义隔离 |
| 五-1 | “四代故事形态” | `duanxian/design/specs/2026-06-06-hld-digital-life-novel.md:L7–10`、`duanxian/design/specs/2026-07-05-duanxian-proposal.md:L11,L39`、`duanxian/design/workflow-docs/duanxian-intent-card.md:L7–10`、`duanxian/conception-approved/README.md:L3` | 可作为历史组织方式；属于分析归纳，应标推断 |
| 五-9 | “proposal…四段式…旧文档非冻结” | `duanxian/design/specs/2026-07-05-duanxian-proposal.md:L39,L45–46,L266–276` | PASS，仅限旧版本 |
| 五-12 | “6 月前序＝陆远” | `duanxian/writing/characters/2026-06-07-writer-qianxu.md:L1,L15` 对照批准报告“顾衡”L409–419 | PASS，命名演变不等于新旧人物事实逐条相同 |
| 六-1 | “五校验器与六测试…另 conftest” | `engine/scripts/validate_proposal_contract.py`、`validate_prd_contract.py`、`validate_hld_contract.py`、`validate_hld_release.py`、`validate_design_tasks.py` 均存在；`engine/tests/` 为五 `test_*.py` + `conftest.py` | 数量支持；conftest 是支持文件，勿称六个测试套件 |
| 六-11 | “schema 正/拒例…fixture…生产分离” | `engine/testing/test_conception_autonomous_v2_contracts.py:L108–142`；`engine/testing/test_conception_autonomous_v2_e2e.py:L119` | PASS，源码存在不等于执行通过 |
| 六-17 | “.zcode…仓库重构方案” | `.zcode/plans/plan-sess_316609e2-5263-4909-a27a-c47b17476339.md:L1–7,L18–50` | PASS，工程历史不是小说完成证据 |
| 七-1/6 | “6 月…历史遗留…不可晋升当前结构” | `duanxian/README.md:L16–23`；旧 proposal L39/L276；正文 `duanxian/novel-text/2026-06-07-duanxian-novel.md` 留存草稿 | PASS；该分类不能抵销全文阅读缺口 |
| 七-9 | “三个机器文件是否存在于未入库位置…不可判” | 全树精确 basename 零命中，批准目录 README L3 明示账本不入 Git | PASS；恰与同节“零运行”确定断言冲突，须统一到证据不足口径 |

**补样与扩查**：补齐“部分完成”R:L31 代码层、“历史遗留”旧 HLD 和“无法判断”机器本体；这些已在 E02/上表覆盖。按职责另核：CLI 加载器、17 项 testing 的驱动链、构思 runtime、访谈迁移、HLD 发布、通用交付 harness、纯提示/旧技能、五 validator 与运行时测试，结果如下。

- `duanxian/testing/run_duanxian_conception_v2.py:L43–55,L80–123,L131–146`：三段路径回退、W1/E1/T1/C1 构建器以及 Q1/P1 加载点成立，迁移输入不在 Git；只支持调用形状，不能证明八月运行实际走了它。
- `engine/harnesses/novel-conception-autonomous/runtime/production_orchestrator.py:L3466–3497` 与 `production_store.py:L617`：初始化确有锁、未初始化检查、revision-000、持久化、安装契约摘要；`author_decision.py:L80–88,L202–255` 有签封和当前状态/包绑定拒绝；`return_routing.py:L147–192,L195–214` 有 schema、确定性字段与 evidence 拒绝。支持静态机制，不证明全生产链实际成功。
- `engine/scripts/validate_hld_contract.py:L13–17` 的 ROOT/契约路径有效；`engine/tests/test_validate_hld_contract.py:L1185–1193` 正向测试确在，`test_harness_rejects_open_inventory_coverage` 亦存在。`engine/scripts/validate_hld_release.py:L192–210` 明确 root 解析。其余四组不能因同目录存在就取得能力 PASS；候选须补每组正/拒闭包。
- `engine/harnesses/kun-workshop-intranet-delivery/README.md:L11` 明确不自动创建云资源/读取生产数据；`engine/skills/novel-hld-writer/SKILL.md:L3–5` 明确历史非权威入口。分类方向支持，不把无 Python 文件当未实现。
- 扩查计数：82 技能、669 文件、56 个技能测试文件、21 个 novel-hld-* 目录和 31 zip 支持；31 zip 原始 SHA-256 分组支持六组 interview 1.0.0 双份相等、两组 autonomous codex/source 相等和各版本差异。未解包/执行。runtime 实际为 19 个 `.py`（含 189 行 `__init__.py`），总行数 20446；写“18 模块”须注明是否排除初始化模块，不能把 19 文件总行数混作 18 文件计数。
- 扩查字节稳定断言：根 `.gitattributes:L3–23` 的模式为 `harnesses/...`、`skills/...`，缺 `engine/` 前缀。`git check-attr --cached text eol -- engine/skills/novel-hld-finalizer/SKILL.md engine/harnesses/novel-hld-autonomous/manifest.yaml engine/skills/novel-development-baseline-preparer/SKILL.md` 六项属性均为 `unspecified`。R:L27“强制 LF”及 L31“字节稳定策略”不能作为已有效支持结论，FAIL/F08。

## 6. 启动摘要 M/S/A 编号补充对照

本节前缀 `摘要-` 区别于第 3 节 B 原编号。PASS 只表示该窄主题通过，不抵销 B 的 FAIL。

| ID | 核对主题与候选定位 | 判决及主表映射 |
| --- | --- | --- |
| 摘要-M01 | 输入与两段机械脚本 | PASS；B-M01/M02，第 1–2 节 |
| 摘要-M02 | 引用真实且支持结论 | FAIL；B-E01/E02，F02/F03/F04/F07/F08 |
| 摘要-M03 | 远端 tip、元数据、文件 hash、哨兵 | PASS；实测远端与编排哨兵绑定，第 2 节 |
| 摘要-M04 | 秘密/占位/伪造验证/额外业务范围 | FAIL；秘密与提交范围子检查通过，但 hash 验证叙述不真实、执行记录子门未闭合，B-M03/X01 |
| 摘要-S01 | 要写什么，R:L11 | 当前数字生命/新主体方向支持；B 的逐问实现矩阵未满足，整体 FAIL/F05 |
| 摘要-S02 | 为何写，R:L11 | 没有编作者私心；亲属/伦理方向正确；缺逐问程度/强度与直接证据，FAIL/F05 |
| 摘要-S03 | 为谁写，R:L11 | PASS；意图卡 L31、目标 L25，建议明确推断 |
| 摘要-S04 | 怎么写，R:L11/L15 | 流程/P1 权威边界正确；实际实现/运行推断过强，FAIL/F04/F05 |
| 摘要-S05 | 合格标准，R:L11 | 场景 80/70% 及三门限定正确，源 `engine/docs/ai-novel-workflow/development-phase.md:L137–152`；以缺记录推出“门未启用”不成立，FAIL/F04 |
| 摘要-S06 | 进度断点，R:L11/L19/L31 | FAIL；不能把未留存扩大为零运行、未发生 |
| 摘要-S07 | 清晰、无凑字；格式适用性 | B 九节机械 PASS；不要求 B 六节拟人化。R:L23 重复 subject-definition/causal-storyline/development-map/coverage-matrix/map-check，同一长段重复降低清晰度；随 F05 删除重复并分行 |
| 摘要-A01 | 主体/顾衡/关系 | 当前说法无相反设定；批准报告 L147/L169/L382–419 支持，主题 PASS；写作取证不足归 B-A02 |
| 摘要-A02 | 当前感官/记忆非录像 | 无新增当前感官；批准 L241/L277/L289/L389 支持，当前主题 PASS；旧稿全覆盖不可据抽读认定 |
| 摘要-A03 | 现实核验/授权/行动 | R:L23 七类表述未充分给现实团队对照证据；批准 L295–315/L468–475/L524–531；FAIL/F03/F09 |
| 摘要-A04 | 亲属/同意/分层信息 | R:L11/L23 当前边界方向正确；批准 L253/L315/L423–449；未把亲属当工具，主题 PASS |
| 摘要-A05 | 当前关停、无活动备份、开放 | R:L15/L23；批准 L271/L283/L327/L608–615；主题 PASS |
| 摘要-A06 | approved/ready 与复验范围 | FAIL；构思范围正确，五组 hash 说法错误，F02 |
| 摘要-A07 | 旧链/规范/正式完成分离 | 历史隔离基本正确；新版无留存被写成未运行，FAIL/F04 |
| 摘要-A08 | 样片与 P1 | PASS；R:L15 明确非权威，不把 Markdown 变机器入口，最终交付契约 L26–44 |
| 摘要-A09 | 读者/篇幅/现实科学 | PASS；未编市场画像、最终章节数或现实科学结论；R:L11/L31 保持读者与篇幅未决 |

## 7. 修正指令（按 B §6.3 / 启动摘要 §6.4 模板）

以下每条共用且绑定：**候选完整 SHA `00cc828650a2f1318d4eab0a994d5b68babbf799`；报告 SHA-256 `25a93807ab8972c040cc325eb0dfb994d30985d5bbb7f41af0eabfd590153e19`；B 定义书完整 SHA `c423216ef9f8bbe8a9846b1a4d877d298a9334f7`；内容基线 `92573f1cca40f37cee04d2beb8708ff33ba603d6`。** 下列“报告定位”均为唯一候选文件 `outputs/duanxian-audit/implementation-review-report.md`，不得修改其他源文件。

### F01：补足实际全文阅读和覆盖账

- 验收结论：FAIL；检查 ID：C01、C03、A02。
- 报告定位：§1 R:L7、§9 R:L39，“非代表源码未逐字读毕”“13 份同构抽读”“上述未读不影响任一裁定”。
- 证据定位：B 定义书 §2.1 L58、§2.3 L101/L113、§2.4 L126/L128、§5.2 L298–309；BASE 清单共 1444 文件，分组数已独立核实。
- 问题及影响：抽读不能替代冻结的全文阅读要求；相同表头不证明独有内容相同。未给每层完整/重复/二进制/未读数量，无法核对剩余范围；“不影响任一裁定”无证明。
- 修正动作：继续只读完成未覆盖独有文档/源码，按每层给总数、全文已读数、重复投影及核对方式、非文本数、未读数/原因，数量闭合。补 17 testing、82 技能、四 harness、五 validator 的归类和跨文件闭包；仍未完成则如实保留，不自称满足全量门。不得只把“抽读”文字改成“全读”。
- 不得改变：原全量阅读要求、BASE、唯一报告路径、源文件、Owner 本轮重派安排与 A 目标口径。
- 复验要求：新 SHA 文件/范围机械门；C01–C03、E01–E03、A02，重审所有受新阅读影响的结论。

### F02：分清真实重算与引用值一致

- 验收结论：FAIL；检查 ID：M03、E02、A03、S01。
- 报告定位：§3 R:L15、§7 R:L31、§9 R:L39，“五组绑定全部一致”“终态哈希…handoff…与跟踪文件逐项相符”。
- 证据定位：本文 4.1 中 author-decision、completion 的完整路径/Pointer 与哈希；批准 README L3/L18/L21–22；最终交付契约 L64–79。
- 问题及影响：三项实际文件重算、一个引用值比较与两个不可得本体被合称可直接重算；人审字段/数量也被扩大成“合规/三投影一致”，削弱实现程度判断可信性。
- 修正动作：用逐对象表替代“五组”；列三份可重算对象与完整 hash，单列 manifest 引用一致，终态/handoff/九阶段等均标仅引用且本体不可复验。把人审计数、结构/离线检查与逐元素语义验证分开；没有证据就收窄表述，同步总评。
- 不得改变：既有 approved/ready、conception 范围、P1 权威、H1/样片非权威；不得补造机器本体或推翻批准。
- 复验要求：新 SHA 机械门及全部 hash/作者门断言逐条重验，重审 M03/E02/A03/S01。

### F03：修正假路径并重建唯一证据索引

- 验收结论：FAIL；检查 ID：E01、E02、I01。
- 报告定位：R:L15 的 `.gitignore`；R:L35 省略路径；R:L39 的主题式 B-E 索引。
- 证据定位：BASE 根 `.gitignore:L11–18`；批准目录 6 文件清单；B 定义书 §5.4 L325、§6.2 E01。
- 问题及影响：不存在的文件被当作依据；B-E 分组名称和通配/省略号不能唯一回指具体来源。读者不得依赖验收者补全路径。
- 修正动作：改为真实根 `.gitignore`；给每个使用的 B-E 键明确完整路径、原始行/JSON Pointer、短引及适用版本；将运行路径、历史旧根和确实不存在对象明确标记。B-IC 的路径不得用省略号代替。附否定性搜索的规则和范围。
- 不得改变：不改原文件、引用内容和历史状态，不以最新 main 补证，不扩大可访问来源。
- 复验要求：新 SHA 机械门；E01 全量路径检查、E02 全部候选与冲突回读，不得只抽六条引用。

### F04：撤回由未留存推出未发生的断言

- 验收结论：FAIL；检查 ID：E02、E03、A01、A04、S01。
- 报告定位：R:L11“正文层仍未开工”“门未启用”“其余…实现未发生”；L19“新版 HLD 既未运行”；L31“零运行、零作者批准”；L15/L27 由驱动代码解释八月实际运行；L35 IC006“至今无处置”。
- 证据定位：`duanxian/README.md:L3,L16–23`；`duanxian/conception-approved/README.md:L3`；`duanxian/novel-goals.md:L49–51,L113–119`；A 总结第六节；驱动 L19–35/L43–55；旧完整性报告 L57。
- 问题及影响：存在旧正文且账本按设计不入库，“未见新版证据”不等于未开工/未运行；可配置 RUN_ID 和静态回退不能证明实际执行历史。候选自身未决项又承认本体可能在未入库位置，形成自相矛盾。
- 修正动作：逐项写明在 BASE 哪个清单/模式下未见何种证据、因此何事无法判断。对构思后阶段保留“未能复验正式准入”；把驱动解释改为有条件静态推断。对旧风险写“此冻结记录仍为 open”，不延伸到现实至今。
- 不得改变：不抹去旧正文，不宣称现实必然完成，不推翻既有批准，不请求外部运行服务补证。
- 复验要求：新 SHA 机械门；扩查全文所有“未运行/未开工/零/不存在/全部/已完成”及相邻因果，重审 A01/A04/S01。

### F05：补六问矩阵、逐事实口径与可读结构

- 验收结论：FAIL；检查 ID：C02、A05。
- 报告定位：R:L11 六问长段；R:L15/L27/L31 混合事实；R:L23 重复过程材料清单。
- 证据定位：B 定义书 §5.3 L313、§5.4 L325–349、§5.6 L361–375；A 目标六问及 `duanxian/novel-goals.md:L5`。
- 问题及影响：有六问名不等于六问实现对照完成；多个问缺程度/证据强度、反证和实现路径。全局标签出现不能覆盖未标或错标的事实段。
- 修正动作：保持九个固定二级节，第二节整理为六行目标/实现/正证/缺口/程度/强度矩阵；每个事实段或行贴适用五口径，静态代码影响标推断、规范标流程、历史发布标历史。删除 L23 重复列举，拆开长行，保证引用相邻可读。
- 不得改变：6000–12000 中文字硬门、A 未定读者/篇幅/开放项；不套用 A 六节拟人化版式替换 B 九节。
- 复验要求：新 SHA 机械门、C02/A05、摘要 S01–S07 全主题对照。

### F06：纠正统计与计数对象

- 验收结论：FAIL；检查 ID：C03、E03、S01。
- 报告定位：R:L15/L31/L35/L39“33 份 Schema”；L27 runtime “18 模块 20446 行”等统计。
- 证据定位：BASE `engine/docs/ai-novel-workflow/contracts/autonomous-v2/` 32 schema + 1 Markdown；`engine/harnesses/novel-conception-autonomous/runtime/` 19 `.py`（含 `__init__.py` 189 行），共 20446 行；测试目录含支持文件。
- 问题及影响：文件总数与 schema 数、模块范围与行数混用。数量不能替能力、阅读或测试成绩。
- 修正动作：修正全部“33 schema”为准确计数，说明 runtime 是否排除初始化模块并用同一分母；补命令/筛选规则。复查所有计数，不改正确的 1444、82、31 zip 等事实。
- 不得改变：不能改源目录以迎合统计，不把测试文件数说成测试通过数。
- 复验要求：新 SHA 机械门，按 BASE 重算目录/扩展名/行数与 hash 分组，E03/C03/S01。

### F07：保留路径缺陷，修正未经证明的异常分支

- 验收结论：FAIL；检查 ID：E02、T01、I01。
- 报告定位：R:L27“必然抛 cannot load stage runtime”“fixture 的 spec 断言必失败”；R:L35 IC001/002。
- 证据定位：CLI `duanxian/conception-production/run.py:L41–48`；测试 `duanxian/conception-production/tests/test_attempt_selection_cli.py:L19–23`，另两测试同型；CLI L123–135 为 Q1/P1 同型路径。
- 问题及影响：文件不存在不等于 `spec_from_file_location` 返回空 spec/loader。仅用标准库对不存在 `.py` 的 spec 构造观察，两者仍存在；没有执行模块。这证明候选具体断言不能由路径不存在推出，实际加载读取发生在后续 `exec_module`。静态路径缺陷与新实测失败必须分开。
- 修正动作：表述为正常冻结布局下目标源码缺失导致加载不可完成，指出后续加载位置；撤回不正确的固定异常/断言结论。扩查该加载器所有七条 runtime 路径，解释调用条件，不泛称每条 CLI 子命令都在入口失败；IC001/002 合并时保留两种路径成因和验证点。
- 不得改变：不运行项目 CLI/pytest，不修代码，不把静态分析写成测试成绩或新回归。
- 复验要求：新 SHA 机械门、E02/T01/I01；静态核对 ROOT、每条组合路径、标准库加载阶段及测试入口。

### F08：撤回当前已强制 LF 的结论

- 验收结论：FAIL；检查 ID：E02、E03、S01。
- 报告定位：R:L27/B-E038“.gitattributes…强制 LF”，L31“字节稳定策略”。
- 证据定位：根 `.gitattributes:L3–23`；本文 5.2 的三个真实路径 `git check-attr --cached text eol` 输出均 unspecified；源文件与 BASE 已逐字节比对。
- 问题及影响：模式保留旧根路径，不能覆盖当前 engine 路径。文件存在/规则意图不能证明规则在当前布局生效。
- 修正动作：写清规则文本意图与当前实际匹配差异，改总评；按报告问题候选规则判断是否与其他根路径迁移问题归并，给出准确验证命令。不要在本轮实际修 `.gitattributes`。
- 不得改变：BASE、源码、配置、提交边界；不把此前历史设计意图写成当前有效保证。
- 复验要求：新 SHA 机械门，E02/E03/S01，扩查所有宣称已生效的路径和规则。

### F09：重整全部 ISSUE 候选和故事证据对照

- 验收结论：FAIL；检查 ID：I01、E01、E02、A02。
- 报告定位：R:L35 九条候选；L23 七类故事对照。
- 证据定位：本文 4.2/4.3 的完整源路径与定位；B 定义书 §5.5 L357 规定每条字段；`duanxian/README.md:L22–23` 反证 IC009 全仓缺声明。
- 问题及影响：部分候选只有问题/建议，不能让 C 无猜测消费；79 处路径未列选择口径；IC005 混无 frontmatter 与编号错位；IC008 混留存政策与路径问题；IC009 忽略现存权威隔离声明。
- 修正动作：逐条补问题、应然/实际双证、影响、版本、强度、根因不确定性、建议、验证及归并。IC004 列出规则和有效反例，避免误改 engine 内有效相对引用；IC005 拆不同根因，未证明违约者降线索；IC008 明示政策待 Owner；IC009 改局部提示建议并承认已有全仓说明。七类故事每类补批准要求与写作片段双向证据，未对应处给范围，不让关停一例替代现实授权链。
- 不得改变：不预造 GitHub 编号、不提交 ISSUE、不直接通知实施者，不修既有文件；C 仍负责归并与提交。
- 复验要求：新 SHA 机械门，九候选全部重审，不抽样；连同全部故事高风险控制重验 E01/E02/A02/I01。

### F10：补充执行证据，校正自检时序

- 验收结论：BLOCKED（执行记录子门）；检查 ID：X01、T01，以及 M03 记录可信性。
- 报告定位：R:L39“§6.1 两段…本提交前…FILE-PASS/SCOPE-PASS”“本轮未运行…”。
- 证据定位：候选历史仅一个新增报告提交；B §6.1 第二段要求 BASE..HEAD 至少一个交付提交、报告已入 HEAD 且工作树干净；B §6.1 L471 要求核作业记录而非只看干净 Git。
- 问题及影响：本次独立机械复跑已通过，但不能证明实施自检真的在所述时点完成；缺日志也不能证明未测试/联网/写忽略区或实际模型。不得凭缺口反向断定存在越权。
- 修正动作：实施者只在报告中如实更正提交前/提交后的自检次序，给可核对的检查摘要；编排方以控制渠道提供已有执行记录，不在业务仓库新增第二份日志或报告。保留审计记录本身，不能事后补造原始输出。
- 不得改变：已证 Git 单文件范围、候选历史、源材料、秘密保护；不得为补日志重放禁用测试。
- 复验要求：新 SHA 文件/范围门与远端 tip/哨兵；逐项审查执行记录和模型重派授权，重验 X01/T01/M03。
- 待提供输入：由编排方提供 rint2 实施阶段相关命令/退出码/时间、源与忽略区写入范围、模型重派记录及交付自检记录；本次交接已提供哨兵，无需重新猜测其值。

## 8. 基线失败、交付限制与复验入口

启动摘要提到 `engine/tests` 12 个、`novel-hld-lld-readiness-evaluator` 14 个既有失败。本候选没有声称这两组是它引入的新回归，本验收也没有运行这些测试；本轮未取得与具体命令/环境/输入绑定的原始成绩，不能把该交接提示改写为本验收实测数字。候选相对 BASE 仅新增 Markdown，Git 中可见的源码不变；可定位的旧路径问题属于 BASE 静态问题，不以候选交付后发现就称“新增缺陷”。

本验收只做 B 规定的独立抽查与高风险全查，不替实施完成 1444 文件全文阅读。所有发现均有候选短引、BASE/定义书证据与可执行修正方向；无法证明的执行行为按输入缺口登记。F01/F02/F03/F04/F05/F06/F07/F08/F09 为已定位 FAIL，F10 为补证项；不以任何窄项 PASS 抵销总 FAIL。

下一步由编排方交实施者在同一唯一报告追加修正并普通提交、推送新 SHA。验收需重新封定新文件 hash，复跑 B §6.1 两段脚本、完整树/逐提交范围、远端及哨兵，再全审受影响结论、相邻因果和同型扩查集合。不得沿用旧候选 PASS，不得把本验收报告当小说 HLD/LLD 或正文批准。

本作业唯一业务交付物是本文；ACK/初始化控制文件不进入提交。验收报告自身的 UTF-8、至少 4000 字节、M01/S01/A01/verdict/修正指令关键词、秘密模式、diff 空白与唯一新增范围在提交前检查；实际提交号、报告 SHA-256 与远端核验结果由最终交接提供，避免在本文写入尚未产生的提交号或成功状态。
