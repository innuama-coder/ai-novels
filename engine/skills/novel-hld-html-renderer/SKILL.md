---
name: novel-hld-html-renderer
description: 将已通过独立忠实度审查的 HLD 人审报告 JSON 确定性渲染为单文件离线 HTML/SVG，并生成 HUI render target registry。用于 novel-hld-autonomous 的 HH1-C 内部 script task；不改写报告内容、不读取故事源、不发布 HH1 completion。
---

# HLD 人审报告确定性 HTML 渲染器

## 必读

依次完整阅读：

- [输入输出契约](references/input-output-contract.md)
- [方法论](references/methodology.md)
- [SOP](references/sop.md)
- [运行时契约](references/runtime-contract.json)

研究依据见 [sources](references/sources.md)。

## 唯一职责

只把 HH1-A 已密封的 `hld-human-review-report.json` 按固定模板和 CSS 渲染为单文件、可离线打开和打印的 HTML/SVG，并生成与 DOM 全等的 `render-target-registry.json`。HH1-B 必须已对完全相同的 report hash 给出 pass。

每个可见报告元素只创建渲染容器 ID：

`HUI-<HRE-or-HVG-id>-<render_role>-<zero_based_ordinal>`

HTML 用 `data-render-target-id` 登记 HUI，用 `data-report-element-id` 回指原 `HRE-/HVG-`。本技能不创建任何新语义元素。

## 硬边界

- 不摘要、润色、删减、补充或重新排序报告结论。
- 图形只消费 report JSON 的 visual model data；布局坐标是固定表达，不是新故事事实。
- 不读取 HP1、构思、HA1–HK1、聊天、旧报告或任何故事源。
- 不评审报告忠实性；HH1-B pass 是准入，不由本技能重做。
- 不使用 CDN、远程字体、外链、iframe、脚本或未经转义的 HTML。
- 只生成 `result_scope=composite_internal` 内部结果；HH1 publisher、顶层包、completion 和作者门属于 Harness。
- 作者可见页面只讲故事方案和真正需要作者判断的问题；必须使用具体的人、地点、行动和后果来叙述，不得显示流程说明、验证解释、来源 ID/路径、schema/枚举、职责标签、逐卡制式提问或 Agent 备忘录句法。
- “世界环境定义”必须与“具体地点定义”分开：前者解释城市、当地人、社会、技术和气候等宏观生活环境，后者解释实验室、控制室等可进入的具体场所；不得混成一组泛化卡片。跨城故事至少完整定义四座实际承担不同事件的城市，逐城用自然段落说明规模、城区、生活质感、季节和关键事件，并说明人员、物品与消息怎样跨城流动；季节必须有明确时间窗和物理影响；普通人画像必须覆盖每一座城市，不得用“居民照常生活”替代。精确机器结构只用于隐藏校验，作者页面不得逐字段转录。

## 执行

Harness 签发 work order 后运行：

```powershell
python scripts/run_skill.py <work-order.json>
```

需要独立复核已生成包时运行：

```powershell
python scripts/validate_render.py <package-directory>
```

ready 内容包精确包含：

`hld-human-review-report.html / render-target-registry.json / render-execution.json / validation.json / package-manifest.json`

包外 `stage-result.json` 必须是 `composite_internal/ready`，且不得有 completion。
