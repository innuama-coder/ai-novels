# 输入输出契约

## 输入硬准入

当前 Harness work order/input gate 必须满足：`stage=HH1`、`action=execute`、`exact_owner_skill=novel-hld-html-renderer`、top-level upstream 精确为 `[HB0,HP1,HQ2]`、`unresolved_projection=[]`。二者 run、state、owner、implementation、allowlist、return/revision binding 必须逐值一致；所有引用 path 必须受控、sha256 当前。

HH1-A report 与 HH1-B review 的 consumer revision 必须等于当前 HH1 work order revision。HP1/HQ2 是已接受的封存上游，允许来自更早修订；其真实性由同 run、正确 stage/status、completion/manifest 成员关系以及 work-order 精确 artifact 引用共同证明，不得错误要求其 revision 等于当前 HH1 consumer revision。

内容读取权只有：

- HH1-A 密封 `hld-human-review-report.json` 与 manifest；
- HH1-B 密封 `presentation-fidelity-review.json` 与 manifest；
- 固定 report schema、HTML template、CSS、renderer implementation snapshot。

不得授予或读取 HP1、canonical、构思、故事源、聊天、旧报告或预期答案。HH1-B 必须 `verdict=pass`，其 `report_ref` 必须逐值等于当前 HH1-A report 引用；renderer snapshot hash 必须等于 work order `implementation_sha256`。

## report 契约

输入必须通过 [HH1-A 权威 report schema](../../novel-hld-review-report-assembler/references/hld-human-review-report.schema.json)。作品名来源于 `title_and_decision_scope`；评审范围、版本、状态、来源定位和内部分类只属于机器数据，不得出现在默认可见页面。十个内容域中的每个展示元素使用 `HRE-`，visual models 使用 `HVG-`。五张世界环境卡、角色定义与具体地点定义必须分别显示为独立结构卡，但结构卡不能显示成字段表。城市、跨城路线、普通人和季节必须分别使用 `city_stories / route_stories / ordinary_people_stories / season_story` 的自然叙述；对应的 `city_network / ordinary_people_portraits / season_profile` 只用于精确验证和 DOM 追踪，不得逐字段抄到作者页面。其余元素使用公共字段 `id / element_kind / conclusion / source_ids / locators / visual_role / review_question`。Renderer 不接受 `element_id` 同义字段。

## 渲染契约

- 每个 report element 恰好生成一个带 `data-render-target-id` 与 `data-report-element-id` 的可见 DOM 容器。
- 文档标题从 `title_and_decision_scope` 开头的书名号标题确定性提取；第一屏在目录和评审方法之前单次呈现第一个整体叙事架构元素，让作者先看见“这是什么故事”。该元素不得在后文重复。
- `model_kind` 只作为机器数据；默认可见图形类型必须经闭合中文映射呈现，未知值在输出前失败，不能把英文枚举暴露给作者。
- HUI ID 固定为 `HUI-<report_element_id>-<render_role>-0`；当前 profile 每元素只渲染一次，因此 ordinal 固定从 0 开始且集合中唯一。
- `visual_role` 作为自然中文标题，`conclusion` 作为正文；只有 `open_items_constraints_and_lld_boundary` 的 `review_question` 可显示为“请你判断”。其他 review question、source IDs、locator、element kind、model kind 和内部 ID 都不得进入默认可见文本。
- 作者可见正文必须按普通人的阅读方式组织：先说谁或哪里，再说发生什么，最后说明为什么重要。不得出现工作流、审计、schema、控制链、输入输出、职责标签或 Agent 备忘录句法。跨标签拆开的违规词、密集分号和重复段落也必须在输出前拒绝。
- HVG 使用内联 SVG，必须含 `role=img`、`aria-labelledby`、首子元素 `<title>` 和 `<desc>`，并提供自然中文的可见文本替代；不得显示绑定清单或审计说明。
- HTML 必须有 `lang`、准确 `<title>`、skip link、header/nav/main/footer landmark、唯一 h1、顺序 heading、可键盘访问的 fragment links。
- CSS 内联；支持 320 CSS px reflow、长字符串换行、forced colors、reduced motion 和 `@media print/@page`。不得依赖 JS。
- 禁止远程 URL、外部资源、script、iframe、object/embed、非 fragment link 和未转义输入。
- 相同 report/template/CSS/renderer bytes 必须产生字节完全相同的 HTML、registry、execution 和 validation。

## render target registry

`render-target-registry.json` 顶层字段和每个 target 都由 schema 冻结。每项包含：

- `id`：HUI ID；
- `dom_locator`：`[data-render-target-id="<HUI>"]`；
- `render_role`；
- `report_element_id`：原 HRE/HVG；
- `report_element_kind`；
- `visual_model_id`：HVG 时同其 ID，否则 null；
- `content_sha256`：该原始 report element 的 canonical JSON hash。

registry HUI 集合必须与 HTML `data-render-target-id` 集合全等；`data-report-element-id` 回指集合必须与 report HRE/HVG 集合全等。

## 交付与结果信封

ready 内容包精确是 catalog 2.4-B 的五文件 profile。manifest 不包含包外 work-order result；包外 result 固定 `result_scope=composite_internal`、`result=ready`、只有 `internal_manifest_ref`，`completion_ref=null`。

输入、hash、fidelity binding 或隔离失败 → fail closed，不渲染。脚本/模板/registry 本地缺陷 → `revise/local_candidate`。本技能不得生成 HH1 顶层结果、publisher 包或 completion。
