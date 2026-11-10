# HTML 生成交付契约

## 1. 输入

必须提供：

1. `assembly-package`
   - `human-review-report.json`
   - `human-review-report.md`
   - `assembly-execution.json`
   - `validation.json`
   - `package-manifest.json`
2. `plan-package`
3. `fragment-package`
4. `R1-package`

`assembly-package` 是内容权威，但仍须用后三个包重新完成上游验收，防止伪造、过期或断链输入。

## 2. 输出

### `human-review-report.html`

必须：

- 是 UTF-8、`lang="zh-CN"` 的单文件 HTML；
- 以 `review_contract.work_title` 作为唯一 `<h1>`，并在浏览器标题中同时显示
  《作品名》与“小说构思人审报告”；不得用梗概代替作品标题；
- 精确绑定 `human-review-report.json` 的 SHA-256；
- 嵌入可反解析且与输入完全相等的报告 JSON；
- 使用 `editorial-review-desk-v1`；
- 完整显示 orientation/world/story/characters/fragments/decision；
- 用人物名、故事线名和“主线/支线/背景线”本地化标签呈现正文，不显示机器 ID；
- 生成构思控制总链、系统因果链、环境承载图、故事线阶段泳道和人物关系网络
  至少五张内联 SVG，
  而不只输出卡片或视觉模型字段列表；
- 全部 SVG 均有无障碍标题与说明，并在窄屏容器内独立横向滚动；
- 默认可见六层控制主链、每个对象的控制摘要和全部主要事件控制链；支持性运行
  参数可以渐进展开，但定义、因果、边界和下游责任不得藏入追溯层；
- 默认显示全部小说片段；
- 只把追溯细节放入 `<details>`；
- 包含跳过导航、语义 landmarks、逻辑标题、显式表单标签；
- 四组判断均无默认选择；
- 支持 320px 单列重排、键盘焦点、减少动态和打印；
- 不含网络依赖、外部 URL 或内联事件处理器；
- 用 HTML 转义把上游字符串当作文本，而不是可执行标记；
- 设置限制资源加载的 CSP。

### `render-record.json`

必须声明：

- skill、mode、run_id；
-完整固定 style contract；
- 上游 report、manifest、validation 哈希；
- 当前技能全部源文件哈希；
- HTML 哈希。

### `package-manifest.json`

绑定 HTML 与 render record，并声明唯一 `author_review_artifact`。

### `validation.json`

只能是：

- `ready`：全部输入、确定性、结构、可访问性、安全和哈希检查通过；
- `blocked`：任一硬条件失败。

## 3. 内容忠实性

页面不得：

- 改写、摘要、翻译或补充报告；
- 删除世界系统、主要环境、故事线、时间线阶段、核心人物、关系层或片段；
- 把机器 ID 当作人类可见解释的替代品；
- 以视觉组件改变原始语义；
- 通过直接编辑 HTML 修复上游内容。

验证器以“嵌入 JSON 完全相等 + HTML 必须由当前模板重新生成得到相同字节”双重检查确定性。

## 4. 作者决定

页面状态固定为“待作者判断”。页面生成成功、页面被打开、或本地导出评审草稿均不构成：

- 作者批准；
- 构思阶段完成；
- 进入小说开发的授权。

正式决定必须由工作流另行接收，并绑定当前 report 与 HTML 哈希。
