# H1-C V2 HTML 契约

The default navigation renders the bounded decision-control surface measured by
H1-A. Full P1 evidence is rendered separately as closed, keyboard-accessible
`details` entries carrying the exact stage, source id, JSON pointer and value
hash. Drill-down content is available but is not silently charged as default
reading. The page states that source binding is provenance, not semantic
equivalence, and never describes bulk anchor binding as semantic completeness.

## 1. 责任与边界

H1-C 是 H1 内容组装后的呈现节点。输入内容的唯一事实源是 H1-A 已验收的 `human-review-report.json`。H1-C 可以选择固定的排版、颜色和几何位置，但不得：

- 补写、删改、摘要、翻译或解释报告内容；
- 从 P1、规划包或片段包反向生成新展示内容；
- 以关键词、NLP 或人工规则猜测关系；
- 改变图模型的 ID、顺序、分组、方向、标签、来源或文字等价物；
- 收集或预选作者决定；
- 生成 H1/stage completion，或推进到 `completed`。

## 2. Python API

```python
render_html(report: Mapping[str, Any]) -> str

validate_html_document(
    document: str,
    report: Mapping[str, Any],
) -> dict[str, Any]

validate_html_package(
    package_root,
    *,
    p1_package,
    plan_package,
    plan_input_gate,
    plan_workspace_state,
    fragment_package,
    fragment_workspace_state,
    assembly_package,
    assembly_workspace_state,
    workspace_state,
    plan_logical_package_path="H1/plan",
    fragment_logical_package_path="H1/fragments",
    assembly_logical_package_path="H1/assembly",
    plan_active_return_request=None,
    runtime=None,
) -> dict[str, Any]

run(
    package_root,
    *,
    p1_package,
    plan_package,
    plan_input_gate,
    plan_workspace_state,
    fragment_package,
    fragment_workspace_state,
    assembly_package,
    assembly_workspace_state,
    workspace_state,
    coordinator,
    logical_package_path="H1/html",
    plan_logical_package_path="H1/plan",
    fragment_logical_package_path="H1/fragments",
    assembly_logical_package_path="H1/assembly",
    plan_active_return_request=None,
    active_return_request=None,
    runtime=None,
) -> HtmlReceipt
```

`run` 的 `package_root` 必须尚不存在。输入对象必须是 runtime 的密封文档；不得仅传裸 JSON 来跳过哈希校验。

## 3. 输入状态链

| 输入 | 要求 |
|---|---|
| P1 包 | `stage-completion.json` 为 P1/ready，且被规划门绑定 |
| 规划包 | H1-A 正式规划包，manifest 路径默认 `H1/plan/package-manifest.json` |
| 规划门/工作区 | 同 run；规划门精确绑定 P1，工作区为规划所用的 `initialized` |
| 片段包/工作区 | H1-B 正式包，工作区为片段生成所用的 `planned` |
| 组装包/前工作区 | H1-A 正式组装包，工作区为组装所用的 `fragments_ready` |
| 当前工作区 | 密封、同 run/session、状态仍为 `assembled`，artifacts 精确绑定三份 manifest |

H1-C 首先调用 H1-A `validate_assembly_package`，不得复制、缩写或旁路该验证器。随后独立验证当前 assembled 工作区、报告预算、run/session 和四个输入目录的执行前后清单。任何输入在验证与发布之间变化都必须失败。

## 4. HTML DOM 契约

根元素：

```html
<html lang="zh-CN" data-render-contract="h1-html-v2">
```

必须满足：

1. `<title>` 和页面中唯一 `<h1>` 逐字等于 `report.title`。
2. 存在唯一主导航；其中每一项按 `review_path` 顺序携带精确的 `data-path-id`、`data-path-kind` 与 `data-visible-element-ids`。后者是 `visible_element_ids` 的 UTF-8 compact JSON 数组，经 HTML 属性转义；validator 必须在实体解码后逐项与报告全等。
3. 默认可见且按评审路径呈现：
   - `#section-world`
   - `#section-storylines`
   - `#section-characters`
   - `#section-fragments`
   - `#section-decision`
4. 五个 `visual_models` 各生成一个 `.semantic-visual` SVG。visual card、SVG 和 `.visual-text-equivalent` 都携带精确的 `data-text-equivalent-module-id`；SVG 自身还携带精确的 `data-visual-id` 和 `data-semantic-role`，文字等价容器也携带 `data-visual-id`。三类容器必须逐图、逐序绑定同一个报告值。
5. 图中的 group/node/edge 分别携带原始 ID 和 order；edge 携带原始 direction。`directed` 显示终点箭头，`bidirectional` 同时显示起点和终点箭头，`undirected` 不显示箭头。
6. 每个 SVG 紧邻一个 `.visual-text-equivalent`，以可展开的自然中文逐项呈现相关 group/node/edge 的标签、摘要和关系，使图形不是唯一信息载体。上游压缩式 `text_equivalents.text` 仅是机器绑定材料，不得在可见页面复述成口号；element IDs、source IDs 与原始 text-equivalent 绑定只保留在机器可核验结构中。
7. 同一自然语言结论不能因为同时存在于首屏、报告标量和模块定义而重复展示。若标量与某个模块定义逐字相同，渲染器必须把它们合并成一个作者可见条目，并在该条目保留模块标题与机器追踪属性；不得在相邻卡片或首屏再次复述。
8. 所有来源、控制条目、约束、边界、片段正文和决策选项均来自报告字段并经过 HTML 转义。
9. 决策选项只作为静态文字，不得使用 radio、checkbox、button 或默认状态表达选择。

五个固定语义角色恰好各一次：

- `control_logic_chain`
- `world_environment_map`
- `storyline_architecture`
- `major_event_timeline`
- `character_relationship_network`

## 5. 安全、访问与打印

- UTF-8 单文件，不引用外部字体、样式、图片、脚本或网络资源。
- CSP 至少为：`default-src 'none'`、`script-src 'none'`、`connect-src 'none'`、`object-src 'none'`、`base-uri 'none'`、`form-action 'none'`。
- 禁止 `script/form/input/button/select/textarea/iframe/object/embed/link`，禁止事件处理属性、任何 `download`、meta refresh、`xlink:href`，以及 `src/srcset/action/formaction/poster/data/cite/background/manifest/longdesc/usemap/profile/ping` 等 URL-bearing 属性；属性名和值按 HTML 实体解码后、大小写不敏感判断。
- 唯一允许的 `href` 是生成器定义的 `#main-content` skip-link，以及逐项与 `review_path` 匹配、目标 section ID 已存在的五个导航锚点；其余外部、片段或悬空链接都拒绝。
- 禁止任何元素级 `style` 属性；文档只能包含一个且内容逐字等于内置 `CSS` 的 `<style>`。此外，CSS 出现大小写不敏感的 `url(` 或 `@import` 时拒绝。
- 提供跳转主内容链接、语义 landmark、连续标题层级、可见 `:focus-visible`、SVG 的 `title/desc/role=img`。
- 窄屏可回流；宽图允许键盘可聚焦的局部水平滚动，文本等价物始终可回流。
- `@media print` 移除阴影和交互外观，防止关键卡片与片段无意义断裂；不得依赖颜色表达唯一含义。

### Storyline timeline rendering semantics

For `major_event_timeline`, the SVG is a shared time spine rather than a list
of boxes. Nodes with the same `temporal_label` share one x-coordinate; lanes
carry distinct storyline functions on the y-axis. Node styling distinguishes
`opening`, `setup`, `probe`, `turning_point`, `reveal`, `climax`, `payoff`, and
`aftermath`, while the visible legend and node copy translate them into natural
Chinese such as “铺垫”“探问”“转折”“高潮”“回收” and “余波”. For the sealed
timeline labels whose author-facing narrative roles were accepted by H1-A, that
accepted label-to-role projection is authoritative for the visible subtitle,
legend, and color. A stale raw `kind` remains traceable in `data-kind` but must
not turn an early probe into a climax or hide an accepted climax as generic
progress. Machine phase labels
such as `P1` are rendered as “第一阶段”; raw marker kinds and internal node labels
remain available only through non-visible machine attributes. Every node thus
exposes its time and narrative function without requiring the author to learn
the model vocabulary, and color is never the only carrier of meaning. Rendering
must not reinterpret graph order, edges, or source bindings.
The admitted legacy `control-node` and `节点` kinds are shown as “推进”; every
other unknown kind is rejected before rendering rather than exposed to the
reader.

## 6. 包结构

```text
human-review-report.html
render-record.json
validation.json
package-manifest.json
implementation/
  schemas/...
  skill/run_v2.py
  skill/SKILL.md
  skill/v2-html-contract.md
```

除此以外不允许出现其他文件，尤其禁止 `stage-completion.json`。

`render-record.json` 固定：

- `schema_version`: `2.0`
- `stage`: `H1`
- `operation`: `H1-C-render`
- `render_contract`: `offline-accessible-h1-v2`
- 精确绑定当前 workspace reference、P1 completion、plan/fragment/assembly manifests、输入 report、输出 HTML 和实现快照目录。

`validation.json` 只能在全部检查通过后为 `ready`。`package-manifest.json` 的 profile 必须为 `h1-html`，父状态哈希必须等于当前 assembled workspace reference 的哈希。

## 7. 原子发布与状态推进

正式生成顺序：

1. 验证全部输入并记录目录清单。
2. 纯渲染，立即做 HTML 文档验收。
3. 在目标同父目录的临时目录写入全部文件和实现快照。
4. 以正式 `validate_html_package` 完整重验临时包。
5. 再比对四个输入目录清单，确认无 TOCTOU。
6. 原子改名为最终目录。
7. 对最终目录再次完整重验。
8. coordinator 仅接受 `assembled -> rendered`。

任何步骤失败都清理临时目录；目标目录不得留下半包。已经存在的目标目录必须拒绝覆盖。

## 8. 验收判定

以下任一情况都必须拒绝：

- 上游正式验证器失败或输入不属于同一 run/session；
- 当前工作区不是精确 assembled 状态；
- 报告超过十分钟预算；
- 重渲染字节与 HTML 不同；
- 标题、评审路径、五板块、五图、图模型逐值信息或文字等价物缺失；
- 外链、脚本、表单、事件处理器、作者决定预选或 CSP 失效；
- record、validation、manifest、实现快照或文件边界不精确；
- 输入树在验证期间发生变化；
- 试图生成阶段完成或从非 assembled 状态推进。

## 9. 作者可见文本流

作者可见文本检查以 DOM 阅读流为准，而不是逐次 `handle_data` 检查：

- 同一块级元素内，`em`、`strong`、`span`、`b`、`i`、`tspan` 等行内元素
  不得打断词语；字符实体解码后也必须参与同一文本流检查。
- `p`、标题、列表项、section、表格单元、图注及独立 SVG 文本等块级边界
  会结束当前文本块，避免把相邻自然段错误拼成一个词。
- `script`、`style`、`template`、`noscript` 不属于作者阅读流；除唯一受控样式外，
  其余容器均被安全合同拒绝。
- `hidden` 或 `aria-hidden="true"` 子树不得承载作者文本；`aria-hidden` 只允许
  `true`、`false`，其他值一律 fail closed。空的装饰性 `aria-hidden="true"`
  元素可以保留。
- `data-*`、机器 JSON、脚本与样式内容不参与可见文案扫描；不可见追溯绑定保持原样。
