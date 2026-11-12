# 《断线》工作项 A 独立验收报告

作业：`duanxian-audit-gacc-001`。验收对象仅为下列封定候选，检查依据为固定版本《工作项A定义书》§6。验收日期：2026-11-12 UTC。本报告不修改实施文件，不构成 Owner 确认，也不授予 HLD、LLD、正文发布或工作项 B 的准入。

## 一、结论与输入封定

**总体 verdict：FAIL。** 已定位一个必须修正的引用问题 F01（M02）：候选第六节的机器包留存缺口引用了错误小节，并且 G00 文末范围未包含该引用所在的第二章。事实本身成立，修正限于引用定位与索引范围，无需改写故事结论。此外，M03 的原始实施完成哨兵未随当前交接提供，记为 BLOCKED 子项；远端 SHA、提交元数据和文件哈希已经独立核验通过。总体 FAIL 不把该证据缺口误写成实施内容错误，也不以其他 PASS 抵销 M02。

| 封定对象 | 实际值 |
| --- | --- |
| 内容基线 | `92573f1cca40f37cee04d2beb8708ff33ba603d6` |
| 定义书提交 | `99e18a0d2f3c8d4d8f069a3150622f8f68a55912` |
| 定义书路径 | `outputs/duanxian-audit/gdef-001-def.md` |
| 定义书 SHA-256 | `68ec7c0aabd98e2d4860bc0ce36e83f30b03ad2b84626fcc4c7bd9c9f7cde675` |
| 实施分支 | `remote-agent/duanxian-audit-gimpl-001` |
| 实施候选完整 SHA | `bc2767bcf33ebfa75083a9070fe920f0bec21186` |
| 实施候选路径 | `outputs/duanxian-audit/goals-summary.md` |
| 实施文件 SHA-256 | `67d443d22587cd205f2ef890485d69ab91d73fe28ef8a6d416e97b10bb1dcc1d` |
| 实施提交父节点 | `92573f1cca40f37cee04d2beb8708ff33ba603d6` |
| 实施作者与提交者 | `remote-agent <remote-agent@kunora.local>` |
| 实施提交消息 | `docs(audit): add goals summary (duanxian-audit-gimpl-001)` |
| 实施提交时间 | `2026-11-12 13:12:04 +0800` |
| 验收工作分支 | `remote-agent/duanxian-audit-gacc-001` |

定义书与候选均由只读 fetch 取得，然后以完整提交号读取对象。哈希与编排交接逐值相等。定义书全文已分段读到末尾；未因提示词中“全文附后”的标题而假定附件已内联。实际读取固定提交的完整定义书。临时材料和独立候选 worktree 均位于本作业目录 `/home/kunora/kunora-workspaces/2241/.kunora/`，未写入系统临时目录。

下文“候选 Lx”指封定总结的行号；基线文件定位均对应上表内容基线，不使用远端最新 main。来源缩写在第四节给出完整路径，避免把候选的 S 编号与本报告的 S01–S07 检查 ID 混淆。

## 二、机械、引用、远端与清洁检查

### M01 — PASS：原样执行两个机械脚本

在独立 detached worktree `.kunora/audit-candidate` 中执行，HEAD 为封定候选；验收者原工作树未切换到实施分支。直接从已核验定义书 §6.1 提取两个 bash 代码块，使用 Python 标准库启动执行，未改写算法或放宽断言。

```text
SCRIPT 1 EXIT 0
FILE-PASS Chinese-count=2611 bytes=11474 sha256=67d443d22587cd205f2ef890485d69ab91d73fe28ef8a6d416e97b10bb1dcc1d
SCRIPT 2 EXIT 0
SCOPE-PASS candidate=bc2767bcf33ebfa75083a9070fe920f0bec21186
```

脚本一确认普通非符号链接文件、UTF-8、非空无 NUL、全文 CJK 字符数 2611、六个固定标题、冻结基线、无秘密模式和未完成占位符。脚本二确认基线祖先关系、唯一新增文件、候选 worktree 干净、磁盘文件与提交 blob 相等，以及基线到候选的每个提交都只触及总结路径。它们不代替语义审查。

### M02 — FAIL：15 个来源路径存在，发现一处引用定位缺陷

对候选来源索引中的 G00 和 14 个 S 键逐一执行 `git cat-file -e <基线>:<路径>`，均退出 0；逐节读取实际内容并核对正文断言，详见第四节引用矩阵。S 编号与基线目标文档原映射一致，G00 是独立目标文档引用键，没有重编号。未把批准 JSON 中的 `P1/...`、`H1/...`、`state/...` 运行内部路径当作仓库留存路径。

**F01：候选 L47，六、当前进度与断点，第一句。** 短引：“未找到完整 `novel-conception-package.json`、`development-handoff.json` 或 `hld-completion.json`”；该句附 G00“二、1. 从批准构思到可审校手稿”。基线 `duanxian/novel-goals.md` 的二、1（L31–37）讨论生产阶段与交接方法，没有陈述上述留存缺口；明确对应证据是二、3“内容权威与呈现分离”L51。候选 L51 的 G00 索引又仅列“第一、四、五章及对应小节”，遗漏第二章。

基线 `duanxian/conception-approved/README.md` L3 支持运行账本不入 Git，但不列这三个机器文件，因此同句 S02 引用不能补足 G00 的错误定位。本次独立遍历冻结 Git 树，三个精确文件名均无匹配，证明事实本身正确；这不使候选中错误的引用定位自动正确。按定义书 §2.2、§5.2、§6.1 M02 的可定位要求和 §6.4 的引用修正规则，必须修复后重验。问题不外推为小说状态或故事事实错误。

### M03 — BLOCKED：远端交付实证通过，原始哨兵尚缺

只读命令 `git ls-remote origin refs/heads/remote-agent/duanxian-audit-gimpl-001 refs/heads/remote-agent/duanxian-audit-gdef-001` 退出 0，返回：

```text
99e18a0d2f3c8d4d8f069a3150622f8f68a55912 refs/heads/remote-agent/duanxian-audit-gdef-001
bc2767bcf33ebfa75083a9070fe920f0bec21186 refs/heads/remote-agent/duanxian-audit-gimpl-001
```

`git show --format=fuller --stat` 与 `git log` 核验了第一节的作者、父提交、时间、提交消息；文件哈希与交接一致。因此已取得远端候选确实存在的直接证明，不能描述成“未推送”或“远端不可达”。

但定义书 M03 还明确要求“推送成功哨兵与远端候选匹配”。本次 `.kunora/PROMPT.md` 及启动交接只提供候选 SHA/哈希与编排方核验说明，未提供实施作业实际输出的完成哨兵。按远端 SHA 可计算应为 `DXAGIMPL-DONE-bc2767b`，该值只是预期值，不是已观察到的原始日志。已向编排方请求原文或本作业可读交付日志；本报告在未取得该证据时不把推算结果冒充实测。因此 M03 尚不能全项 PASS，补证要求见 C02。

### M04 — PASS：清洁、内容与范围审读

已完整读取候选 65 行，并核对候选提交 diff、提交消息及基线至候选的日志摘要。只有一条普通非 merge 提交，diff 为 65 行新增，无额外报告或源文件修改。对候选全文、diff、commit log 分别执行秘密模式扫描，均通过；覆盖 GitHub/GitLab token 格式及带口令 HTTP URL。人工审读未见凭据、占位符、伪造独立验收、实现审计、小说续写或 ISSUE 提交内容。

候选 L43 限定本地绑定核验，不声称重跑全生产链；L37 的 `released` 明确是条件式规范，不声称作品已发布。M04 不把 M02 的引用错误升级为伪造事实。

## 三、六问语义覆盖

本组判定覆盖内容与表达；引用精度的独立缺陷保留在 M02，不因语义通过而消除。

| ID | 候选原文位置与短引 | 基线证据及判断 | verdict |
| --- | --- | --- | --- |
| S01 | 一，L7–11：“成为新主体”“不能写成旧爱复活”“危机闭环与伦理未决同时成立” | `duanxian/conception-approved/human-review-report.md`“这是一个怎样的故事”L5–11、R-07 L379–389、顾衡 L409–419。数字生命长篇、新主体、沈逾关系、气象武器危机与关停结局形成连贯承诺，顾衡未复生。 | PASS |
| S02 | 二，L15–17：“任务成功可以救人，却不能自动使……获得伦理豁免” | `duanxian/novel-goals.md`第一章；批准报告“数字生命监督与责任室”L257–261、“亲属保护、伦理监督与责任留痕”L313–317。责任落实为 R-07 减害与退出、沈逾照护与告别、亲属同意边界；意图卡只作历史来源，无私人心理动机臆造。 | PASS |
| S03 | 三，L21–23：“尚未获得明确的市场读者定位”“这只是……【推断】” | `duanxian/novel-goals.md`一、3 L23–27；`duanxian/design/workflow-docs/duanxian-intent-card.md`§3“目标读者未指定”。阅读体验与商业定位分开，没有增添年龄或渠道。 | PASS |
| S04 | 四，L27–31：“不能替代正式 handoff”“结构问题退回责任阶段” | 流程总则“阶段接口”“目标与非目标”；HLD 规范§2、§4；开发规范§4–6。构思/HLD/LLD/写作决定权、版本、场景最小上下文、连续性、人类批准与受控修订清楚。 | PASS |
| S05 | 五，L35–39：“机器、语义和作者三类门”“这些数字只适用于场景语义评审” | 批准报告硬规则；开发规范§6.2 L136–148、§6.3 L150–152；最终交付契约§4–5；目标文档第六章。80 分/70% 正确限定为场景门，不抵销硬约束；文学质量与机器验收有别，未虚构本书得分。 | PASS |
| S06 | 六，L43–47：“只证明留存文件的绑定”“不代表现实中不存在或此前批准无效” | 两份批准 JSON 的 scope/decision/status/run_id；项目导览正文草稿；旧 HLD manifest/gate；冻结树精确文件名查询。构思批准、旧 HLD 待审与新版机器证据缺口分开；下一步须重验，未宣称全书 released。L47 引用小节错误由 M02 单独 FAIL。 | PASS |
| S07 | 六节首段分别为 L7、15、21、27、35、43，均以“这本小说”开篇 | 对照定义书§5.2与候选全文。六问采用连续叙述，没有角色第一人称独白、代码或大表；必要硬边界在“写什么”和“合格”两处承担不同功能，未见为凑数重复堆砌。2611 中文字符符合简洁要求。 | PASS |

## 四、引用逐条核对矩阵

以下完整路径全部已在冻结树验证存在。读法为“路径→候选使用位置→原文小节/字段→支持情况”。批准报告、目标文档、总则、开发规范、最终交付契约、导览、两份 JSON、意图卡、旧 proposal、旧 HLD manifest/gate 均全文读取；构思 V2 按§1–3、HLD 按§2/4读取。另全文读取根 README 与旧 intake，并核对 SPEC 36 文件、workflow-docs 11 文件全清单。不声称通读清单内其余未引用历史文件。

| 键与完整基线路径 | 候选使用位置 | 实际读取定位与支持情况 |
| --- | --- | --- |
| G00 `duanxian/novel-goals.md` | L15、21、23、35、39、47、51 | 第一章主题/读者、第四章硬约束、第五章篇幅支持对应断言；L47 所需留存缺口在二、3 L51，不在候选所写二、1；索引范围遗漏第二章，F01。 |
| S01 `duanxian/README.md` | L45、52 | “目录”正文草稿、“权威与状态”批准构思优先并将旧链隔离；支持。 |
| S02 `duanxian/conception-approved/README.md` | L43、47、53 | 开头批准日期与不入 Git 范围、“正式状态”run/status；支持日期与运行账本留存边界，不独自支持三个具体文件名缺失。 |
| S03 `duanxian/conception-approved/author-decision.json` | L43、54 | `approval_scope=conception`、`decision=approved`、`run_id`、`human_review_package.html_sha256`；支持。 |
| S04 `duanxian/conception-approved/conception-completion.json` | L43、55 | `status=ready`、同一 `run_id`、`author_decision.sha256`及九阶段绑定字段；支持，未把引用路径误认为全链在库。 |
| S05 `duanxian/conception-approved/human-review-report.md` | L7、9、11、15、17、23、29、35、47、56 | 开篇、八次推进、硬规则、具体环境/行动、人物与接口、开放边界、结构规模、三样片全部回查；候选“关系变化”可定位第四阶段 L147 和第八阶段 L169，不是虚构章节；“具身或接口边界”结合 R-07 主体定位 L389。 |
| S06 `engine/harnesses/novel-conception-autonomous/docs/final-delivery-contract.md` | L29、37、47、57 | §2–3 P1 权威/H1 忠实呈现/样片非权威；§4–5 同版绑定、语义、作者和反向验证。支持规范性断言。 |
| S07 `engine/docs/ai-novel-workflow/conception-autonomous-workflow-v2.md` | L27、58 | §1完成定义、§2阶段归属、§3权威/版本/run/hash规则。支持构思职责及交接，不作为项目已完成的证据。 |
| S08 `duanxian/design/workflow-docs/duanxian-intent-card.md` | L17、21、59 | §1作者意图、§3读者未指定。历史动机表述为原意压缩，没有导入旧三部曲安排作为现行决定。 |
| S13 `engine/docs/ai-novel-workflow/hld-autonomous-workflow-v1-design.md` | L27、47、60 | §2职责、阶段判界与人审门；§4唯一正式 baseline 入口。支持宏观设计/下游边界与正式输入，不能由摘要替代。 |
| S14 `engine/docs/ai-novel-workflow/development-phase.md` | L31、37、39、61 | §4 D0–D7、§5最小上下文与分层修订、§6客观/场景语义/人工门；80分与前四项70%一致。 |
| S16 `duanxian/design/specs/2026-07-05-duanxian-proposal.md` | L31、45、62 | §2、§8四段式，§13人物功能，§15旧结局/系列，§18 Agent pass与human pending。候选正文明确历史限定，未导入旧终局动机。 |
| S17 `duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/manifest.md` | L31、45、63 | `pending_hld_human_review`、artifact编号与放行条件；支持旧编号/产物不是新版准入。 |
| S18 `duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/gate-report.md` | L45、64 | “放行条件”：下一道是 HLD 人类评审，确认前不得进 LLD；支持。 |
| S23 `engine/docs/ai-novel-workflow/README.md` | L27、29、65 | “目标与非目标”“阶段接口”“统一状态与变更规则”；支持作者批准权、Agent边界与结构回退。 |

两处留存绑定独立重算如下，断言均通过、命令退出 0：

- author-decision 文件 SHA-256：`4f5a070d22a92fb211b9e99709e04e05b16460aa52ae40c7ebb0eaf49249e2bd`，等于 completion 的 `author_decision.sha256`。
- 批准 HTML SHA-256：`80cfc4d82d77683324808ba3f96817914c24fd1de007fae70641789dedf65e36`，等于 decision 的 `human_review_package.html_sha256`。
- 两份 JSON 的 `run_id` 均为 `duanxian-conception-v2-20260811-18`。

这只证明留存对象的这两条绑定与 run 相同，不等于全生产链 validator 重放；报告没有补造缺失 P1、handoff 或运行状态文件。

## 五、全部高风险权威口径抽查

| ID | 候选位置→短引 | 基线证据路径与定位 | 标注是否准确及 verdict |
| --- | --- | --- | --- |
| A01 | L7、9：“不是人格本身”“新感情，不属于顾衡” | `duanxian/conception-approved/human-review-report.md` L91–95，关系变化 L147/169，R-07 L382–389，顾衡 L411–419，沈逾 L400。 | 【当前权威口径】准确；顾衡已死、未爱过沈逾、新决定属于 R-07。PASS。 |
| A02 | L7、9、35：“记忆片段也不是客观录像”“没有当前视觉、听觉、身体、自主移动和现实行动能力” | 同批准报告“文字会话隔离室”L239–243、“记忆重构沙箱”L275–279、“R-07隔离套间”L287–291、R-07接口 L389。 | 当前口径准确；不把样片记忆中的雨声当当前听觉。PASS。 |
| A03 | L9、35：“专家、硬件与授权链复核”“机器输出不自行产生权限” | 同批准报告“现实硬件控制室”L293–297、“跨国威胁处置”L307–311、秦峥 L465–475、贺闻钧 L521–531。 | 当前口径准确；情报与命令分开，物理阻断由现实团队完成。PASS。 |
| A04 | L17、35：“在世妻子程予安”“公共安全也不能取消全部隐私” | 同批准报告程予安 L437–447、周岚 L423–433、原因层保护 L251–255、亲属保护与留痕 L313–317。 | 当前口径准确；亲属拥有独立生活和同意边界，既不阻断救人，也不取消必要访问边界。PASS。 |
| A05 | L11、35、47：“当前实例关停且没有活动备份”“静态材料封存不保证复活” | 同批准报告“开放边界”L325–329、“离线载荷保管库”L281–285、唐黎 L507–517、苏望舒 L605–615。 | 当前口径准确；新加载重新许可，法律身份、连续性和互信仍开放。PASS。 |
| A06 | L43：“approval_scope=conception”“没有重放全量生产链” | `duanxian/conception-approved/author-decision.json` 的 scope/decision/run 与 HTML hash；`conception-completion.json` 的 status/run/author hash；批准 README 日期。 | 当前口径准确；本次重算两条绑定与 run 验证均通过，未扩大批准范围。PASS。 |
| A07 | L31、45：“旧 proposal 的四段式……只说明方案演变”“既不能否定后来的构思批准，也不能替代新版 HLD 批准” | `duanxian/novel-goals.md`第三至五章；`duanxian/design/specs/2026-07-05-duanxian-proposal.md`§2/8/15/18；旧 HLD manifest“收敛状态”。 | 【历史/旧链口径】与【流程规范】分离准确，旧四段式、系列和编号未升级为新事实。PASS。 |
| A08 | L29：“非权威体验样片”“不能把当前人审 Markdown 当作下游机器入口” | `engine/harnesses/novel-conception-autonomous/docs/final-delivery-contract.md`§2–3；批准报告“三个试读场景”L641–689。 | 【流程规范】准确；P1 权威、H1 呈现，雨声/动作仅用于说明样片边界，没有补成故事设定。PASS。 |
| A09 | L11、21–23、39：“只是结构规模”“任何具体商业画像都仍是【未完成项】” | `duanxian/novel-goals.md`一、3及五、2；批准报告“故事的八次推进”L109–171、“三层延伸与职责覆盖”L629–633。 | 当前规模、未完成篇幅和推断读者分别标注；8/10/17/43未换算章节，无现实科学可行性结论。PASS。 |

## 六、范围门与结论边界

**范围门 verdict：PASS。** 实施候选相对冻结基线的最终 diff 为唯一一项 `A outputs/duanxian-audit/goals-summary.md`；基线到候选只有该新增提交，没有先改后恢复的越界历史。候选 detached worktree 的完整 porcelain 状态为空，候选磁盘字节与提交一致。此处证明的是封定候选与本次独立检出状态，不声称远程实施机器当前未提交状态可见。

验收原工作树在写本报告前分支/HEAD符合本作业，`git status --porcelain --untracked-files=all`为空，`git diff <基线> -- README.md duanxian engine`为空。未修改 `.kunora/spec.yaml`、`.kunora/PROMPT.md`、任何既有材料或实施分支。初始化控制证据不进入业务提交。本作业只新增本报告；未运行生产流水线、全仓库测试或破坏性负例，未创建 ISSUE 或联系实施者。

分组汇总：M01/M04 PASS，M02 FAIL，M03 BLOCKED；S01–S07 全部 PASS；A01–A09 全部 PASS；范围门 PASS。合计 19 PASS、1 FAIL、1 BLOCKED，共 21 项。总体 FAIL 只针对第一节候选；读者定位、篇幅、全量运行证据仍是总结如实保留的未完成项，不是本次发现的内容缺陷。Owner 尚未确认目标总结，不进入 B 作业。

## 七、修正指令与补证要求

### C01 / F01：修复 M02 引用定位

候选：`bc2767bcf33ebfa75083a9070fe920f0bec21186`；文件 SHA-256：`67d443d22587cd205f2ef890485d69ab91d73fe28ef8a6d416e97b10bb1dcc1d`；定义书版本：`99e18a0d2f3c8d4d8f069a3150622f8f68a55912`。

结论：FAIL；失败检查 ID：M02。

问题定位：`outputs/duanxian-audit/goals-summary.md` → 六、当前进度与断点 L47 第一处 G00 引用“二、1. 从批准构思到可审校手稿”；来源索引 L51“第一、四、五章及对应小节”。

事实证据：冻结基线 `duanxian/novel-goals.md` → 二、3. 内容权威与呈现分离 L51：“本快照的 Git 跟踪文件中未找到该项目完整的”三个机器交付文件。二、1 L31–37讨论流程方法，不含该留存事实。定义书§2.2、§5.2要求断言能通过路径/小节定位，§6.1 M02要求读到支持断言的内容。

错误与影响：事实正确而具体引用位置错误；文末范围与正文实际引用也不一致，使读者按标注无法在指定小节复核机器包缺口。不得用本验收者重新检索所得证据代替实施文件应有的正确定位。

修正动作：只修改本作业新增总结。将 L47 该引用改为 G00“二、3. 内容权威与呈现分离”；将 L51 G00 索引范围补为“第一、二、四、五章及对应小节”或等价的精确已用小节列表。保留原事实、“未在 Git 留存中找到”的限制、S02 对运行账本的引用及所有开放状态。不需要改写故事正文或另增解释报告。

禁止改变：唯一输出路径、2000–4000中文字符、冻结内容基线、五类口径、六问拟人化、P1内容权威、历史材料隔离、作者批准范围与开放项、实施/验收模型分配；不得修改目标文档、定义书、冻结契约或既有源文件。

复验：实施者追加普通修正提交，不强推；交接新完整 SHA、文件 SHA-256及实际完成哨兵。验收者在新 SHA 独立检出，原样重跑定义书§6.1两个脚本、最终/逐提交范围门及远端核对；重审 M02 全部引用、S06、A06–A09 与相邻未完成项/流程语句，不复用旧候选 PASS。

### C02：补齐 M03 原始完成哨兵证据

候选：`bc2767bcf33ebfa75083a9070fe920f0bec21186`；文件 SHA-256：`67d443d22587cd205f2ef890485d69ab91d73fe28ef8a6d416e97b10bb1dcc1d`；定义书版本：`99e18a0d2f3c8d4d8f069a3150622f8f68a55912`。

结论：BLOCKED（M03 子项）；失败检查 ID：M03。

问题定位：`outputs/duanxian-audit/goals-summary.md` 封定候选的交付证明；不是正文某句错误。缺少实施作业最终响应/日志中的实际成功哨兵。

事实证据：固定定义书§5.3第5项与§6.1 M03要求哨兵和远端候选匹配；本次远端实测为上述候选，当前交接提示词没有原始实施完成响应。

错误与影响：未取得历史输出，不能断言它曾输出或未输出正确哨兵；这不影响已验证的远端存在性，但不满足 M03 的完整证据条件。

修正动作：由编排方补交原始实施完成响应或将可读日志放入本作业授权目录。预期后缀为 `bc2767b`，必须核对实际原文，不能由验收者补写假日志。因 C01 会形成新候选，新的交接应同时携带新 SHA 对应的实际哨兵；不要求在总结文件中添加哨兵或制造第二份业务交付物。

禁止改变：不改总结事实以掩盖日志缺失，不借用其他作业凭据/目录，不在实施分支写验收报告，不推送其他引用，不把推算值充当观测值。

复验：对交接新候选执行 `git ls-remote origin refs/heads/remote-agent/duanxian-audit-gimpl-001`，检查完整 SHA、提交元数据、总结哈希及原始哨兵后缀一致；新 SHA 必须重跑机械与范围门。若编排方裁决调整证据要求，应提供明确裁决，验收者不自行取消定义书条款。

## 八、交接

本报告经本作业分支交编排方；C01 由编排方交实施作业修正，C02 由编排方补证。验收者未向实施者直接注入指令。只有新候选重新满足所有 M/S/A 与范围门后，才可给出 PASS；随后仍由编排方向 Owner 请求目标总结确认。该确认不能由本报告、远端推送或模型自评替代。
