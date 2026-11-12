# 断线审视工作项 C 实施：ISSUE 提交记录

## 一、作业、封定输入与时间

- 作业：`duanxian-audit-iimpl-001`
- 仓库：`innuama-coder/ai-novels`
- 工作分支：`remote-agent/duanxian-audit-iimpl-001`
- 实施起始 SHA / 内容基线 BASE：`92573f1cca40f37cee04d2beb8708ff33ba603d6`
- 开始时间（UTC）：`2026-11-12T17:24:31Z`
- 七条最终回读完成时间（UTC）：`2026-11-12T17:30:54Z`
- C 定义书提交：`e63c9bd7f02063afb0a570f70cc8d1cb37d40fa9`
- C 定义书路径：`outputs/duanxian-audit/idef-001-def.md`
- C 定义书 SHA-256：`a096699f2e359fc18c0b95549306b67c254aa22e285a7284444d9a5e7a638c2d`

| 别名 | 报告提交 | 仓库相对路径 | 文件 SHA-256 |
| --- | --- | --- | --- |
| B3 | `ffb8c9a10b51ae23000bc4e9fbd0a203dec120f1` | `outputs/duanxian-audit/implementation-review-report.md` | `fe0dc30f0b16d1101edc1826079ef1e970334312dd463006798c540d05c71f13` |
| A1 | `d7fc94ac9fe4490c523bb112f6c4fb7a8115abe1` | `outputs/duanxian-audit/racc-001-acceptance.md` | `cd79394fe966cb109382f2e8b8f4ebe462de1c43a215b3b0649e4ed475faf3cb` |
| A2 | `8a8280e28c5ab5b6369cca1a7fde3e7e822aec3d` | `outputs/duanxian-audit/racc-001-acceptance.md` | `f1811317b130fe24c41da0e8acc4c32b46f1b88a13227644c444ab572495ff35` |
| A3 | `bb9598c36ac3b78dceaf8852b14dcca8edae8071` | `outputs/duanxian-audit/racc-001-acceptance.md` | `6c059fd18617a9d981aee0a2ba4afdf07c35ce2876d1b1824b3a35f481b02221` |

上述定义书与四份报告均按完整提交 SHA 取得、全文读取并重算哈希；七份请求体严格由定义书标记块确定性生成。线上正文路径、行号和 JSON Pointer 均绑定 BASE，不以最新分支替代。

## 二、Owner 原样裁决与不可变约束

三轮实施+三轮验收后，实施候选 r3（ffb8c9a）实质质量逐轮提升、核心事实发现已被 racc-001/raccr2 两轮交叉确认，但验收方「1444 文件全文阅读硬门」三轮未闭合——Owner 裁决采纳 r3 为审视结论工作基础进入工作项C；C 只能提交**交叉验证过的发现**，B 报告残余争议项不得入库；该裁决与限制须写入最终交付物与 ISSUE 正文（透明呈现）。

- C-实施交付物唯一路径＝`outputs/duanxian-audit/iimpl-001-issues.md`（ISSUE 编号与 URL 记录），唯一新增文件；ISSUE 本体提交到 GitHub innuama-coder/ai-novels。
- 仅提交三轮验收交叉确认的发现；预计 ISSUE 数量 5–9 条（以交叉验证裁定为准，不多不少）。
- C-实施执行器/模型＝kimi-code/k3.1-pro；C-验收＝codex/gpt-6-astra（Owner 冻结）。
- 审视任务全程不得修改仓库既有文件；ISSUE 正文必须包含 B 验收硬门未闭合的透明声明。
- 所有结论引用具体路径作证据；不得虚构仓库不存在的内容。

七条 ISSUE 均完整追加了定义书 `COMMON-BODY` 公共块，逐字保留上述 Owner 裁决、三轮 B 总验收 FAIL、全文阅读硬门未闭合、静态证据与现实运行分离、缺失留存不等于外部不存在等限制。本记录与线上发布不构成全仓审视 PASS、缺陷修复、现实运行失败认定或小说阶段新批准。

## 三、定义书条目到 ISSUE 的一一映射

| 本地键 | 冻结标题 | 严重程度 | 状态 | 实际编号与 URL |
| --- | --- | --- | --- | --- |
| C-I01 | [断线审视] 构思 CLI 的七条运行时路径及三份测试入口未适配当前布局 | high | CREATED_VERIFIED | [#1](https://github.com/innuama-coder/ai-novels/issues/1) |
| C-I02 | [断线审视] 两处 README 的 81 个技能计数与冻结树实际 82 个不一致 | low | CREATED_VERIFIED | [#2](https://github.com/innuama-coder/ai-novels/issues/2) |
| C-I03 | [断线审视] 17 份历史写作素材的 LLD 路径及 R07 的 HLD 章节引用需要迁移映射 | medium | CREATED_VERIFIED | [#3](https://github.com/innuama-coder/ai-novels/issues/3) |
| C-I04 | [断线审视] .gitattributes 的 HLD 字节稳定规则未匹配 engine 下的实际路径 | medium | CREATED_VERIFIED | [#4](https://github.com/innuama-coder/ai-novels/issues/4) |
| C-I05 | [断线审视] 07-13 历史 HLD 的 HLD-TRACE-CLOSURE P1 仍为冻结记录中的 open | medium | CREATED_VERIFIED | [#5](https://github.com/innuama-coder/ai-novels/issues/5) |
| C-I06 | [断线审视] 07-13 HLD 完整性报告的人审说明混用 v2.0 与 v3.0 | low | CREATED_VERIFIED | [#6](https://github.com/innuama-coder/ai-novels/issues/6) |
| C-I07 | [断线审视] 冻结树未留存三个机器交付文件，需补充同版复验的受控证据 | medium | CREATED_VERIFIED | [#7](https://github.com/innuama-coder/ai-novels/issues/7) |

计数闭合：记录数 7；distinct 编号数 7；新建并完成回读 7；旧项重复 0；失败 0；UNKNOWN 0；最终全量列表 ISSUE 数 7；清单外新增 0。七条均为 open，均不是 PR。

## 四、来源与候选绑定

所有条目的定义候选均为 `e63c9bd7f02063afb0a570f70cc8d1cb37d40fa9`，BASE 均为 `92573f1cca40f37cee04d2beb8708ff33ba603d6`。marker 的统一形式为 `<!-- duanxian-audit-idef-001:<本地键>:base=92573f1cca40f37cee04d2beb8708ff33ba603d6 -->`；最终列表中每个 marker 仅命中其对应编号。

| 本地键 | payload SHA-256 | 解码正文 UTF-8 SHA-256 | A1 / A2 / A3 对应来源 |
| --- | --- | --- | --- |
| C-I01 | `05964c22a0320236969a3f57174ec89bb42a886fcd3c4765d8e397f2859dba57` | `16c4784bf787401b43cf6cdf8aef6aa5a4bac6271a17018628c6f90f7af18e0a` | A1 §4.3 L103–104、F07；A2 §4.4 L131–132、§6 L193；A3 §4.4 L135、§4.5 L161–162、§4.2 L106 |
| C-I02 | `ab9c6380efe2237c39bfb7b0b2c992eee5ce3858f52bfa6e8385220242c0cf43` | `73394dadbe4bf26ae220ab23913828c2e5d597db18003d00d057fc8e265624fc` | A1 §4.3 L105；A2 §4.4 L133、§2 L43；A3 §4.5 L163、§2 L43 |
| C-I03 | `812e6f23c5e1d8d8dde6a3a4554f60f53289b22d7b22b5ff2f36d3eb551dfdb4` | `f7cf2cf36764afc17f3052dfb2834ab59ad9cbccfa8d902a9fae3641297d4b24` | A1 §4.3 L106–107；A2 §2 L46、§4.4 L134–135；A3 §4.5 L164–165、R3F07 L299–301 |
| C-I04 | `2637d7f7f0685fcf2a89597ab1402f9645c51c086cea8e84624fdfca66e6047c` | `724caded9a6c8bb4d60d1c01477d8341d79cd9e6d3267cf59e73678e595d350d` | A1 §5.2 L168、F08；A2 §6 F08 L194；A3 §4.2 L111、§6 L202 |
| C-I05 | `da4b61f346c69d03aa5314a4f671f02fec9c6d695bf34888dd26dde77abe7dea` | `6f0edc8749268702b34647c875ffca7136539d874333fd43c5b71b5306fc2ebf` | A1 §4.3 L108；A2 §4.4 L137；A3 §4.5 L167、§4.4 L153 |
| C-I06 | `5152e927b36bd31fe42da4579c1f9c55892378e754b981c7eb50ce1a7ad95d40` | `c15d55f0c8cf724453303a5d3f9d1961d974002d8f8db5a3a74de929a02d2a21` | A1 §4.3 L109；A2 §4.4 L138；A3 §4.5 L168 |
| C-I07 | `d4d536785e862123403b3711770e5f48dcd118ef6581c7141f7ac25d43702bef` | `ab19538cd2d67b221510ffacc498df2640a58970615fd9b6f52aac7187389a1c` | A1 §4.1 L77–78、§4.3 L110；A2 §2 L46、§4.1 L82、§4.4 L139；A3 §2 L46、§4.1 L88、§4.5 L169、R3F07 L299–301 |

## 五、尝试、去重与逐条回读

初始全量分页在第一个空页成功结束，原始条目为 0。每条 POST 前均重新分页，并扫描当前条目 marker 与冻结标题；后续列表只出现本次已创建条目，没有需要归并的旧 ISSUE。每条均只 POST 一次，transport=0、HTTP=201；首次 GET 一次，transport=0、HTTP=200；最终复核再 GET 一次，transport=0、HTTP=200。标题和完整正文均在 JSON 解码后与 payload 逐字一致，未使用摘要比对代替。

| 本地键 | 当次预查 ISSUE 数 / 当前项重复命中 | POST 时间（UTC） | 首次 GET 时间（UTC） | 最终 GET 时间（UTC） | 回读结论与异常 |
| --- | --- | --- | --- | --- | --- |
| C-I01 | 0 / 无 | `2026-11-12T17:28:34Z` | `2026-11-12T17:28:34Z` | `2026-11-12T17:30:51Z` | 精确一致；无重试 |
| C-I02 | 1 / 无 | `2026-11-12T17:28:42Z` | `2026-11-12T17:28:42Z` | `2026-11-12T17:30:51Z` | 精确一致；无重试 |
| C-I03 | 2 / 无 | `2026-11-12T17:28:52Z` | `2026-11-12T17:28:52Z` | `2026-11-12T17:30:52Z` | 精确一致；无重试 |
| C-I04 | 3 / 无 | `2026-11-12T17:29:07Z` | `2026-11-12T17:29:07Z` | `2026-11-12T17:30:52Z` | 精确一致；无重试 |
| C-I05 | 3 / 无 | `2026-11-12T17:29:14Z` | `2026-11-12T17:29:15Z` | `2026-11-12T17:30:53Z` | 精确一致；预查列表当时未显示全部既有新项，但当前项 marker/标题无重复，最终完整列表与逐条 GET 已闭合 |
| C-I06 | 5 / 无 | `2026-11-12T17:29:26Z` | `2026-11-12T17:29:27Z` | `2026-11-12T17:30:53Z` | 精确一致；无重试 |
| C-I07 | 6 / 无 | `2026-11-12T17:29:35Z` | `2026-11-12T17:29:36Z` | `2026-11-12T17:30:53Z` | 精确一致；无重试 |

最终全量分页包含一个七条目页及一个空终止页；排除 PR 后恰为 #1–#7。七个 marker 各自唯一，编号与上表互对一致。没有 401/403、422、429、5xx、超时或断连，没有 POST 重试、GET 重试、重复创建、编辑、评论、关闭、重开或删除已有 ISSUE。没有失败项需要登记 UNKNOWN 或交接重试；C-I05 的预查可见性差异已如实保留，不据此宣称当时列表完整覆盖全部新项。

## 六、证据与交付检查

- 输入版本：C 定义书及 B3/A1/A2/A3 的文件 SHA-256 全部符合封定值。
- 发布内容：七次最终 GET 的编号、URL、open 状态、非 PR 类型、冻结标题、完整正文、marker 唯一性和正文 SHA-256 全部一致。
- C-I01：七个正确 runtime 均存在、七个双 `engine/` 路径均不存在，三份测试入口的 `parents[4]` 与旧 `projects` 布局均已静态复核。
- C-I02：两处 81 声明与 BASE 的 82 个一级 `SKILL.md` 入口已复核。
- C-I03：17 个源行旧 LLD 引用与 17 个迁移目标逐项复核；R07 五个 §10.x 指称与 HLD 版本/章节位置已复核。
- C-I04：三个真实路径的 text/eol 共六项均为 `unspecified`。
- C-I05/C-I06：历史 open/fail/pending/blocked、两文件检索范围、v2/v3 标签与 manifest 的 v3 权威均已复核。
- C-I07：1444 条 BASE 跟踪路径中三个机器 basename 均为零；批准范围、完成记录 Pointer、hash 引用和顶层 `unresolved_items` 已复核。
- 执行边界：未导入仓库模块，未运行项目 CLI、pytest、validator、构建或小说流水线，未修改任何既有跟踪文件。凭据文件已核可读且权限为 600；凭据仅经命令替换使用，未进入 payload、响应记录、终端输出或本交付物。
- 文件范围：起始 SHA 为 BASE，初始工作树干净且唯一输出原先不存在。控制 payload/响应/脚本位于未提交的 `.kunora/c-issues/`；业务写入仅 `outputs/duanxian-audit/iimpl-001-issues.md`。提交前 UTF-8、秘密模式、URL、diff 和暂存范围检查，以及提交后 BASE 到候选的最终范围、HEAD 与工作树一致性、远端 tip 和记录文件 hash，均以实际执行结果交接；本文不预写尚未发生的提交后通过状态或自指候选 SHA。

## 七、交接结论

C-I01–C-I07 七主题均已按定义书创建并取得唯一真实编号 #1–#7；最终全量列表和逐条 GET 已完成，正文与确定性 payload 完全一致。无失败、未知或未裁决重复项。线上结果可供 C-独立验收封定；本实施自检不冒充独立验收 PASS。

后续交接须给出实际候选完整 SHA、本记录文件 SHA-256、远端分支实测 tip 和提交后范围检查结果。只有这些交付检查实际通过后，完成哨兵才可绑定实测远端 tip 前七位。
