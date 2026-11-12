# 《断线》工作项 B 独立复验报告

作业：`duanxian-audit-raccr2-001`；日期：2026-11-12。**总 verdict：FAIL。** 本结论只针对下列封定修正候选。候选机械门和 Git 可见范围通过，但全文阅读硬门仍未完成，且存在字段错引、历史权威升级和不受证据支持的一致性结论；不得以 PASS 交工作项 C。执行记录子门为 BLOCKED，不据缺日志指控实施者越权，也不以该缺口替代已经确定的内容失败。

## 1. 输入封定与验收方法

| 输入 | 完整提交 SHA | 文件 SHA-256 |
| --- | --- | --- |
| 内容基线 BASE | `92573f1cca40f37cee04d2beb8708ff33ba603d6` | 所有内容证据固定于此树 |
| B 定义书 `outputs/duanxian-audit/rdef-001-def.md` | `c423216ef9f8bbe8a9846b1a4d877d298a9334f7` | `b0017ed4db8c46c0b368f01543659b93077a7b2aed94fb459137e40b4e107975` |
| A 定义书 `outputs/duanxian-audit/gdef-001-def.md` | `99e18a0d2f3c8d4d8f069a3150622f8f68a55912` | `68ec7c0aabd98e2d4860bc0ce36e83f30b03ad2b84626fcc4c7bd9c9f7cde675` |
| 已确认目标 `outputs/duanxian-audit/goals-summary.md` | `a6935ddcdf6716cf96bfdc6804e0cde29471bb5c` | `ac7f045a92af07c23b0b7a15a59421de25756f60883d4a3c9adc75b47e90155e` |
| 前次验收 `outputs/duanxian-audit/racc-001-acceptance.md` | `d7fc94ac9fe4490c523bb112f6c4fb7a8115abe1` | `cd79394fe966cb109382f2e8b8f4ebe462de1c43a215b3b0649e4ed475faf3cb` |
| 本次候选 `outputs/duanxian-audit/implementation-review-report.md` | `b967b0736bc8065e08a4c2957d680225204f0c4b` | `5eb1a84a87e68ed6a64fe127a7f10bc7314ff1c125b3c4c7a194167782e2f24d` |

五份文件均按完整 SHA 从 Git 对象读取，重算结果与交接一致；两份定义书、目标总结、前次验收报告及本次候选全文已读。候选父提交实测为 `00cc828650a2f1318d4eab0a994d5b68babbf799`。本报告下文 `R:L数字` 均指本次候选原始行号（共 227 行），不沿用旧候选 39 行定位；来源行号为 BASE 原文，JSON 使用字段路径，不使用格式化后的伪行号。

检查单版本差异：封定 B 定义书 §6.2 的实际编号为 M01–M03、C01–C03、E01–E03、A01–A05、T01、I01、S01、X01，修正模板在 §6.3。启动摘要所称 M01–M04、S01–S07、A01–A09 及 §6.4 是 A 定义书编号。本报告以 B 的十八项为主判决，在第 7 节补齐摘要编号对照；不将 A 的拟人化六节格式或 2000–4000 字门套到 B 报告。

实施来源是 `remote-agent/duanxian-audit-rint2-001`，交接明确修正作业 `duanxian-audit-rint2r2-001` 为 GLM-5.3，接受该本次明确重派说明，不因 B 旧定义中的 kimi 分配直接判越权。模型实际运行和全部执行行为仍需控制记录佐证。旧哨兵 `DXARINT-DONE-00cc828` 只绑定父候选；新哨兵 `DXARINT-DONE-b967b07`、补步哨兵 `R2R2PUSH-DONE-b967b07` 均来自编排补证，非本验收亲见实施终端输出。

本次先全文读取启动文件、逐项确认，再写 ACK `ack-1aeb2735a90dbcb2`，之后才执行业务 fetch/取证。主工作树一直保持自身分支，从 BASE 开始。只读取得授权分支，以临时 detached 候选 worktree 原样复跑 B §6.1 两段标准库脚本，没有切换自身工作树到实施分支。另将主树全部 1444 个跟踪文件逐字节对照 BASE 对象，全部相等；这证明来源一致，不冒充 1444 文件全文阅读。

验收采用 Git、标准库和静态文本读取。没有导入仓库业务模块、运行 CLI/pytest/validator/build/小说生成、安装依赖、修改源文件、创建 ISSUE 或直接通知实施者。验收的取证抽查不替代实施的全量阅读义务。临时输入副本和候选检查树仅作取证，交付前清理，不进入业务提交。

## 2. 机械、提交、远端与统计复现

| 检查 | 本轮实际结果 | verdict |
| --- | --- | --- |
| 环境 | Git 2.43.0；Python 3.12.3；主机 `nodemach-002.kunora.ai` | PASS |
| B §6.1 文件脚本 | 原样提取首个 Python 块，在候选根运行，退出 0；`FILE-PASS Chinese-count=6359 bytes=42634 sha256=5eb1a84a87e68ed6a64fe127a7f10bc7314ff1c125b3c4c7a194167782e2f24d` | PASS |
| B §6.1 范围脚本 | 第二块原样运行，退出 0；`SCOPE-PASS candidate=b967b0736bc8065e08a4c2957d680225204f0c4b` | PASS |
| 历史范围 | BASE..候选共两次单父提交；首提交仅 A 报告，修正提交仅 M 报告；最终唯一差异为 `A outputs/duanxian-audit/implementation-review-report.md`；候选检查树干净 | PASS |
| 新提交元数据 | author/committer 均为 `remote-agent <remote-agent@kunora.local>`；日期均为 `2026-11-12 21:08:43 +0800`；消息 `docs(audit): fix review report per racc-001 F01-F10 (duanxian-audit-rint2r2-001)` | PASS |
| 远端 | `git ls-remote origin refs/heads/remote-agent/duanxian-audit-rint2-001` 返回完整新候选 SHA | PASS |
| 哨兵 | 两个新哨兵后缀与实测远端前七位 `b967b07` 一致；旧哨兵仅作父版本记录 | PASS |
| 字节及安全 | UTF-8、无 NUL、九节顺序、五口径标签、BASE、秘密/行首占位模式通过；候选全文、diff 和提交消息未见实际秘密或伪造已创建 ISSUE/独立验收通过声明 | PASS（不代表语义真实性通过） |

脚本执行只从封定 B 定义书 §6.1 提取两个 `python3` 块，未改字数算法、HEAD 参数或断言。下面是独立复算的统计，均限 BASE：

- `git ls-tree -rz --name-only BASE` 按 NUL 解码：1444＝根层 6＋duanxian 148＋engine 1290；engine 子层 83/669/404/5/6/10/112/1 与候选一致。
- `engine/docs/ai-novel-workflow/contracts/autonomous-v2/`：32 个 `.schema.json`＋1 个 `contract-index.md`。runtime 直接 `.py` 为 19 件，含 189 行 `__init__.py`，`splitlines()` 合计 20446；F06 的这两处旧错误已修。
- 技能一级目录 82，`novel-hld-*` 21；技能下 `test_*.py` 56，但只有 **28 个技能目录**含这类测试，不支持 R:L131“一技能一契约一测试”的全称归纳。纯提示技能没有测试不因此自动成为缺陷。
- 四 harness 文件/测试文件数分别为 interview 92/0、conception-autonomous 107/25、hld-autonomous 152/12、kun-workshop 53/0；31 zip 按原始字节 SHA-256 得 23 唯一值、8 个两份组，未执行或解包发行工具。
- 全 BASE 可解码文本逐行含字面串 `docs/superpowers`：79 文件、219 行；duanxian 31/88、engine 47/119、根层 1/**12**。R:L218 写根 11，分项和为 218，与总数不闭合。根文件为 `.zcode/plans/plan-sess_316609e2-5263-4909-a27a-c47b17476339.md`，命中 L5/7/29/30/31/42/43/44/48/49/62/64。字符串命中包含历史说明和有效 engine 相对路径，不是 219 个失效链接。
- 17 份 writing 各一个反引号 `docs/superpowers/specs/lld/…`，替换为 `duanxian/design/specs/lld/…` 后均真实存在。三个机器 basename 对全树精确匹配为零；revision-037/038 两个 basename 也为零。该结论只关 Git 留存。
- `HLD-断线设计稿.md` 的 NUL 文件名不含引号；R:L10/L95 把 Git 展示引号当作文件名属性，需更正，148 总数本身正确。

## 3. B 定义书十八项逐项判决

| ID | 候选位置与短引 | 检查方式、证据与判定理由 | verdict |
| --- | --- | --- | --- |
| M01 | R:L3–4 输入基线 | 五份指定对象与哈希封定、父 SHA 和 A 目标对照见 §1；没有改用最新 main | PASS |
| M02 | R 全文/提交 | 两段原样脚本、两提交逐项范围、远端与元数据，见 §2 | PASS |
| M03 | R:L43/53“语义门…review_path”及 L58 | 没有秘密/占位；但阅读导航被当作语义门留痕、completion 字段被错报，验证记录的内容真实性仍不合格，见 §4.1 | FAIL |
| C01 | R:L14–31“全量阅读门未满足” | B §2.1、§2.4、§5.2 要全文阅读；候选自己列 11 全文/158 定点/1275 结构，仍缺重复投影与非文本独立分类、未读数；L28 所谓 11 件清单只列 8 件 | FAIL |
| C02 | R:L37–54 六问矩阵 | 六行形式已修；但目标章节、主题证据和三门证据错位，否定性结论缺具体搜索规则；五维中信息分层对照仍缺，见 §4 | FAIL |
| C03 | R:L123–135“其余为结构级核对” | 17 文件归类和计数有改善，仍未完成 82 技能分类闭包、四 harness 成功/拒绝/退回链及五 validator 各正负路径；不能用同法核对代替证据 | FAIL |
| E01 | R:L174–223 B-E001–050 | 显式路径和上下文补全路径可定位，但 JSON Pointer、目标章号、多处行号错误；B-E045/050 未给精确检索表达式及词表，见 §4.2 | FAIL |
| E02 | R:L43/58/101–110/143–166 | 全审批准/hash/权限门、全部 ISSUE、已完成与直接冲突；三项重算修复，但旧契约升级、五类支持归纳和门证据混用仍失败 | FAIL |
| E03 | R 第二至七节 | 按 §5 的首/中/末规则取样并扩查全部同型字段、章号、计数和故事结论，出现不支持项，不以多数正确放行 | FAIL |
| A01 | R:L39–54、L106 | 与已确认 A 总结对照：目标主体/读者/篇幅大体保留，但把旧过程契约升级成新版必守依据，且留存不足仍夹“尚未开始”，改变了证据边界 | FAIL |
| A02 | R:L99–110 七类 | 回读全部高风险控制；列表用关系项替掉独立信息分层控制，未见反例被算作支持，漏掉会议室信息来源疑点，见 §4.3 | FAIL |
| A03 | R:L58–76 | approved/ready、三个实际 hash 与引用一致基本正确；但 `/event_seq`、`/unresolved_items` 错挂 completion，`/review_path` 不在该文件，三门推论不成立 | FAIL |
| A04 | R:L84–95/145–146 | pending、superseded、implementation-candidate 与现实未知已区分；仍有 v4 日期错误和关键词零命中升级为“隔离已核”，不能整项通过 | FAIL |
| A05 | R:L101/106/123–131/143–149 | 五标签机械存在；旧稿比较标当前权威、旧叙述契约标现行规范，多处事实/静态归纳未就近贴适用口径 | FAIL |
| T01 | R:L116/119/135/137/225–226 | 路径异常分支和 12/14 数字边界修复；忠实度 fixture 错称作者门，执行记录未取得；内容子项失败、执行子项阻塞 | FAIL |
| I01 | R:L157–166 全部候选 | 001/002/003/005a/006/007主要事实可证，005b/009降级正确；004统计及宽泛规则、008政策根因断言、若干字段仍待修，见 §4.4 | FAIL |
| S01 | R:L143–151 | 分对象、无总百分比正确；“隔离已核”“能力与存量在”等强结论不能由词表/数量/未全读支撑；随分节修正 | FAIL |
| X01 | R:L225–227、Git 历史 | Git 单文件范围 PASS；未取得实施两轮原始执行/忽略区写入/实际模型记录，不能仅凭自述闭合全过程门 | BLOCKED（执行记录子门） |

## 4. 高风险全查、引用核对与全部 ISSUE 复验

### 4.1 批准、hash、门禁与 JSON 字段

以下事实均独立读取 BASE 原字节。`duanxian/conception-approved/author-decision.json` SHA-256 为 `4f5a070d22a92fb211b9e99709e04e05b16460aa52ae40c7ebb0eaf49249e2bd`；`duanxian/conception-approved/conception-completion.json` 为 `4eabd4af2b249493f3aae1a2668c4de9b37dea7f61628e1b454293e49587d127`；`duanxian/conception-approved/human-review-report.html` 为 `80cfc4d82d77683324808ba3f96817914c24fd1de007fae70641789dedf65e36`。

| R 定位/短引 | BASE 证据及操作 | verdict |
| --- | --- | --- |
| L64–66 三个本地重算对象 | 上述三原文件 hash 分别对照 completion `/author_decision/sha256`、批准 README L22、author-decision `/human_review_package/html_sha256`，全部一致 | PASS |
| L67–69 三组引用一致 | author-decision `/machine_package/{manifest_sha256,completion_sha256}` 与 completion `/p1_manifest/sha256`、`/stage_completions/P1/sha256`；两 JSON H1 completion 引用也一致。只是引用比较 | PASS |
| L70–75 未留存与 revision | completion 九个 `/stage_completions/*/path`、`/run_state`、`/validation`、`/h1_html_manifest`、`/development_handoff` 和 author-decision 的包路径均为运行相对引用；批准目录仅 6 件，未取得运行本体。037 与 README 038 应作不同记录阶段，不能因序号不同直接判冲突，也不能声称实际重放迁移 | PASS（此限定） |
| L58 completion “/event_seq=1”“/unresolved_items=[]” | completion 顶层无两键；实际分别为 **author-decision `/approval_record/event_seq`** 和 **author-decision `/unresolved_items`**。两个对象 run 一致、approved/ready 限 conception 正确，不能抵销字段错引 | FAIL |
| L43、L182 B-E009 “/review_path 五项” | `/review_path` 位于 **human-review-report.json**，不在 completion。该字段各项 kind 为 world/storylines/characters/fragments/decision，问题与预计阅读秒数构成人审导航，不是独立语义审查 verdict | FAIL |
| L43/53“三门…均有记录” | `engine/harnesses/novel-conception-autonomous/docs/final-delivery-contract.md:L64–79` 规定 hash/结构不能单独证明语义，H1-A 需要独立逐元素 pass；未留存 `presentation-fidelity-review.json` 本体。现有 ready 引用不得改写为本轮已核三门执行证据 | FAIL |
| L76 人审计数 | human-review-report.json 对应数组长度为 8/5/3/4602/4602/3924；五项秒数 187+113+89+175+23=587；HTML 5 SVG、无 script。候选明确限结构/离线核对，方向正确 | PASS（结构，不是语义） |
| L135 “作者门不可由生产侧合成” | `engine/testing/test_conception_autonomous_v2_e2e.py:L112–125` 函数名 `_test_fidelity_review`，参数 P1/plan/fragment，注释的 this gate 指**忠实度评审 fixture**。不能将其改名为作者门证据。真正作者绑定可读 `engine/harnesses/novel-conception-autonomous/runtime/author_decision.py:L202–255` | FAIL |

### 4.2 E01 全量引用审核与同型扩查

逐行审核候选九节和 B-E001–050，程序提取的 35 个完整 ASCII 文件路径均在 BASE；另对“同 run”、同目录测试、runtime 模块、五 validator/测试等上下文引用补全并用 `git cat-file -e BASE:<path>` 核验。中文 HLD 文件、根隐藏文件、writing 17 件和目录/通配集合另按 NUL 清单展开。运行相对 P1/H1/state 路径和被分析的失效路径明确作为引用/缺失对象，不因其不在树就误判为假文件。旧错误 `conception-approved/.gitignore` 已改为根 `.gitignore`。本轮未发现新的虚构完整源文件路径，但**存在不等于定位与语义正确**：

| 候选定位 | 实际来源与需要改正的定位 |
| --- | --- |
| L40 “novel-goals 第二章：记忆、身份与照护责任”；L41 第三章读者；L42 第四章流程；L44 第六章进度 | `duanxian/novel-goals.md` 实际为一主题与目标、二编写方法、三边界、四约束、五成果设计、六验收标准。动机在 L9–21，读者 L23–27，流程 L29–51，状态分散于 L49–51/L71/L113及项目 README。候选把 A 总结六节顺序误套为目标文档章节；B-E001 索引不能修复正文错指 |
| L40 意图卡“动机段 L7–11” | `duanxian/design/workflow-docs/duanxian-intent-card.md:L7–11` 是版本/状态/批准人/日期/交接，实际动机在 L15–17 |
| L84 “2026-06-06…L10 记 v4.0” | `duanxian/design/specs/2026-06-06-hld-digital-life-novel.md:L10` 的 v4.0 日期是 **2026-06-07**，不能从文件名推修订日 |
| L87 proposal L39/L45–46 指 Agent pass、人审 pending | `duanxian/design/specs/2026-07-05-duanxian-proposal.md:L39` 非冻结材料、L45–46 四段式/三者关系；门禁应定位 §18（如 L265–267 的 pass/pending/blocked） |
| L101 “L474『这不是前序…』” | `duanxian/novel-text/2026-06-07-duanxian-novel.md:L474` 是引出句，真正引文 L476，另 L381 同句。属于局部定位误差，主题证据仍在 |
| B-E009 completion `/review_path`、L58 字段 | 文件真实，字段所属对象错误，详见 §4.1；必须逐字段重验而非只跑路径存在性 |
| B-E045/B-E050 | 前者没有明确是字面串、regex还是路径链接及分母，分项还少一行；后者没有列出 7 旧词和 6 新名。仅“全树 git grep”不能复现具体词表与语义隔离判断 |

“同 run”在 B-E019 后连续 B-E020–023 可唯一展开为 `duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/`，不再按旧 F03 一概判无法解析；但建议直接完整列出，避免跨段依赖。B-E027 writing 目录和 B-E031 runtime 目录均可按声明前缀展开，问题主要是覆盖证据不足，不是这些目录不存在。

### 4.3 故事七类控制、旧链与五种口径全查

下表“批准报告”仅为缩写，完整路径是 `duanxian/conception-approved/human-review-report.md`，非样片正文。当前目标还由 `duanxian/novel-goals.md:L79–89` 七行控制表、A 总结相应六节约束。写作侧全文读完旧正文 508 行，并定点扩查 17 份 writing 的感官、权限、私密信息、终止和旧名；没有把搜索等同 17 份全文阅读。

| 控制及候选短引 | 双向证据、反证与限度 | verdict |
| --- | --- | --- |
| 主体/记忆，R:L101 “判定：支持” | 批准报告 L277–289/L382–419：记忆主观、非录像、新主体；旧正文 L183–205 有像素采样/82%匹配，L381/L476 有“这是我的”。后者支持旧稿自我区分主题，前者须讨论其作为客观数据匹配的差异，不能整体写支持当前记忆机制，更不能给旧稿比较整行贴【当前权威口径】 | FAIL（过强归纳/漏反证） |
| 当前感官/信息来源，R:L102 “未见越权感官叙述” | 批准报告 L241/L289/L389 限文字/受限记忆；旧正文 L245/L271 写击键/施压力数据，**L335/L341 在 R-07 内部评估直接使用“会议室中的沉默时长——十秒”**，上文会议发生在室外且未给向 R-07 的文字传递。至少存在当前信息来源未交代的旧稿差异，不能不解释即全称未见。并非把所有人类 POV 的声音误判为机器感官 | FAIL |
| 权限与现实核验，R:L103 “未见…判定：支持” | 批准报告 L295–315/L468–475/L524–531 要专家、硬件、授权席、团队物理阻断；旧稿 L359–369 是遇袭轮廓与档案关联、L464–476 为读取记录，未展现相同气象武器处置链。没有直接机器行动不等于落实核验链；应列无对应实现/待迁移，而非正向支持 | FAIL |
| 亲属同意，R:L105 “未见反例” | 批准报告 L423–449 明示周岚/程予安主体性和同意。对旧正文＋17 writing 字面检索两名均零命中，只能支持“未找到同名对应”，不能证明所有亲属主题合格；旧稿 LLD 人物版本不同。候选该行保留未见反例比旧稿改善，但仍需具体对应/缺失依据 | 部分支持，完整门未通过 |
| 信息分层 | B 要七类中的独立信息控制；候选七条将第 4 条单列关系，漏掉行动层/原因层逐类对照。批准报告 L253/L315 与旧正文 **L407 私密保留→L417“访问权限：开放——无限制”** 应并列，解释对象、救人、亲属与访问阈值差异。不能让关停或关系项替代 | FAIL（缺项） |
| 关停/备份，R:L106 | 批准报告 L271/L283/L396/L510–517/L608–615 支持外部执行、无活动备份、静态保管不保证连续性；旧正文 L409–441、`duanxian/writing/characters/2026-06-07-writer-R07.md:L74,L91` 支持自主终止差异。差异本身成立；但 R:L106 将七月 `duanxian-narrative-contract.md:L26` 叫“新版契约”并要求新版写作照办，违反目标文档 L93–97 的历史/未绑定限制 | FAIL（权威升级，差异证据保留） |
| 开放边界，R:L107 | 批准报告 L327/L608–615 支持法律身份/重载/互信开放；旧正文 L480–508 留认知问题与空缺，不覆盖两国互信、重新授权等全部开放主题。只能写局部留白/无对应，不能据未封闭就计为实现支持 | FAIL（过强归纳） |

关系主题仍需核：批准报告 L147/L169/L396/L400/L411–419 明确顾衡已死、旧情未回应、R-07新感情；旧正文与 `writer-qianxu.md:L1,L15` 的前序是“灰鸟/陆远”，只能说明另一代素材。候选 R:L104 未见反向不构成已实现新关系。R:L110“五类获支持”据此不能成立。

样片非权威、未来无复活保证和读者/篇幅未定的方向保留，不推翻构思批准。旧叙述契约与批准内容在某些句子相合，也不能因此把整个过程契约提升为绑定 P1 的现行规范。R:L50“新版执行尚未开始或未见留痕”仍应删除“尚未开始”的实况选项；R:L52“三份记录满足交接要求”、L151“新版 HLD 人审门记录…唯一合规依据”都过度收束证据，需要机器基线、语义/消费门和作者门等完整链，见 HLD 规范 §2.5 及最终交付契约。

旧链核对：07-13 manifest L11–15、gate-report L14、final-hld-package L20–22 直接支持 pending/不得 LLD；旧 LLD manifest L3/17–18 为 superseded 错误记录；新版 HLD manifest `/status` 和发布 `0.1.0-acceptance.json` 为 implementation-candidate、not-run、declaration-only。这些修正均不应被撤销。R:L92/L145 用关键词零命中推出“旧链未渗入/隔离已核”仍不充分，须限词表检索结果，语义隔离另按逐事实检查。

### 4.4 ISSUE 候选全部复验

下列本地 B-IC 编号不是实际 GitHub ISSUE。十条记录（005 拆 a/b）逐条检查，没有创建 ISSUE。

| 候选/位置 | 双向核查与处理结论 |
| --- | --- |
| IC001 R:L157 | `duanxian/conception-production/run.py:L14,L41–55,L58–99,L123–135`：ROOT 已含 engine，七个传入路径又以 engine/ 起始；正确七文件都在 BASE，双 engine 七路径均不在。L47 才执行 loader；静态失效位置修正成立，**PASS 核心事实**。具体重构根因宜保留推断，不把静态核对称本轮实测失败 |
| IC002 R:L158 | 三件 `duanxian/conception-production/tests/test_{attempt_selection,line_sequence_review,topology_review}_cli.py:L12–13,L19–23` 都用 parents[4]＋projects 旧布局；spec 不一定空、exec_module 后续读取修正成立。**PASS 核心事实**。与 001 可作为迁移族，实际路径成因分别记录 |
| IC003 R:L159 | `README.md:L5`、`engine/README.md:L9` 的 81 与 BASE 82 比较成立。**PASS 核心事实**；“新增技能后未同步”未在冻结树证明历史因果，应改为推断或未知 |
| IC004 R:L160 | 17 writing 迁移路径可定位、有效 engine 相对路径反例成立；79/219 是文本命中不是全数坏链，根分项错误，`engine/` 根约定不能一概判定所有文档链接有效。需按实际解析基点分代码、Markdown、历史文本；“f7ac2db 一族”不是本报告已取证的历史根因。**FAIL 完整候选质量** |
| IC005a R:L161 | `writer-R07.md:L14–16` 引 §10.x，HLD L312–337 实际 §9，L10 是 06-07 v4；错位成立，根因已标静态推断，**PASS 核心事实**。迁移不能机械把所有 §10.x 数字减一：旧小节结构已改变，应按内容重新对照；补明确应然依据 |
| IC005b R:L162 | 未找到必须 frontmatter 的规范，作为待取证线索而非已证缺陷，**PASS 此降级处理** |
| IC006 R:L163 | `duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/artifacts/12-hld-integrity-report.md:L25,L32–34,L57` 与同 run final-hld-package L20–22 支持冻结 open；全树 HLD-TRACE-CLOSURE 仅上述两文件。修正不再称现实至今无处置，**PASS 核心事实**；补准入应然来源/验证落点 |
| IC007 R:L164 | 同完整性报告 L33 写 v2.0，而自身元数据 L8/L11 及 manifest L12–15 写 v3.0，标签混用成立；**PASS 核心事实**。不能以此推翻 v3 权威，或自动合并不同修复责任 |
| IC008 R:L165 | 机器本体未入 Git是真，政策“应有明示/根因入库政策未定”却受批准 README L3 明示不入库、根 `.gitignore:L11–18` 反证。可提出获取与重验渠道的政策建议，不可把缺本体等同政策未定；仅检索 basename 也不能验收完整 handoff 可消费性。**FAIL 表述/验证方向** |
| IC009 R:L166 | 承认 `duanxian/README.md:L22–23` 及 proposal L276 已有隔离说明，降为 writing 局部提示建议，**PASS 此修正方向**；“文件内无就地提示”须说明具体提示定义，不能否认 17 文件已有日期/版本/修订表 |

报告已补多数影响、版本、强度、建议、验证和归并字段，但不能由核心事实 PASS 推出整节 I01 PASS。IC004/008 仍有实质错误；005a/006/007 等还应明确对应的应然规则，归并只是 C 的建议而非已决定的 ISSUE 粒度。

## 5. E03 确定性样本与扩查记录

结论单位按候选表格行、编号条或一个可独立判定的事实子句划分，保留原始行号与顺序。先把所有已完成、冲突、ISSUE、权限/hash/作者门及故事高风险放入 E02 全查，剩余集合再取首、中、末（偶数取前中位），不足三条全取。重合事实在 E02 已核不重复计样本。具体剩余池及选择如下；不是以模糊的“抽查六条”替代规则。

| 节 | E02 之外的剩余结论单位，按原顺序 | 首/中/末及处理 |
| --- | --- | --- |
| 二 | L41 读者未定；L51 读者/渠道未定 | 两条全取；其余目标/三门/进度/完成和权威结论已在 §4 全查 |
| 三 | L76 人审结构计数 | 一条全取；其余均为批准/hash/完成门全查 |
| 四 | L84 v4 日期；L85 LLD 反斜杠旧路径；L95 engine 根约定及中文名说明 | 三条全取；历史准入、版本权威和隔离断言已全查 |
| 五 | 无剩余 | 七条控制、关系、样片、旧人名和汇总全部属于 E02 高风险全查，不以“无剩余”免检 |
| 六 | L123 runtime数量；L125 schema数量；L127五validator文件对应；L129 testing分类；L131技能数；L131一技能一测试；L131四harness数；L131zip；L135 Legacy；L135通用交付职责；L135重构计划 | 共11个，选第1/6/11，即 runtime、一技能一测试、重构计划；随后因计数/归纳错误扩查全部11个。权限门、路径断裂、运行史和发布批准已在 E02 核对 |
| 七 | 无剩余 | 七行分对象程度与 L151 下一证据需求均属于 E02 已完成/缺口及相邻因果全查 |

| 样本 | 候选短引 | BASE 完整路径/定位与支持理由 | verdict |
| --- | --- | --- | --- |
| 二首 | R:L41“目标读者未指定” | `duanxian/design/workflow-docs/duanxian-intent-card.md:L31`、`duanxian/novel-goals.md:L25` 支持；候选指第三章的定位错误另见 E01 | PASS（事实） |
| 二末 | R:L51“年龄层与渠道均无作者决定” | `duanxian/novel-goals.md:L25–27` 与 A 总结第三节，限定已读批准材料未给定位，不外推市场结论 | PASS（该边界） |
| 三唯一 | R:L76“属结构/离线核对” | `duanxian/conception-approved/human-review-report.json` 的上述七数组和五项 `/review_path/*/estimated_seconds`，HTML 原字节结构重算见 §4.1 | PASS（计数） |
| 四首 | R:L84“2026-06-06…v4.0” | `duanxian/design/specs/2026-06-06-hld-digital-life-novel.md:L10` 明记 2026-06-07 | FAIL |
| 四中 | R:L85“L36–39 反斜杠旧路径” | `duanxian/design/specs/2026-06-06-lld-digital-life-novel.md:L36–39` 确为 docs\\superpowers\\specs\\lld 历史文本路径，未冒充现行根 | PASS |
| 四末 | R:L95 engine根约定/带引号文件名 | `engine/README.md:L27` 支持 engine 内相对寻址；NUL 树中的 `duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/HLD-断线设计稿.md` 不含引号 | FAIL（文件名属性）；根约定事实 PASS |
| 六首 | R:L123“19件20446行” | `engine/harnesses/novel-conception-autonomous/runtime/` BASE 直接 py 清单与逐字节行数复算一致，未以行数证明能力 | PASS |
| 六中 | R:L131“一技能一契约一测试” | `engine/skills/` 82目录，仅28目录含56个test_*.py；例如 `engine/skills/novel-character-designer/` 仅 SKILL.md，L5–11 是提示式职责而非测试实现 | FAIL（全称归纳） |
| 六末 | R:L135“旧根布局为当时设计状态” | `.zcode/plans/plan-sess_316609e2-5263-4909-a27a-c47b17476339.md:L5–7,L29–49,L62–64` 描述整体平移与例外；支持工程历史，不证明所有路径已修 | PASS（限定历史） |

补齐程度类型：部分完成取 R:L147 CLI，与七条真实源码/双 engine 缺失核对；历史遗留取 R:L145 的旧 HLD pending，保留阶段但拒绝以词命中证明全部隔离；无法判断取 R:L146，BASE 三机器 basename 零匹配＋批准 README L3 不入库，只支持留存不足。均已在 §4 全查。

代码职责补样与交叉核对如下，全部为静态证据，不是执行成绩：

- 项目 CLI 与 testing：`duanxian/conception-production/run.py:L14,L41–135` 到七个真实 `engine/skills/<目录>/scripts/run_v2.py` 路径闭合/断裂；`duanxian/testing/run_duanxian_conception_v2.py:L16–55` 明确 ENGINE/NOVEL、可配置 RUN_ID、迁移旧根及三段回退。候选 F07 修正成立；未证明历史实际走哪入口。
- 构思 harness：`engine/harnesses/novel-conception-autonomous/runtime/production_orchestrator.py:L3466–3497` 初始化持锁、ensure_uninitialized、revision-000、持久化；`production_store.py:L617–628` 有非空残留拒绝；`author_decision.py:L80–88,L202–255` 签封、状态及 P1 绑定；`return_routing.py:L147–175` schema和确定性路由字段核对。候选支持部分机制，未完成所有职责闭包。
- 访谈 harness：`engine/harnesses/novel-conception-interview/README.md:L3–13` 定其拥有跨技能顺序、证据与批准门，不能以零 test_ 文件推为无门禁；`engine/skills/novel-interview-b0-migrator/SKILL.md:L23–30` 两条明确决定路径与 `engine/harnesses/novel-conception-autonomous/runtime/migration_handoff.py:L1–6` 不接纳 waiting_author 相互支撑。候选仅列数量不满足其完整成功/拒绝/退回链要求。
- HLD harness：`engine/harnesses/novel-hld-autonomous/manifest.yaml:L3,L14–27,L44–48`、`releases/0.1.0-acceptance.json` 的 status/agentic_qualification/hld_e2e_fixture_status、`releases/0.1.0.md:L3–5` 对照，支持候选态及42 bounded未由fresh Agents执行，不能算本轮新测。
- 通用交付 harness：`engine/harnesses/kun-workshop-intranet-delivery/README.md:L3–12` 为内网系统交付且云资源/生产数据/发布需授权，不是《断线》小说阶段完成凭证。纯提示/旧技能分别由 `engine/skills/novel-character-designer/SKILL.md:L5–11`、`engine/skills/novel-hld-writer/SKILL.md:L3–7` 区分，不以无脚本否定职责存在。
- 五 validator：`engine/scripts/validate_proposal_contract.py:L12–18`、`validate_prd_contract.py:L12–31`、`validate_design_tasks.py:L14–43`、`validate_hld_contract.py:L13–17`、`validate_hld_release.py:L192–212` 各有不同寻址/输入职责，不能从同目录推定全部相同。对应 `engine/tests/test_validate_hld_contract.py:L1185–1193,L1500–1520` 有正向检查与明确 raises 拒绝；L1418 是检查技能文本包含规则，**不是运行时拒绝执行证明**。`engine/tests/test_validate_hld_release.py:L80–95,L130–160` 是跟踪/校验和/快照/状态门测试，不能全部称作 root-not-cwd 的专项证明。其余三组“同法核对”未提供所需闭包，C03 仍失败。
- runtime testing：`engine/testing/test_conception_autonomous_v2_contracts.py:L108–142` 有 schema 文件/引用/路径正负规则；`engine/testing/test_conception_autonomous_v2_e2e.py:L112–125` 是忠实度 fixture，作者门错误命名已扩查至 §4.1。测试文件存在、预期拒绝和本轮通过三者始终分开。

扩查结果：发现字段错属后核对两份批准 JSON 全字段及人审导航；发现章号/日期错误后核对六问全部目标定位；发现支持过强后全查七类及缺失的信息分层；发现计数归纳错误后复算全部主要目录/测试/zip/旧根统计。未把未读取的其余源码判为已核能力；进一步全量阅读仍由实施完成。

## 6. 前次 F01–F10 复验对照

| 前次项 | 本次修正已成立部分 | 残留/新增问题与复验结论 |
| --- | --- | --- |
| F01 全文阅读 | 不再把抽读说全读，增加分层账 | 仍明确未满足；11清单只列8，缺非文本/重复/未读分母和全职责闭包。**FAIL**，诚实披露不豁免硬门 |
| F02 hash/门 | 三份真重算、引用一致、不可得本体已分层；不再说五组均可重算 | completion字段错挂，review_path错对象且当语义门。**FAIL**，旧错误部分修复但新证据归属错误仍影响三门结论 |
| F03 路径/索引 | 根.gitignore已正，B-E001–050大多可按上下文唯一解析 | 目标章号、意图卡行号、proposal门行号、JSON字段错；词表不完整。**FAIL** |
| F04 未留存不等于未发生 | 多数零运行/至今未处理已撤，现实进度未知保留 | R:L50仍“尚未开始或未见留痕”；L52/L151交接/准入结论过强。**FAIL** |
| F05 六问/口径 | 六行矩阵和九节分段完成，清晰度显著改善 | 六问引用错位，旧稿/旧契约标签及许多事实行口径仍不合格。**FAIL** |
| F06 统计 | 32schema＋1、19py/20446及zip等正确 | 根引用12写11、全称一技能一测试、v4修订日/文件名引号错误。**FAIL**（扩查新问题，不抹去已修部分） |
| F07 异常分支 | 撤销spec必空/固定RuntimeError，定位后续exec_module，扩到七路径；三测试成因保留 | **PASS（本条内容修正）**；未用此声称CLI或测试实际已运行，执行证据另归F10 |
| F08 属性生效 | 三路径text/eol六项unspecified本轮独立复现，撤销强制LF结论 | **PASS（本条内容修正）**；`.gitattributes` 未改 |
| F09 ISSUE/七控制 | 005拆分、009降建议、006限定冻结、008与路径问题分离，多数字段补齐 | 004统计和修复规则、008政策根因仍错；七控制漏信息分层，五类支持不成立。**FAIL** |
| F10 执行证据/时序 | R:L225正确区分文件门提交前、范围门提交后，不预写后者成功；新tip/哨兵可核 | 实施原始执行/写入/实际模型日志未随输入提供，候选L151也明列待提供。**BLOCKED（执行子门）**；时序文字修正 PASS |

前次不通过事项未被简单继承：本次按新 SHA 重跑机械门、逐条重读修正和相邻因果，确认 F07/F08 已修，其余按本轮证据判定。前次报告不是 BASE 故事证据，本报告没有以其旧结论代替原文件核查。

## 7. 启动摘要 M/S/A 编号覆盖对照

以下“摘要-”仅作主题对应，B 的九节/6000–12000中文及十八项仍是主判决。窄主题 PASS 不抵销整体 FAIL。

| 摘要 ID | 候选定位/证据 | verdict 与 B 映射 |
| --- | --- | --- |
| M01 | 输入与两段原样机械脚本，§1–2 | PASS；B-M01/M02 |
| M02 | R:L174–223及全文引用，§4.2 | FAIL；B-E01/E02 |
| M03 | 新完整tip、父SHA、author/committer、hash及新旧哨兵区分，§2 | PASS；远端封定证据齐全 |
| M04 | 无秘密/占位/第二业务文件；门记录含错属、执行日志未得 | FAIL（内容），执行子门BLOCKED；B-M03/X01 |
| S01 | R:L39/49/101，目标新主体和危机方向保留，旧稿支持范围过强 | FAIL（实现对照）；B-C02/A02 |
| S02 | R:L40/50，照护动机可由目标一章与批准角色支持，章号/行号错、进度过强 | FAIL；B-C02/E01/A01 |
| S03 | R:L41/51，读者未定、建议非事实 | PASS（目标边界）；章号错误归E01 |
| S04 | R:L42/52/106，流程链方向正确，旧契约升级与三记录满足交接不成立 | FAIL；B-A01/A05/E02 |
| S05 | R:L43/53，80/70%限场景正确；review_path不证明语义门 | FAIL；B-A03/M03 |
| S06 | R:L44/54/143–151，现实未知修正但字段/隔离/唯一准入证据过强 | FAIL；B-S01/A03/A04 |
| S07 | R九节与六行矩阵，分段可读，没有套用A六节拟人化 | PASS（B适用格式）；口径/来源另判，不要求B每段“这本小说” |
| A01 | R:L101/104，批准报告L147/L169/L382–419 | 当前新主体/新感情方向PASS；写作实现支持FAIL，B-A02 |
| A02 | R:L102，批准报告L241/L277/L289/L389与旧正文L335/L341 | FAIL（漏反证与信息来源）；B-A02/E02 |
| A03 | R:L103，批准报告L295–315/L468–475/L524–531 | FAIL（未实现相同授权链不能称支持）；B-A02 |
| A04 | R:L105，批准报告L253/L315/L423–449 | FAIL（亲属对应不足、独立信息分层缺项）；B-A02 |
| A05 | R:L106/107，批准报告L271/L283/L327/L510–517/L608–615 | 关停无备份当前方向PASS；旧契约升级、开放项实现过强FAIL；B-A02/A05 |
| A06 | R:L58–76，两个批准JSON及review_path | FAIL；B-A03/M03 |
| A07 | R:L84–95/106，旧链pending与候选发布状态正确，但旧叙述契约升级 | FAIL；B-A04/A05 |
| A08 | R:L73/111，最终交付契约§2–3，P1/H1/样片区分 | PASS（该权威边界） |
| A09 | R:L41/51、目标未决范围 | PASS（未编读者画像、最终篇幅或现实科学结论）；其他推断过强归E02 |

## 8. 修正指令（B §6.3／启动摘要 §6.4）

每条共用绑定：**候选完整 SHA `b967b0736bc8065e08a4c2957d680225204f0c4b`；报告 SHA-256 `5eb1a84a87e68ed6a64fe127a7f10bc7314ff1c125b3c4c7a194167782e2f24d`；定义书完整 SHA `c423216ef9f8bbe8a9846b1a4d877d298a9334f7`；内容基线 `92573f1cca40f37cee04d2beb8708ff33ba603d6`。** 报告定位均为唯一实施文件 `outputs/duanxian-audit/implementation-review-report.md`。这些指令由编排方交实施者，本验收不直接发送给实施者。

### RF01：完成全文阅读与可核对覆盖账（承接 F01）

- 验收结论：FAIL；检查 ID：C01、C03、C02、A02。
- 报告定位：R:L14–31，尤其“全文已读11”和“全量阅读门未满足”；L127–135 各职责清单。
- 证据定位：B 定义书 §2.1、§2.3–2.5、§5.2；BASE NUL清单1444。R:L28实际只列批准4＋目标＋项目README＋正文＋run.py＝8，未命名根层3件。
- 问题及影响：披露限制是必要诚实行为，但仍未交付冻结要求的全量阅读和闭包；结构/grep不能证明语义已读。
- 修正动作：继续实际阅读未覆盖独有文档/源码，逐层列总数、全文已读、重复投影核对、二进制处理、未读数及原因，账目互斥闭合；补齐82技能分类、四harness及五validator闭包。仍未读则保留失败，不得只改声明。
- 不得改变：BASE、全量阅读硬门、A目标、源文件、唯一输出及本次重派安排；不运行禁用测试/流水线。
- 复验要求：新SHA机械/范围门；C01–C03及所有由新增阅读影响的E/A/I/S结论重验，提供可核对阅读范围而非大段复制凑字。

### RF02：修正批准字段归属和三门证据（承接 F02/F03）

- 验收结论：FAIL；检查 ID：M03、E01、E02、A03、T01、S01。
- 报告定位：R:L43/53/58/76/135/182，“语义门review_path”“event_seq”“作者门不可…合成”。
- 证据定位：author-decision `/approval_record/event_seq`、`/unresolved_items`；completion无上述键及review_path；human-review-report.json `/review_path`；完整路径/hash见§4.1。最终交付契约L64–79；`engine/testing/test_conception_autonomous_v2_e2e.py:L112–125`。
- 问题及影响：把导航/结构记为语义门，把忠实度fixture记为作者门，错误提高了构思三门可复验程度。
- 修正动作：逐字段写清所属文件/Pointer；保留三个真实重算与引用一致；把导航和计数降回人审结构信息，语义门只写记录指向但本体不可复验；更正fixture职责，同步六问/总评/索引。用正确作者绑定模块说明静态机制，不能替代运行成绩。
- 不得改变：既有approved/ready及conception范围、P1权威、样片非权威；不补造机器本体或审查结果。
- 复验要求：新SHA机械门；两批准JSON全字段、所有hash/状态/作者/语义门断言和相邻推论重验。

### RF03：校准章节、行号与可复现引用（承接 F03/F05）

- 验收结论：FAIL；检查 ID：E01、C02、E03。
- 报告定位：R:L39–44/84/87/101及B-E001/009/015/016/045/050。
- 证据定位：目标文档六章标题及L15–27/L29–51；意图卡L15–17；proposal L265–267；HLD修订表L10；旧正文L476；完整路径见§4.2。
- 问题及影响：源文件存在但定位指向不同含义，下游不能按引用复核；没有词表的零命中不可复现。
- 修正动作：按实际目标文档章节重新映射六问；逐条核正文/索引行号和字段；为B-E045列原始匹配串、范围、分母与例外；为B-E050列完整7词/6名和三个批准文件路径，将结果限于关键词匹配，不推出全部语义隔离。
- 不得改变：原来源内容、历史版本、B九节和A目标；不得用最新main或外部来源补证。
- 复验要求：新SHA机械门；E01所有路径/上下文展开/Pointer/行定位全查，E03同类引用扩查；不能只抽六条文件存在性。

### RF04：恢复七类控制并收窄旧稿支持结论（承接 F09）

- 验收结论：FAIL；检查 ID：A02、E02、C02、I01、S01。
- 报告定位：R:L99–110“五类获写作层支持”“未见越权感官叙述”。
- 证据定位：批准报告L241/L253/L277/L289/L295–315/L389；旧正文L183–205/L245/L271/L335/L341/L407/L417/L409–441；writing-R07 L74/L88/L91；完整路径和对照见§4.3。
- 问题及影响：缺信息分层独立对照，用没有写到代替已经实现，漏当前信息来源及公开权限反证，夸大旧稿与新目标一致程度。
- 修正动作：按定义书七类逐行给批准依据、旧稿具体片段或明示无对应、正证/反证、历史归属、程度/强度；补信息分层；解释会议室数据从何而来，缺证列旧稿差异/迁移待办，不猜补设定；将五类支持改为可证的局部主题支持/无对应/无法判断，重审相邻总评和ISSUE线索。
- 不得改变：旧稿原文、当前批准故事边界、人物认知与叙述事实区别；不把历史差异宣布为当前生产回归，不创作新故事。
- 复验要求：新SHA机械门；七类与全部直接冲突、无反例断言全查，正文首中尾及17素材相关段扩查。

### RF05：撤销旧契约升级及无证实况推断（承接 F04/F05）

- 验收结论：FAIL；检查 ID：A01、A04、A05、E02、S01。
- 报告定位：R:L50/52/95/101/106/145/148/151，“尚未开始”“新版写作须按契约”“隔离已核”“唯一合规依据”。
- 证据定位：`duanxian/novel-goals.md:L93–97` 明示叙述契约是历史且未完成P1绑定；A总结第四/六节；批准README L3；HLD规范§2.5及最终交付契约§2–4。
- 问题及影响：历史与当前批准边界被模糊，留存不足又带入未开始可能性，关键词数量被提升为语义隔离/能力和准入结论。
- 修正动作：七月契约标历史来源，相同当前要求回引批准正文；删实况无证选项，只述BASE未见何证据；三记录不能概括满足完整交接，HLD进度需要分机器/语义/消费/作者证据；逐事实段贴五口径，未经全查的能力概括收窄。
- 不得改变：A已确认口径、构思批准、读者/篇幅/重载未决项；不从未留存推出无效，也不推出已完成。
- 复验要求：新SHA机械门；全文所有完成、未发生、全部、唯一、隔离、规范强制表述与相邻因果重审。

### RF06：修正计数分母、日期与展示字符（承接 F06）

- 验收结论：FAIL；检查 ID：C01、C03、E03、S01。
- 报告定位：R:L10/28/84/95/131/218。
- 证据定位：BASE NUL清单；82技能中28目录含56个test文件；根重构计划12个命中行；HLD修订表L10为06-07，见§2/§4.2。
- 问题及影响：总数正确不能抵销分项错误或全称归纳；展示引号不是实际文件名，文件名日期不是v4日期。
- 修正动作：列完整11已读对象或纠正数；根引用改12并使分项合219，定义统计口径；删除一技能一测试的全称，区分提示技能/测试存量；更正v4日期和中文名属性。保留已正确的32schema、19py/20446、82、31zip等。
- 不得改变：不通过修改源树迎合统计，不把测试文件数转为执行成绩。
- 复验要求：新SHA机械门；所有统计按同一BASE和明确规则重算，相关E03/C03/S01重验。

### RF07：完成ISSUE字段与政策证据边界（承接 F09）

- 验收结论：FAIL；检查 ID：I01、E01、E02。
- 报告定位：R:L159–166，尤其IC004与IC008。
- 证据定位：writing17旧LLD路径及engine README L27；`engine/scripts/validate_prd_contract.py:L16–22` 有迁移解析规则，不能按旧串直接判断失效；批准README L3与根.gitignore L11–18明确不入库；各候选双证见§4.4。
- 问题及影响：文本命中被混作坏链接，根因历史被无证定论，明确不入库政策被称未定；验证方案不足以证明hand-off可用。
- 修正动作：按解析基点、链接载体与实际目标逐类登记，区分历史说明与真失效；未证明的重构/新增因果标推断；IC008改成已知留存政策下获取/复验渠道的建议，不称已证政策未定；补应然规则与同版机器包/hash/消费复验方向。保留005b/009建议降级及006冻结状态限定。
- 不得改变：不修源码/配置/旧文档，不提交或预造ISSUE，不替Owner改变留存政策，不直接向实施者注入修正。
- 复验要求：新SHA机械门、全部十条记录及双证、影响、版本、强度、根因、建议、验证、归并逐项审核。

### RF08：补执行控制证据（承接 F10）

- 验收结论：BLOCKED（执行记录子门）；检查 ID：X01、T01、M03。
- 报告定位：R:L151/225–227，候选自身声明待提供记录。
- 证据定位：B §6.1 要核执行记录，不能把干净Git当作完整红线证明；本报告§2仅证明提交可见范围与远端交付。
- 问题及影响：时序文字已修，新tip/hash/哨兵可核，但原始命令/退出码/写入范围/实际模型证据未随交接提供；不知道不等于发现越权。
- 修正动作：实施报告保留真实自检次序及限制；编排方经控制渠道提供已有两轮记录，验收者核对。不得事后伪造原始日志或为补证运行禁用命令，不新增第二业务日志。
- 不得改变：已证Git单文件范围、源文件、秘密保护、普通追加提交要求；模型重派以本次明确授权为准。
- 复验要求：新SHA机械/范围门、远端及哨兵；逐项核执行记录、原始自检输出与模型安排，再决定X01/T01/M03执行子门。
- 待提供输入：编排方提供 rint2、rint2r2 的命令、退出码、时间、源码/忽略区写入范围、实际模型及重派记录、提交前后自检与推送日志；只需受控脱敏记录，不要凭据。本次验收已在会话请求文件路径，截至成稿未取得。

## 9. 基线失败、交付边界与后续入口

交接提示的 `engine/tests` 12 个、`novel-hld-lld-readiness-evaluator` 14 个既有失败，仅作为编排提示。没有与本轮命令、环境、输入绑定的原始成绩，本验收未运行这些测试，也未把它们算作候选新增回归。候选两次提交只涉及Markdown；源代码问题是BASE静态观察，不因本次发现而变成新回归。

总判决由已确定内容与覆盖失败决定，执行记录缺口另列。F07/F08的内容修正、三个真实hash、部分路径/统计/历史状态通过，不抵销RF01–RF07。编排方应将本文交实施修正，在同一报告普通追加提交并推送新完整SHA；新候选重新封定hash、复跑机械/范围门、审查修正断言和扩查集合，不能沿用本候选窄项PASS直接放行。

本验收唯一业务交付文件为 `outputs/duanxian-audit/racc-001-acceptance.md`，只提交/推送自身 `remote-agent/duanxian-audit-raccr2-001`。ACK/初始化等控制证据不入提交。本文不改变小说批准、HLD/LLD准入或写作状态，不创建ISSUE。报告自身按冻结标准检查UTF-8、至少4000字节、M01/S01/A01/verdict/修正指令关键词、秘密模式、空白错误及唯一新增范围；实际提交号、最终文件hash和远端核验结果由最终交接提供，不预填尚未产生的提交成功状态。
