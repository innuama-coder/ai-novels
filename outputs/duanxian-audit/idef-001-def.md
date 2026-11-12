# 《断线》工作项 C 定义书：ISSUE 整理与提交规程

作业：`duanxian-audit-idef-001`；日期：2026-11-12；目标仓库：`innuama-coder/ai-novels`。内容基线固定为 `92573f1cca40f37cee04d2beb8708ff33ba603d6`（下称 BASE）。本作业仅新增本定义书并提交、推送；实际 ISSUE 发布属于 C-实施，不在本轮执行。

## 一、交叉验证发现清单与 ISSUE 清单

### 1.1 输入封定与判定方法

四份报告均已按完整提交 SHA 全文读取并重算 SHA-256。三份验收报告路径相同但 Git 对象不同，不能按文件名覆盖后混用；下面 A1、A2、A3 是本定义书及 ISSUE 正文的唯一来源别名，引用行号均为该对象原始行号。

| 别名 | 作业/报告 | 完整提交 SHA | 仓库相对路径 | 文件 SHA-256 |
| --- | --- | --- | --- | --- |
| B3 | B 实施修正稿 r3 | `ffb8c9a10b51ae23000bc4e9fbd0a203dec120f1` | `outputs/duanxian-audit/implementation-review-report.md` | `fe0dc30f0b16d1101edc1826079ef1e970334312dd463006798c540d05c71f13` |
| A1 | racc-001 | `d7fc94ac9fe4490c523bb112f6c4fb7a8115abe1` | `outputs/duanxian-audit/racc-001-acceptance.md` | `cd79394fe966cb109382f2e8b8f4ebe462de1c43a215b3b0649e4ed475faf3cb` |
| A2 | raccr2-001 | `8a8280e28c5ab5b6369cca1a7fde3e7e822aec3d` | `outputs/duanxian-audit/racc-001-acceptance.md` | `f1811317b130fe24c41da0e8acc4c32b46f1b88a13227644c444ab572495ff35` |
| A3 | raccr3-001 | `bb9598c36ac3b78dceaf8852b14dcca8edae8071` | `outputs/duanxian-audit/racc-001-acceptance.md` | `6c059fd18617a9d981aee0a2ba4afdf07c35ce2876d1b1824b3a35f481b02221` |

交叉验证的单位是**有明确范围的事实命题**。至少两份独立验收报告确认同一事实，第三轮没有推翻该事实，再由本轮回查 BASE 原文，才可纳入。B3 不是第四票；本轮复核也不冒充另一轮独立验收。某轮 I01 总项 FAIL 不抹去其明确保留的核心事实，但被否定的根因、外推和修复范围不得随事实一并入库。三轮总 verdict 都仍为 FAIL，C 不改写这些判决。

本轮对 1444 个原跟踪文件作了与 BASE blob 的逐字节一致性检查，并对下列候选作静态取证；这不等于本轮全文阅读 1444 文件。未导入仓库模块，未执行项目 CLI、pytest、validator、构建或小说流水线。行号来自 BASE 文本；单行 JSON 用 JSON Pointer；缺失结论以完整 Git 跟踪树清单为范围。

### 1.2 Owner 冻结裁决与不可变约束

以下裁决原样保留：

三轮实施+三轮验收后，实施候选 r3（ffb8c9a）实质质量逐轮提升、核心事实发现已被 racc-001/raccr2 两轮交叉确认，但验收方「1444 文件全文阅读硬门」三轮未闭合——Owner 裁决采纳 r3 为审视结论工作基础进入工作项C；C 只能提交**交叉验证过的发现**，B 报告残余争议项不得入库；该裁决与限制须写入最终交付物与 ISSUE 正文（透明呈现）。

以下五条约束原样保留：

- C-实施交付物唯一路径＝`outputs/duanxian-audit/iimpl-001-issues.md`（ISSUE 编号与 URL 记录），唯一新增文件；ISSUE 本体提交到 GitHub innuama-coder/ai-novels。
- 仅提交三轮验收交叉确认的发现；预计 ISSUE 数量 5–9 条（以交叉验证裁定为准，不多不少）。
- C-实施执行器/模型＝kimi-code/k3.1-pro；C-验收＝codex/gpt-6-astra（Owner 冻结）。
- 审视任务全程不得修改仓库既有文件；ISSUE 正文必须包含 B 验收硬门未闭合的透明声明。
- 所有结论引用具体路径作证据；不得虚构仓库不存在的内容。

### 1.3 入选映射及排除裁定

本定义冻结 **7 个 ISSUE 主题 C-I01–C-I07**。全部为 BASE 已存问题或证据限制，不称 C 新增回归；编号为本地追踪键，不是 GitHub 编号。

| 本地键 | 来源 | 纳入的最小事实 | 交叉验证来源与限制 |
| --- | --- | --- | --- |
| C-I01 | B-IC001＋002 | 七个 runtime 拼接双 engine；三个测试入口越出仓库、使用旧 projects 布局 | A1 §4.3 L103–104/F07；A2 §4.4 L131–132/F07 复验；A3 §4.4 L135、§4.5 L161–162。修正 line_sequence 行号，不称 spec 断言必失败 |
| C-I02 | B-IC003 | 两处 README 写 81，BASE 一级技能目录与 SKILL.md 均为 82 | A1 §4.3 L105；A2 §4.4 L133；A3 §4.5 L163。历史新增原因未知 |
| C-I03 | B-IC004 的 17 条限定子集＋005a | 写作素材 17 个 LLD 路径迁移未同步；R07 风格章节引用错位 | A1 §4.3 L106–107；A2 §2 L46、§4.4 L134–135；A3 §4.5 L164–165。取消全树旧串都坏或都有效的概括 |
| C-I04 | B-E005/006，A1 F08 | 根 .gitattributes 模式缺 engine 前缀，三个样本 text/eol 六项均 unspecified | A1 §5.2 L168/F08；A2 §6 F08 L194；A3 §4.2 L111、§6 L202。这是三轮已确认事实，不是单轮新发现 |
| C-I05 | B-IC006 | 07-13 历史 run 的追踪 P1 保留 open，LLD 准入记录 blocked | A1 §4.3 L108；A2 §4.4 L137；A3 §4.5 L167。只指冻结记录，形式追踪失败不等同语义失败 |
| C-I06 | B-IC007 | 同一 07-13 run 的 v3 元数据和 v2 人审说明混用 | A1 §4.3 L109；A2 §4.4 L138；A3 §4.5 L168。不推翻 manifest 的 v3 权威 |
| C-I07 | B-IC008 的留存事实子集 | 三个机器 basename 在 BASE 均无本体，已留存完成记录含运行相对 Pointer，单凭该树不能复验完整链 | A1 §4.1/§4.3 L77–78/L110；A2 §2 L46、§4.1 L82、§4.4 L139；A3 §2 L46、§4.1 L88、§4.5 L169。只作为证据补充请求；明确排除“外部渠道不存在”与“入库政策未定” |

排除表也是实施边界；不得从这里抽取新 ISSUE 来补数量。

| 候选或断言 | 裁定与理由 |
| --- | --- |
| IC004 全树 79 文件/219 命中行均坏链；engine 内全部旧路径均有效；历史文本皆无影响 | 不纳入。文本统计不等于解析结果；A3 §4.5 L164/R3F07 明确反对全称判断。C-I03 只覆盖已逐项定位的写作素材子集 |
| IC005b 缺 frontmatter | 不纳入。无明确强制规范，A1/A2/A3 均要求降为待取证线索 |
| IC008“获取/重验渠道缺位”“入库政策未定”“机器链未运行/批准无效” | 不纳入。政策已明示；外部渠道和现实运行不在冻结树证据内。C-I07 不要求改变不入库政策，也不认定交付违约 |
| IC009 写作目录就地提示 | 不纳入。全局历史隔离说明已在 `duanxian/README.md:L22–23`；局部提示是建议，非交叉确认的独立缺陷。17 件已有五栏修订表，不重复 B3 的“四栏”错误 |
| 旧正文感官“操作数据合规”、会议沉默时长与保护动机构成直接矛盾、无同名等于无工具化 | 不纳入。A3 §4.3/R3F04 推翻或要求保留未知，属于残余争议；会议来源未交代疑点也不在本轮发布集合 |
| B 报告自身 Pointer、测试正负分类、引用行号、七/八控制计数、阅读覆盖与执行日志问题 | 不纳入仓库问题清单。它们是 B 验收修正/控制证据项；本轮修正自己引用的定位，不将报告审查争议移作仓库缺陷 |
| raccr3 单轮新增发现；12/14 个既有测试失败提示；未全文读源码的能力推论 | 不纳入。没有两轮同命题确认或可绑定的原始执行证据，不将测试存量/交接提示说成实测成绩 |

### 1.4 每条 ISSUE 必带的共同正文

第三节的正文生成规则将下方标记内全文追加至每条 ISSUE，不能只链接本定义书代替透明声明。该公共块本身属于每条 ISSUE 正文。

<!-- COMMON-BODY:BEGIN -->
### 基线、交叉验证来源定义与限制声明

证据基线为 `innuama-coder/ai-novels@92573f1cca40f37cee04d2beb8708ff33ba603d6`。正文路径和行号均指该树；JSON 用原对象 Pointer。可用 `git show 92573f1cca40f37cee04d2beb8708ff33ba603d6:<路径>` 回读，不能用最新 main 的行号替代。

交叉验证引用：A1＝racc-001，提交 `d7fc94ac9fe4490c523bb112f6c4fb7a8115abe1`；A2＝raccr2-001，提交 `8a8280e28c5ab5b6369cca1a7fde3e7e822aec3d`；A3＝raccr3-001，提交 `bb9598c36ac3b78dceaf8852b14dcca8edae8071`。三者报告路径均为 `outputs/duanxian-audit/racc-001-acceptance.md`；必须连同提交号解析。B r3 工作基础为 `ffb8c9a10b51ae23000bc4e9fbd0a203dec120f1:outputs/duanxian-audit/implementation-review-report.md`。

三轮实施+三轮验收后，实施候选 r3（ffb8c9a）实质质量逐轮提升、核心事实发现已被 racc-001/raccr2 两轮交叉确认，但验收方「1444 文件全文阅读硬门」三轮未闭合——Owner 裁决采纳 r3 为审视结论工作基础进入工作项C；C 只能提交**交叉验证过的发现**，B 报告残余争议项不得入库；该裁决与限制须写入最终交付物与 ISSUE 正文（透明呈现）。

三轮 B 总验收仍为 FAIL；本 ISSUE 只发布正文列出的交叉确认事实，不宣称全仓审视 PASS、现实运行失败或小说阶段获新批准。静态源码和历史记录不等于本轮功能测试；BASE 未留存不等于对象从未存在或外部渠道不存在。修复建议与关闭条件供后续另行授权工作使用，C-实施/C-验收不运行修复、不修改仓库既有文件。
<!-- COMMON-BODY:END -->

### 1.5 C-I01：构思运行时与测试入口定位

<!-- ISSUE:C-I01:BEGIN -->
标题：[断线审视] 构思 CLI 的七条运行时路径及三份测试入口未适配当前布局

### 问题与影响

严重程度：**high**。类型：当前布局下的静态装载缺陷。`duanxian/conception-production/run.py` 的 ROOT 已指向仓库根下的 `engine/`，传入加载器的七条路径却再次以 `engine/` 起始，组合后七个源码路径均不在 BASE。三个 CLI 测试又以 `parents[4]` 和旧 `projects/duanxian` 布局寻址，不能自足定位本仓库入口。依赖相应 runtime 的操作及这些测试夹具会遇到装载目标缺失；这是静态结论，未运行项目入口或 pytest，不泛称所有子命令在启动时均失败。

### 证据与应然依据

- `duanxian/conception-production/run.py:L14`：`ROOT = Path(__file__).resolve().parents[2] / "engine"`；L41–47 用 `ROOT / relative_path` 装载，实际读取点为 L47 `exec_module`。L112–120 定义阶段加载调用。
- 同文件的全部七个路径如下。表中“正确位置”均在 BASE，前面再加 `engine/` 后的错误位置均不在 BASE；它们同时也是原代码传入的字符串。

| 阶段 | 源行 | 正确位置（仓库相对） |
| --- | --- | --- |
| S1 | L54 | `engine/skills/novel-storyline-architecture-designer/scripts/run_v2.py` |
| W1 | L69 | `engine/skills/novel-world-model-designer/scripts/run_v2.py` |
| E1 | L77 | `engine/skills/novel-environment-system-designer/scripts/run_v2.py` |
| T1 | L85 | `engine/skills/novel-event-timeline-designer/scripts/run_v2.py` |
| C1 | L93 | `engine/skills/novel-character-system-designer/scripts/run_v2.py` |
| Q1 | L126 | `engine/skills/novel-conception-reviewer/scripts/run_v2.py` |
| P1 | L133 | `engine/skills/novel-conception-deliverable-assembler/scripts/run_v2.py` |

- `duanxian/conception-production/tests/test_attempt_selection_cli.py:L12–13,L19–23`、`duanxian/conception-production/tests/test_topology_review_cli.py:L12–13,L19–23`：`ROOT=...parents[4]`，`ENTRYPOINT=ROOT / "projects" / "duanxian" / "conception-production" / "run.py"`；模块执行点均为 L23。
- `duanxian/conception-production/tests/test_line_sequence_review_cli.py:L12–13,L20–24` 同型；其执行点是 **L24**。以测试文件所在位置计算，`parents[3]` 才是仓库根，`parents[4]` 是仓库父目录；本仓库正确入口为 `duanxian/conception-production/run.py`。
- 应然来自该 CLI 自己的 ROOT/加载器契约和 `duanxian/README.md:L10,L24` 所述项目入口及双根寻址。不存在源码不保证 `spec_from_file_location` 返回空值，因此不使用“spec 断言必失败”或固定 `cannot load stage runtime` 异常作为证据。

### 建议与关闭条件

统一以已选定根目录拼接相对路径，逐条消除七个重复前缀；使三个测试入口从本仓库结构计算，不依赖仓库父目录恰好存在另一份项目。目录迁移未同步是静态根因推断，未取证历史提交，不能写成已证历史因果。

未来获代码修复授权后，先枚举核对七个 runtime 与三个测试入口的解析结果，再在隔离环境逐一验证七阶段装载及三个测试模块；记录命令、环境和退出码。一个 CLI selftest 不足以代替全部七个路径。C 发布本 ISSUE 时仅要求证据与正文准确，不执行这些修复验证。

### 交叉验证来源与归并理由

A1 §4.3 L103–104、F07 L263–269；A2 §4.4 L131–132、§6 L193；A3 §4.4 L135、§4.5 L161–162、§4.2 L106。B3 §8 L190–191。三轮均保留路径事实，第三轮校正了 line_sequence 行号。

合并 B-IC001/002：同属构思 CLI 及其验证入口对当前布局的适配，关闭必须同时覆盖生产加载与测试入口。两个具体成因及验证点分别保留。不与文档引用、Git 属性或机器包留存归成一个全仓迁移大项。
<!-- ISSUE:C-I01:END -->

### 1.6 C-I02：技能计数

<!-- ISSUE:C-I02:BEGIN -->
标题：[断线审视] 两处 README 的 81 个技能计数与冻结树实际 82 个不一致

### 问题、证据与影响

严重程度：**low**。类型：当前导览数据不一致。`README.md:L5` 写“81 个 `novel-*` 技能”；`engine/README.md:L9` 同写 81。BASE 的 `engine/skills/` 下直接一级目录有 82 个，各有一级 `SKILL.md`，且全部符合 `novel-*` 前缀。统计对象为目录/技能入口，不是嵌套文件、测试数或能力通过数。

应然：上述两处是现有引擎库存说明，应与其指向的技能集合一致。影响为库存认知和导览维护偏差，不声称损害运行。可用 `git ls-tree -rz --name-only BASE`，筛选路径分段恰为 `engine/skills/<name>/SKILL.md` 后计数，结果 82；BASE 为公共声明中的完整 SHA。

### 建议与关闭条件

后续授权维护时，两处同步采用对应目标提交的实际计数，或去掉需人工同步的固定数值；保留明确统计口径。关闭时用同一提交重新枚举集合并对照两份说明，不能以当前 HEAD 数量混配 BASE。关于“某次新增技能后遗漏更新”的历史原因未知，不作为本 ISSUE 事实。

### 交叉验证来源与归并理由

A1 §4.3 L105；A2 §4.4 L133、§2 L43；A3 §4.5 L163、§2 L43。B3 §6 L163、§8 L192。

两处相同数字归一条文档数据问题，可独立关闭；不扩入每技能是否都有脚本/测试、技能能力分类或 harness 数量等未在本条交叉确认的命题。
<!-- ISSUE:C-I02:END -->

### 1.7 C-I03：写作素材来源追溯

<!-- ISSUE:C-I03:BEGIN -->
标题：[断线审视] 17 份历史写作素材的 LLD 路径及 R07 的 HLD 章节引用需要迁移映射

### 问题与影响

严重程度：**medium**。类型：历史素材的来源可追溯性问题。17 件写作素材各保留一个旧根 `docs/superpowers/specs/lld/` 的反引号 LLD 引用；这些文本路径在 BASE 仓库根下不能直接定位，以 `duanxian/design/specs/lld/` 替换前缀后 17 个目标均存在。R07 素材另将风格/语言规则指向 HLD §10.x，而该历史 HLD v4 的风格章已是 §9，现 §10 为 HLD→LLD 交付包。

这些是历史素材引用，不是当前批准 P1 的故事规则。应然是素材中名为“LLD 引用”“HLD 引用”的字段可追溯到其声明的设计来源，不能以新的故事事实补旧引用。`duanxian/README.md:L22–23` 已规定批准构思优先、旧设计属于历史链，故不要求将旧素材升级为现行正文。

### 证据：17 个确定的路径映射

下表源路径与目标均为完整仓库相对路径。各源行的旧文本精确等于目标将 `duanxian/design/specs/lld/` 换成 `docs/superpowers/specs/lld/`，不是 Markdown 超链接自动解析结论。全部源、全部新目标均已按 BASE 树核对；范围限这 17 项。

| 素材源路径 | 原始行 | 迁移后实际目标 |
| --- | --- | --- |
| `duanxian/writing/characters/2026-06-07-writer-R07.md` | L13 | `duanxian/design/specs/lld/characters/2026-06-07-character-it.md` |
| `duanxian/writing/characters/2026-06-07-writer-betrayer.md` | L13 | `duanxian/design/specs/lld/characters/2026-06-07-character-betrayer.md` |
| `duanxian/writing/characters/2026-06-07-writer-colleagues.md` | L13 | `duanxian/design/specs/lld/characters/2026-06-07-character-colleagues.md` |
| `duanxian/writing/characters/2026-06-07-writer-jiling.md` | L14 | `duanxian/design/specs/lld/characters/2026-06-07-character-jiling.md` |
| `duanxian/writing/characters/2026-06-07-writer-qianxu.md` | L13 | `duanxian/design/specs/lld/characters/2026-06-07-character-qianxu.md` |
| `duanxian/writing/characters/2026-06-07-writer-shenyu.md` | L13 | `duanxian/design/specs/lld/characters/2026-06-07-character-shenyu.md` |
| `duanxian/writing/characters/2026-06-07-writer-zhengbozhou.md` | L14 | `duanxian/design/specs/lld/characters/2026-06-07-character-zhengbozhou.md` |
| `duanxian/writing/scenes/2026-06-07-scene-K1.md` | L15 | `duanxian/design/specs/lld/scenes/2026-06-07-scene-K1.md` |
| `duanxian/writing/spaces/2026-06-07-writer-apartment.md` | L15 | `duanxian/design/specs/lld/spaces/2026-06-07-space-apartment.md` |
| `duanxian/writing/spaces/2026-06-07-writer-city.md` | L14 | `duanxian/design/specs/lld/spaces/2026-06-07-space-city.md` |
| `duanxian/writing/spaces/2026-06-07-writer-corridor.md` | L14 | `duanxian/design/specs/lld/spaces/2026-06-07-space-corridor.md` |
| `duanxian/writing/spaces/2026-06-07-writer-digital-realm.md` | L13 | `duanxian/design/specs/lld/spaces/2026-06-07-space-digital-realm.md` |
| `duanxian/writing/spaces/2026-06-07-writer-hotel-room.md` | L14 | `duanxian/design/specs/lld/spaces/2026-06-07-space-hotel-room.md` |
| `duanxian/writing/spaces/2026-06-07-writer-meeting-room.md` | L14 | `duanxian/design/specs/lld/spaces/2026-06-07-space-meeting-room.md` |
| `duanxian/writing/spaces/2026-06-07-writer-operation-room.md` | L13 | `duanxian/design/specs/lld/spaces/2026-06-07-space-operation-room.md` |
| `duanxian/writing/spaces/2026-06-07-writer-security-hall.md` | L14 | `duanxian/design/specs/lld/spaces/2026-06-07-space-security-hall.md` |
| `duanxian/writing/spaces/2026-06-07-writer-server-room.md` | L14 | `duanxian/design/specs/lld/spaces/2026-06-07-space-server-room.md` |

章节错位的直接证据：`duanxian/writing/characters/2026-06-07-writer-R07.md:L14` 引“§10.2（三阶段语言）/ §10.3（情感约束）/ §10.4（记忆）/ §10.6（通讯窗口）/ §10.8（禁用语）”，L16 又指“§10.2 定义”；`duanxian/design/specs/2026-06-06-hld-digital-life-novel.md:L10` 记 v4.0 修订日为 **2026-06-07**，L312–339 实为 §9 风格与用语规范，含 9.1–9.3；L343 是 §10 HLD→LLD 交付包。路径能映射不代表旧小节可以机械减一。

### 建议与关闭条件

后续授权维护时建立显式迁移映射或补充勘误，不覆盖历史事实；逐条检查 17 个文本引用能定位目标。R07 五个风格指称须按内容分别对照：确有对应内容的给准确定位，无对应内容的注明历史版本依赖或待核，不补造缺失规则。对历史文件采取何种勘误方式由后续授权决定；C 阶段仅登记问题。

全树 `docs/superpowers` 的 79 文件/219 行只是文字命中，既不证明全部失效，也不证明其余全部有效。`engine/README.md:L27` 的根约定和 `engine/scripts/validate_prd_contract.py:L17–23` 的迁移 resolver 只是具体反例，不是全体文档链接豁免。关闭本 ISSUE 应覆盖上表全部 17 项和 R07 五个内容指称，不能仅 grep 抽样通过。

### 交叉验证来源与归并理由

A1 §4.3 L106–107；A2 §2 L46、§4.4 L134–135；A3 §4.5 L164–165/R3F07 L299–301。B3 §8 L193–194 的事实子集；其宽泛全称处理不采用。

合并 IC004 已证子集与 IC005a：均是历史写作素材到设计来源的追溯迁移，R07 同时出现两类问题，共享逐素材映射与内容核对验收。编号变更的历史因果仅为推断；无 frontmatter、就地提示建议和全仓路径治理不在本条内。
<!-- ISSUE:C-I03:END -->

### 1.8 C-I04：Git 字节属性

<!-- ISSUE:C-I04:BEGIN -->
标题：[断线审视] .gitattributes 的 HLD 字节稳定规则未匹配 engine 下的实际路径

### 问题、证据与影响

严重程度：**medium**。类型：当前仓库属性规则与布局不匹配。根 `.gitattributes:L1–2` 明示 HLD artifact 参与精确字节 manifest，需跨平台保持文本字节稳定；L3–9 的模式以 `harnesses/novel-hld-autonomous/` 起始，L11–17 以 `skills/novel-hld-*/` 起始，L19–23 以 `skills/novel-development-baseline-preparer/` 起始，均无当前布局的 `engine/` 前缀。

在与 BASE 相同的索引上执行以下只读命令，三个真实文件的 text/eol 共六项均为 `unspecified`：

```bash
git check-attr --cached text eol -- \
  engine/skills/novel-hld-finalizer/SKILL.md \
  engine/harnesses/novel-hld-autonomous/manifest.yaml \
  engine/skills/novel-development-baseline-preparer/SKILL.md
```

应然依据是该属性文件自身的字节稳定意图和 `text eol=lf` 规则。实际结果说明这些仓库规则未对样本生效，不能据规则文本宣称已强制 LF。风险是跨平台检出时缺少预期的仓库级文本属性约束，**不是已观察到 hash 损坏或某用户环境一定发生 CRLF 转换**；全局配置影响与历史转换结果未取证。

### 建议与关闭条件

后续配置维护授权后，按实际树位置调整规则覆盖范围，审视既有字节与 manifest 的兼容性，保留可复验记录。关闭时对预期受控文件集合检查 text/eol，而不只复查三个样本；需要跨平台验证时另行授权并记录环境。C 不修改 `.gitattributes`、不批量归一化历史文件。

### 交叉验证来源与归并理由

A1 §5.2 L168 与 F08 L273–279；A2 §6 F08 L194（独立复现六项）；A3 §4.2 L111、§6 L202。B3 §6 L165、证据 B-E005/006。

独立于 C-I01/C-I03：作用机制是 Git 属性匹配与字节策略，关闭标准与 Python 入口或文本引用不同；“迁移”只是共同背景，不能据此并成不可独立验收的大项。
<!-- ISSUE:C-I04:END -->

### 1.9 C-I05：旧 HLD 追踪门

<!-- ISSUE:C-I05:BEGIN -->
标题：[断线审视] 07-13 历史 HLD 的 HLD-TRACE-CLOSURE P1 仍为冻结记录中的 open

### 问题、证据与影响

严重程度：**medium**。类型：历史运行记录中的未闭合追踪门，**不是现实至今未处理的断言**。

- `duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/artifacts/12-hld-integrity-report.md:L25`：`HLD-TRACE-CLOSURE`、P1、`open`，说明 artifact 01 的 Fact Trace 未逐字段绑定 Upstream evidence；L57 同一稳定风险 ID 的状态仍为 open。
- 同文件 L32：`Semantic consistency passes, but artifact 01 trace closure fails strict validation.`；L33 为人审 `pending_required`，L34 为 LLD `blocked_revision_required`。因此必须区分记录自述的语义一致性通过、形式追踪失败和人审待定，不能统称“语义失败”。这里的 validator 失败是历史记录自述，不是 C 本轮重跑。
- `duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/artifacts/final-hld-package.md:L20–22` 分别为 `fail: HLD-TRACE-CLOSURE`、`pending_required`、`blocked_revision_required`。
- 应然定位：`duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/manifest.md:L11–15` 保留人审前不得进入 LLD；上述 integrity L32–34 要求语义和形式追踪都通过，且人审确认后才能放行。

对 BASE 全树执行 `git grep -l -F HLD-TRACE-CLOSURE BASE --`，只有上述 integrity 与 final package 两个文件命中，未在这组记录内取得关闭项；该检索不排除其他 ID、其他渠道或现实后续处置。影响是该历史包本身不能作为已满足 LLD 准入的凭据，不判断八月批准后的新版进度。

### 建议与关闭条件

由后续获授权的 HLD 接管者明确这条历史门的承接关系：若继续消费该 run，补足逐字段追踪与同版完整性复核，再取得所需人审；若已被新流程替代，提供显式替代关系和适用范围。保留历史记录，不将原 open 擦成 pass；取得受控关闭/替代证据后，以新记录的路径、版本、hash 与门状态核验。C 只发布 ISSUE，不重放旧 validator、不授予新准入。

### 交叉验证来源与归并理由

A1 §4.3 L108；A2 §4.4 L137；A3 §4.5 L167、§4.4 L153。B3 §8 L196。

独立保留 IC006；与 C-I06 虽同属 07-13 run，追踪闭合/准入处置和版本标签纠正的证据、责任与关闭条件不同。改 v2/v3 标签不能消除 P1，反之亦然。
<!-- ISSUE:C-I05:END -->

### 1.10 C-I06：同一 run 的版本指称

<!-- ISSUE:C-I06:BEGIN -->
标题：[断线审视] 07-13 HLD 完整性报告的人审说明混用 v2.0 与 v3.0

### 问题、证据与影响

严重程度：**low**。类型：历史包的评审对象版本指称不一致，涉及评审对象追溯，不是纯措辞润色。

`duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/artifacts/12-hld-integrity-report.md:L8,L11` 将上游 canonical 和本文件版本写为 v3.0，但 L33 人审依据写 `v2.0 is newly presented after material world reconstruction.`。`duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/manifest.md:L12–15` 明确输出 v3.0、以 `canonical-world-facts-v3.0.md` 为唯一事实源并等待人审。该 run 下 `canonical-world-facts-v2.0.md` 与 `canonical-world-facts-v3.0.md` 均存在，不能忽略标签差异或自动删除 v2 历史文件。

应然依据为 manifest 指定的本次输出及唯一事实源；影响是读者不能仅凭人审说明明确其指向的版本。事实只支持标签混用，不证明实际审错版本，也不推翻 v3 的权威，不将旧 HLD 提升为当前批准构思。

### 建议与关闭条件

后续授权维护时，按 manifest 和实际评审对象给出可追溯的版本勘误或说明；涉及历史 v2 的引用保留其历史性质。关闭需逐项对照 manifest、integrity 元数据和 L33 的版本指称及真实评审对象，不得仅全局替换字符串、删除历史版本，亦不得顺带把 pending/blocked 改成通过。C 不改原文。

### 交叉验证来源与归并理由

A1 §4.3 L109；A2 §4.4 L138；A3 §4.5 L168。B3 §8 L197。

独立于 C-I05，因为本条只解决评审版本指称的一致性。不得把本轮偶见但未获两轮同命题确认的其他版本字符串扩入范围。
<!-- ISSUE:C-I06:END -->

### 1.11 C-I07：冻结留存与复验证据

<!-- ISSUE:C-I07:BEGIN -->
标题：[断线审视] 冻结树未留存三个机器交付文件，需补充同版复验的受控证据

### 问题与范围

严重程度：**medium**。类型：**证据补充请求，不是已证生产故障或留存政策违约**。三轮一致确认 BASE 没有 `novel-conception-package.json`、`development-handoff.json`、`hld-completion.json` 这三个精确 basename；留存的批准/完成记录仍包含运行相对路径和 hash。因此只取得该 Git 树的消费者不能据此完成同版机器包及后续准入链复验。本轮没有取得运行包或外部受控取证入口，不推断它们在仓库外不存在。

### 证据、应然依据与反证边界

- `duanxian/conception-approved/README.md:L3` 明记“运行账本和历史尝试不纳入 Git”；根 `.gitignore:L11–18` 忽略 conception-runs、compatibility-migrations、development 等运行目录。政策已明示，不能把“入库政策未定”当根因，也不据缺本体否定作者批准。
- `duanxian/conception-approved/conception-completion.json` 的 `/run_id` 为 `duanxian-conception-v2-20260811-18`，`/status=ready`；`/development_handoff/path=P1/development-handoff.json`、`/development_handoff/sha256=d48194db32a43575c96ff2df0c9bccf0f8d95a98f2b7bc7bc601068078c33957`；`/p1_manifest/path=P1/package-manifest.json`、`/p1_manifest/sha256=bba81d35a089320074eb8677911707052ba99b1265fbf19731c78785a1eef8ce`。这些是运行相对 Pointer，不是仓库内存在文件的证明。
- `duanxian/conception-approved/author-decision.json` 的 `/decision=approved`、`/approval_scope=conception`；`/machine_package/manifest_sha256` 与上述 p1_manifest 引用相同。相同只是引用值一致；作者决定本体可读，不把它称为未留存。`/unresolved_items=[]` 在顶层，不在 `/approval_record` 内。
- 对 `git ls-tree -rz --name-only 92573f1cca40f37cee04d2beb8708ff33ba603d6` 的全部 1444 条路径按 basename 精确比较，上述三个名字各零项。`hld-completion.json` 的零项只登记后续机器凭据在此树不可得，**不把它说成构思完成记录应包含的文件，也不推出新版 HLD 未运行**。
- 应然与验证方向来自 `engine/harnesses/novel-conception-autonomous/docs/final-delivery-contract.md:L17–24,L48–58,L64–79,L85–91`：机器包、manifest、handoff、来源链、当前状态与正式验证须同版绑定，结构/hash 不能单独证明语义与准入。此契约不自动要求把运行账本公开入 Git。

### 建议与关闭条件

请后续责任人提供或指认**已有受控渠道**及对应同版包的取证方式；若尚未建立，再由 Owner 决定渠道建设。这是后续取证建议，不是 C 对外部渠道现状的裁定，不要求改变现有不入库政策、不要求把秘密或运行数据公开到 ISSUE。

关闭本证据请求时，应有可审计的访问说明、确切 run/版本、包清单及 hash，能回溯 manifest、完成记录、作者决定、正式 validation/execution/实现快照和所需来源链。完整可消费性结论还需在另获授权的受控环境按契约执行相应 validator/状态重放并核对 handoff 边界；公开 ISSUE 只登记脱敏结果和受控证据引用。只有 basename 存在或两项 hash 一致不足以宣布全链可用。后续 HLD 状态需独立的同版证据，不能从构思 ready 推得。

### 交叉验证来源与归并理由

A1 §4.1 L77–78、§4.3 L110；A2 §2 L46、§4.1 L82、§4.4 L139；A3 §2 L46、§4.1 L88、§4.5 L169/R3F07 L299–301。B3 §8 L198 的留存事实保留，**“获取/重验渠道缺位”这一已被 A3 否定的外推及根因不采用**。

三个名字只组成一个冻结树证据可得性请求，构思与 HLD 阶段含义分别保留。不拆成三个生产缺陷，不与 C-I01 的确定路径装载故障合并，不将本条建议升级为“Owner 已同意机器本体入库”。
<!-- ISSUE:C-I07:END -->

## 二、粒度原则与去重边界

一 ISSUE 一个可独立处理的问题族，以共同受影响对象、处理责任和关闭证据决定归并。共同出现“迁移”“版本”“未完成”不足以归并。C-I01 保留生产与测试两种路径成因；C-I03 保留路径迁移与章节内容映射两个验收子项。C-I04 的 Git 属性、C-I05 的追踪准入、C-I06 的评审版本、C-I07 的取证各有独立关闭条件；七项能分别交接和验收。

证据门槛为：BASE 的真实源路径＋原始行或 Pointer＋短引/精确统计规则＋至少两轮同命题确认＋第三轮反证处理。正面存在性用 Git 对象核验；负面结论明确全集、匹配方式和不能推出的事实。静态机制与运行成绩、历史状态与现实进度、批准记录与完整链复验分别陈述。严重程度是本定义按影响给出的分派优先级，不是原作者风险编号：例如 C-I05 中源记录 P1 是历史门级别，ISSUE 的 medium 是本次历史接管优先级。

去重以仓库全部 open/closed ISSUE 为范围，排除 PR。2026-11-12 本轮通过 GitHub 连接器执行 `repo:innuama-coder/ai-novels is:issue` 搜索，返回空列表；这仅是搜索快照，不能证明全量无 ISSUE，也不能替代实施时的分页列表。C-实施需 GET 仓库 ISSUE 全量分页，比较标题、正文路径、稳定风险 ID、问题范围和关闭条件，不只按标题精确匹配；重试和恢复时再核对。

发现等价旧 ISSUE 时不新建、不擅自编辑/评论/重开：在唯一记录中写 `DUPLICATE`、真实编号/URL、等价证据。若旧正文缺冻结限制声明或本定义的证据，不自动视为验收合格，也不通过再建一条绕过去重；交 Owner 决定后续授权。现有 7 个主题落在 5–9 区间；实施必须覆盖这 7 项，不能自行添删、拆并或为凑 5–9 数量引入排除项。重复/失败导致实际新建数量偏离时如实登记并标未完成，提交交接记录供裁决，不伪造数量或宣称全部 PASS。

## 三、提交规程：GitHub API、逐条记录与失败处置

### 3.1 发布权限与请求内容

C-实施的目标只限 `innuama-coder/ai-novels`。使用 GitHub REST API 的仓库 ISSUE 端点，工具为 `curl`（本定义不依赖 gh 安装）。凭据文件只引用 `/home/kunora/duanxian-audit-iimpl-001-gh.cred`，不要复制本定义作业的凭据；凭据不得进入仓库、JSON payload、日志、终端或 ISSUE。运行前核对文件可读、权限 600；不要输出内容。禁用 shell xtrace、curl verbose/trace；不允许 HTTP 重定向将 Authorization 带向其他地址。

每个请求只发 `title` 和 `body`，严重程度写在正文；不假设仓库已有 label，不修改 assignee、milestone、标签或已有 ISSUE。POST `/repos/innuama-coder/ai-novels/issues`；读取 `number`、`html_url`，再 GET 单条回读。C 阶段不修源码、不执行第一节列出的未来修复测试。

### 3.2 确定性生成七个请求体

以下代码是 **C-实施阶段** 的可执行准备步骤，本 C-定义未执行任何 POST。先以 Owner/编排交接提供的完整 C-定义候选 SHA 读取本文件并核验文件 SHA-256；不可直接信任活动分支 tip。`C_DEF_SHA` 由真实交接填写，不猜测。临时 payload 与响应放在本作业 `.kunora/c-issues/` 控制目录，不提交；唯一业务新增文件仍是 ISSUE 记录。

```bash
set +x
umask 077
: "${C_DEF_SHA:?需要交接中的完整定义书提交 SHA}"
mkdir -p -- .kunora/c-issues
git show "$C_DEF_SHA:outputs/duanxian-audit/idef-001-def.md" > .kunora/c-issues/definition.md
python3 - <<'PY'
import hashlib, json, re
from pathlib import Path
p = Path('.kunora/c-issues')
doc = (p / 'definition.md').read_text(encoding='utf-8')
common = re.search(r'<!-- COMMON-BODY:BEGIN -->(.*?)<!-- COMMON-BODY:END -->', doc, re.S).group(1).strip()
ids = re.findall(r'<!-- ISSUE:(C-I\d{2}):BEGIN -->', doc)
assert ids == [f'C-I{i:02d}' for i in range(1, 8)]
for key in ids:
    part = re.search(r'<!-- ISSUE:' + key + r':BEGIN -->(.*?)<!-- ISSUE:' + key + r':END -->', doc, re.S).group(1).strip()
    first, body = part.split('\n', 1)
    assert first.startswith('标题：[断线审视] ')
    payload = {'title': first.removeprefix('标题：'),
               'body': f'<!-- duanxian-audit-idef-001:{key}:base=92573f1cca40f37cee04d2beb8708ff33ba603d6 -->\n\n' + body.strip() + '\n\n' + common + '\n'}
    raw = (json.dumps(payload, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    (p / (key + '.json')).write_bytes(raw)
    print(key, 'payload_sha256=' + hashlib.sha256(raw).hexdigest(), 'body_bytes=' + str(len(payload['body'].encode())))
PY
```

标题、正文、公开稳定标记由固定定义直接生成，不人工删改限制声明、不补入排除项。标记用来发现本次已创建条目；它不是服务器幂等键。对每条 payload 做 UTF-8/秘密模式检查，人工比对路径、建议、交叉来源与公共声明。若平台正文长度限制不容纳某条内容，先记录失败，不自行删证据后发布。

### 3.3 安全的请求原语与全量去重

以下 Bash 原语将鉴权头通过管道配置交给 curl，凭据仅以命令替换读取，响应和 HTTP 状态分开保存。请求 URL 固定为授权仓库下；**不要自动循环 POST**。

```bash
set +x
C_CRED=/home/kunora/duanxian-audit-iimpl-001-gh.cred
C_API=https://api.github.com/repos/innuama-coder/ai-novels
api_request() {
  local method="$1" path="$2" dest="$3" payload="${4-}"
  local args=()
  if [ -n "$payload" ]; then args=(--data-binary "@$payload"); fi
  curl --silent --show-error --proto '=https' --connect-timeout 15 --max-time 60 \
    --config <(printf 'header = "Authorization: Bearer %s"\n' "$(cat -- "$C_CRED")") \
    --header 'Accept: application/vnd.github+json' \
    --header 'Content-Type: application/json' \
    --request "$method" --url "$C_API$path" \
    --output "$dest" --write-out '%{http_code}' "${args[@]}"
}

page=1
while :; do
  dest=".kunora/c-issues/list-$page.json"
  code=$(api_request GET "/issues?state=all&per_page=100&page=$page" "$dest")
  rc=$?
  if [ "$rc" -ne 0 ] || [ "$code" != 200 ]; then
    printf 'LIST-FAIL page=%s transport=%s http=%s\n' "$page" "$rc" "$code"
    break
  fi
  count=$(python3 - "$dest" <<'PY'
import json,sys
data=json.load(open(sys.argv[1],encoding='utf-8'))
assert isinstance(data,list)
print(len(data))
PY
  ) || break
  [ "$count" -eq 0 ] && break
  page=$((page + 1))
done
```

只有所有页面成功且最后一页为空，才认定本次枚举完整；循环中出现失败必须按失败路径处理，不能将 `break` 当成功。JSON 中有 `pull_request` 字段的条目不是 ISSUE，比较时排除，但翻页时按原始数组计数。扫描完整标题与正文，结合 C-I01–07 的证据路径/稳定 ID 做人工语义去重；对 closed 条目也检查关闭依据。列表搜索漏项或排序变化时，在每次准备 POST 前再取最新页面并按稳定标记复核。

### 3.4 单条创建、回读和记录

七条按 C-I01→C-I07 串行处理。某条核对无重复后，才执行一次该条 POST。例如 C-I01（其他条目替换本地键，不批量无条件执行）：

```bash
C_ID=C-I01
C_PAYLOAD=".kunora/c-issues/$C_ID.json"
C_RESPONSE=".kunora/c-issues/$C_ID.response.json"
C_CODE=$(api_request POST /issues "$C_RESPONSE" "$C_PAYLOAD")
C_RC=$?
printf '%s transport=%s http=%s\n' "$C_ID" "$C_RC" "$C_CODE"
```

成功条件必须同时满足 curl 退出 0、HTTP 201、响应包含正整数 `number` 和目标仓库的 `https://github.com/innuama-coder/ai-novels/issues/<number>`，且响应不是 PR。随后 GET `/issues/<number>`，要求 HTTP 200，`title`/`body` 与 payload 精确一致（JSON 解码后比字符串，不只看摘要），marker 唯一。记录真实 URL、编号、GET 核对时间、payload SHA-256 和解码正文 UTF-8 SHA-256；BODY hash 只核内容一致，不替语义审查。拿到编号即先写入唯一记录，再进行下一条，避免中断丢失已创建事实。POST 已成功而 GET 暂未成功时记录 `CREATED_UNVERIFIED`，不得重发 POST。

### 3.5 失败、重试一次与恢复

固定流程是**失败识别→查重/状态核对→安全情况下重试一次→记录→跳过→交接报告**。每条最多两次 POST 尝试，失败不阻止其他无依赖且能安全确认的主题继续；公共鉴权/枚举失败时停止余下创建并记录整体阻塞。具体分支：

1. 连接超时、断连或 5xx：创建结果可能已落库。先重新完整分页查 stable marker、标题和问题内容；若找到唯一条目，回读并记录，禁止重建。若枚举完整且确认不存在，可重试一次；若无法排除已创建，则记 `UNKNOWN` 并跳过，不能盲目重试。
2. 401/403 权限问题：不换账号、不打印凭据。记 HTTP 状态及脱敏原因，检查已授权凭据配置；权限未恢复不重复请求。429 或限流明确要求等待时遵守服务返回时间，再至多重试一次；不要密集轮询。未恢复则 `FAILED`/`BLOCKED`。
3. 422 或明确校验错误：检查原 payload 格式、目标与平台错误；只允许修请求编码/格式，不改冻结标题或正文语义。能安全修正且确认未创建后重试一次，否则跳过。
4. 回读失败只重试 GET 一次，不重试 POST；正文不符或同标记多条记 `MISMATCH`/`DUPLICATE_CONFLICT`，不自动修改、关闭或删除已发布 ISSUE，交 Owner 处理。
5. 第二次仍失败：在记录中保留每次 UTC 时间、transport/HTTP 状态、脱敏原因、是否有可确认编号、下一步责任。无编号时写“未确认创建”，不能填假编号、假链接或成功哨兵。

重启作业先读已提交/本地记录和线上全量列表，以 marker＋实际 GET 结果恢复；不得因本地 JSON 还在或某次命令退出 0 就跳过核验。只允许创建清单内 ISSUE，不自动评论、通知、编辑、重开、删除或关闭已有 ISSUE。

### 3.6 提交后列表核对与记录格式

全部条目处理后重新获取全量 ISSUE 列表，逐条 GET 回读，形成 C-I01–07 到唯一真实编号/URL 的一一映射；检查无清单外新增、无一条标记对应多个 ISSUE。记录数、distinct 编号数、新建数、重复数、失败数分别列明，不能以“列表有七条”替代内容验证。

`outputs/duanxian-audit/iimpl-001-issues.md` 至少包含：作业/仓库、BASE、定义候选完整 SHA 和文件 hash、四报告 SHA/hash、开始/结束时间、Owner 原样裁决与不可变约束、以下七行状态表、失败处置、文件范围检查和交接结论。控制响应/payload 不提交。

| 必填列 | 含义 |
| --- | --- |
| 本地键、冻结标题、严重程度 | 严格对应七主题，不能另加候选 |
| 状态 | CREATED_VERIFIED / CREATED_UNVERIFIED / DUPLICATE / FAILED / UNKNOWN / BLOCKED / MISMATCH / DUPLICATE_CONFLICT |
| 实际编号与 URL | 只写 API 已确认值；未创建/未知项留明原因，不造链接 |
| 来源与候选绑定 | 定义 SHA、正文 marker、payload/body SHA-256、A1/A2/A3 对应项 |
| 尝试与回读 | 请求次数、时间、HTTP/transport 状态、回读一致性 |
| 去重与异常 | 比较的旧 ISSUE、等价/不等价原因、重试/跳过理由、待处理责任 |

## 四、验收检查单：发布完整性与边界

本节验收 C-实施“准确发布问题”，不是要求缺陷已经修好。全部必要检查通过才判 C-实施 PASS；GitHub 不可达、凭据/证据缺失时记 BLOCKED；已定位内容或越界问题记 FAIL。

| ID | 检查与通过条件 | 核验方式 |
| --- | --- | --- |
| C-M01 | 定义与四报告版本固定且 hash 一致 | 从交接完整 SHA 取对象重算；不得以最新分支替换 |
| C-M02 | 覆盖本定义七主题、实际编号唯一；正常新建七条且处于冻结 5–9 范围 | 全量分页列表＋七次 GET，与唯一记录互对；重复/失败如实计数，未裁决不得声称七条全完成 |
| C-M03 | 每条实际存在于目标仓库，真实编号、URL、state/类型可读且不是 PR | GET `/issues/<number>` 与 html_url 仓库前缀、公开标记核对 |
| C-T01 | 标题和完整正文与确定性生成 payload 一致 | JSON 解码后逐字比对；禁止仅比标题、hash摘要或节名 |
| C-T02 | 全部含问题、严重程度、证据、应然、影响、建议/关闭条件、来源、归并理由 | 七条正文全读，不用抽样替代 |
| C-T03 | 每条包含原样 Owner 裁决和 B 阅读硬门未闭合的透明声明 | 公共正文逐字比对；不能只链接到本定义书 |
| C-E01 | 源路径、原始行/Pointer 真实，且足以支持所述窄命题 | 所有显式源路径检查存在性；每条至少抽查一处正证与一处限制/反证，出现错误即扩查同类全部 |
| C-E02 | 专项高风险证据全部复验 | C-I01 七路径/三测试；C-I03 17映射与五章节内容指称；C-I04 三路径六属性；C-I05/06完整历史门/版本；C-I07三basename与JSON字段全部核，不只抽样 |
| C-E03 | 每条至少两轮同命题确认，A3反证未被带回 | 核对第一节入选/排除表；不以单轮新发现或B自评充数 |
| C-B01 | 无“外部渠道不存在”、现实未发生、全仓PASS、旧HLD当前权威等越界结论 | 全文检查正文与记录；缺失/旧链/静态边界人工审核 |
| C-D01 | open/closed 去重完整，无重复创建或遗漏处理 | 分页终点、旧ISSUE比较、marker唯一性、重试记录互证；搜索空列表不算全量证据 |
| C-X01 | 仅新增 ISSUE 记录，仓库既有文件未修改 | C-实施开始 SHA 到候选的最终 diff 仅 A 指定记录；逐提交路径集合只含该记录；无删除、改名、源码/历史报告变更 |
| C-X02 | 无清单外发布和未授权行为，凭据未泄露 | 核 ISSUE 列表/时间/marker及控制执行记录；不凭干净Git证明从未写忽略区或运行测试 |
| C-H01 | 唯一交付记录 UTF-8、无假编号、完整失败账与线上一致 | 文件回读、秘密模式扫描、七行数量闭合、逐URL确认 |
| C-H02 | 提交与推送交付绑定 | author/committer、允许分支、完整候选SHA、远端tip、记录hash、哨兵一致；提交前文件检查/提交后范围检查有真实记录 |

C-I01 的源码加载测试、C-I04 的跨平台转换验证、C-I07 的正式链重放属于以后修复/取证工作的关闭条件，C-验收只做允许的静态/API/文件核验。缺原始控制日志只能保留对应子门未知，不能凭未知指控已经越权，也不能把未知填成 PASS。

## 五、实施作业工作指令

执行器/模型按 Owner 冻结为 **kimi-code/k3.1-pro**。本定义不自行启动实施 Agent，不代编排分配新工作树或凭据。后续实施作业以自己的 spec/PROMPT 和 ACK 启动序为准，工作分支与起始 SHA 从该作业契约读取；不能把本 C-定义分支当作实施推送目标。

1. 全文读取 C-实施作业契约、这份固定 SHA 定义书及四份报告。核对第一节完整 hash；报告可按以下只读命令取得，再对照交接定义 SHA。不要 checkout 报告分支到实施主树，也不要将报告复制为额外业务提交。

   ```bash
   git fetch origin remote-agent/duanxian-audit-idef-001 remote-agent/duanxian-audit-rint2-001 remote-agent/duanxian-audit-racc-001 remote-agent/duanxian-audit-raccr2-001 remote-agent/duanxian-audit-raccr3-001
   git show ffb8c9a10b51ae23000bc4e9fbd0a203dec120f1:outputs/duanxian-audit/implementation-review-report.md | sha256sum
   git show d7fc94ac9fe4490c523bb112f6c4fb7a8115abe1:outputs/duanxian-audit/racc-001-acceptance.md | sha256sum
   git show 8a8280e28c5ab5b6369cca1a7fde3e7e822aec3d:outputs/duanxian-audit/racc-001-acceptance.md | sha256sum
   git show bb9598c36ac3b78dceaf8852b14dcca8edae8071:outputs/duanxian-audit/racc-001-acceptance.md | sha256sum
   ```

2. 保存实施起始完整 SHA、分支和初始 `git status --short --untracked-files=all`，确认唯一输出原先不存在，既有文件干净；如存在他人工作不要覆盖。只读核对必要 BASE 路径，不运行项目代码。读取凭据权限但不展示内容。
3. 在自己的 `.kunora/c-issues/` 生成七份 payload，核验标题/正文与公共声明；全量分页去重，按第二节处理旧项。payload/响应为控制材料，不成为仓库业务文件。
4. 按 C-I01–C-I07 逐条 POST、GET、即时记录编号/URL。仅在明确安全条件下重试一次；失败记录后跳过，公共阻塞则停止创建。不得用旧素材改写、补证、修源码或额外 ISSUE 补数量。
5. 重新全量列表和逐条回读，完成第四节可自行执行的检查。将结果、异常和 Owner 原样限制写入唯一 `outputs/duanxian-audit/iimpl-001-issues.md`；真实 API 成功不等于独立验收已 PASS。
6. 提交前检查记录 UTF-8、秘密/占位模式、数量与 URL 真实、`git diff --check`、暂存范围；仅 `git add -- outputs/duanxian-audit/iimpl-001-issues.md`。按实施契约署名普通提交，不 amend 他人历史，不 force push。记录可有后续普通修正提交，但各次只涉及此唯一新增交付文件。
7. 提交后以实施起始 SHA 比较候选：最终仅新增上述文件、所有既有文件字节未变，逐提交不夹带其他路径；记录 HEAD 与工作树字节一致。按该作业凭据安全推送其允许工作分支，再 `git ls-remote origin refs/heads/<实施契约工作分支>` 核远端完整 SHA。完整候选 SHA 不自指写入同一待提交文件，由最终交接给出。
8. 向编排方交接 job_ref、候选完整 SHA、记录文件 hash、七条真实编号/URL及状态、异常项和验证结果。七主题发布与所需检查全部完成且推送已核对后，末行输出 `DXAIIMPL-DONE-<tip7>`，其中 tip7 必须是实测远端候选前七位。若仍有失败/未知/未裁决重复，只交接真实部分结果与缺口，不输出完成哨兵或编造验收通过。

## 六、独立验收作业检查单与交接

C-验收由 **codex/gpt-6-astra** 执行。验收者独立封定 C-定义 SHA、C-实施起始/候选 SHA、线上 ISSUE 列表及记录文件 SHA-256，全文读本定义和唯一记录；按第四节逐项给 PASS/FAIL/BLOCKED，标出证据、检查时间及适用提交。静态事实回查 BASE，不将 B3 有争议的原句当作权威，不把本定义的自检当独立验收结论。

验收顺序：先核提交边界/输入 hash，再全量拉取 ISSUE 并逐条比对正文，然后重验高风险证据与去重/异常账，最后核远端交付、控制记录与哨兵。发布后的线上内容可能变化，须保存检查时的正文 hash 和更新时间；变化后重新核对受影响项，不沿用旧 PASS。不得直接编辑、评论、重开或关闭 ISSUE，不修改既有仓库文件；验收输出路径与允许分支由自己的冻结契约规定，本定义不擅自新增业务报告路径。

| 交接字段 | 提供方与内容 |
| --- | --- |
| definition_job_ref | 本轮固定为 `duanxian-audit-idef-001` |
| definition_candidate_sha / definition_file_sha256 | 本定义提交并核验后的完整 SHA / 文件 hash，由最终交接提供，不在正文预填自指值 |
| content_base | `92573f1cca40f37cee04d2beb8708ff33ba603d6` |
| B3 / A1 / A2 / A3 | 第一节四组完整提交、路径、SHA-256 |
| implementation_job_ref / start_sha / candidate_sha | C-实施的真实作业、起始与最终候选完整 SHA |
| implementation_branch / remote_tip | C-实施契约允许分支及 `ls-remote` 实测完整 tip |
| record_path / record_sha256 | `outputs/duanxian-audit/iimpl-001-issues.md` 与实际文件 hash |
| issue_map | C-I01–07 → 真实编号、URL、状态、正文hash、最后GET时间；未创建项明确无编号 |
| counts / failures / duplicates | 新建、已回读、重复、失败、未知数量及闭合关系；所有待处理原因 |
| control_evidence | 作业控制渠道提供的脱敏命令/退出码/时间与模型安排；不得包含 token，不进入第二业务文件 |
| checks / sentinel | 实际检查结果及与远端候选绑定的完成哨兵；未完成则不伪造 |

本定义的完成条件是：七项集合仅含交叉验证事实、六节和全部必需字段齐全、Owner 原文保留、提交规程可执行且有去重/失败处置、冻结机械门与唯一新增范围通过，并已推送到 `remote-agent/duanxian-audit-idef-001`。这些是 C-定义交付检查，不是 B 全量阅读通过、C-实施已发布或 C-独立验收已通过的声明。
