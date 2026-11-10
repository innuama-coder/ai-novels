# SOP

## 1. 确认任务边界

确认任务是“呈现已经验收的构思报告”，不是写报告、改构思或写片段。固定使用
`editorial-review-desk-v1`，不询问主题偏好。

## 2. 完成上游硬准入

调用生成器时同时传入 assembly、plan、fragment、R1。生成器必须重新运行
`novel-conception-human-review-assembler` 的 assemble 验证。

若失败：

- 内容或覆盖问题返回报告设计/组装技能；
- 片段问题返回片段技能；
- 构思问题返回 R1；
- 不创建伪 `ready` HTML。

## 3. 确定性渲染

按固定顺序渲染：

1. orientation；
2. world；
3. story；
4. characters；
5. fragments；
6. decision；
7. 非正文追溯。

所有上游文本通过 HTML 转义。原始 JSON 以 `application/json` 嵌入，并将 `<`
写成 Unicode 转义，避免提前关闭 script 元素。
页首必须直接读取 `review_contract.work_title`，以《作品名》作为唯一 `h1`；
故事身份只能作为副标题，不得参与标题推断。
故事阶段先将 line ID 映射为故事线名称并生成泳道；人物关系先将 character source
ID 映射为人物名并生成关系网络。机器 ID 只保留在锚点、嵌入 JSON 或追溯区。

固定生成至少五张内联 SVG：

1. 六层构思控制总链呈现从世界观命题到终局契约的推导；
2. 系统节点与视觉模型边组成系统因果链；
3. 主要环境组成环境承载图，每格显示特征、职责、变化；
4. 时间线阶段与故事线进入关系合并为因果泳道图；
5. 人物按核心、近层、外层确定性布局，关系连线按层级着色并编号。

SVG 是快速阅读层；全部精确字段仍由随后的卡片、时间线和关系摘要显示。

## 4. 生成 provenance

写入：

- report、assembly manifest、assembly validation 哈希；
- 固定 style contract；
- 当前技能文件哈希；
- HTML 哈希。

manifest 只把 HTML 指定为作者评审入口。

## 5. 硬验收

验证器依次检查：

1. 上游四包仍然有效；
2. manifest、record、skill 源文件哈希有效；
3. 页面 landmarks、section、标题、skip link 完整；
4. report JSON 可反解析且逐字段相等；
5. HTML 与当前确定性渲染结果逐字节相等；
6. 六个正文区默认可见，片段 ID 全部出现；
7. 五张 SVG、无障碍标题说明、控制总链、故事泳道与关系编号图完整；
8. 控件显式标注，四项判断完整且无预选；
9. 无外链、危险 URL、inline handler 或默认隐藏；
10. 固定色板、响应式、打印、焦点与减少动态规则存在。

## 6. 人工抽查

在浏览器和打印预览中各抽查一次：

- 桌面：图形能加快对比，正文不拥挤；
- 320px：主要内容单列，无页面级横向阅读；
- 键盘：跳过导航与焦点清楚；
- 打印：导航和按钮不占版面，片段仍完整；
- 决策：没有任何默认批准或退回。

自动验证通过但人工抽查发现视觉阻断时，不改内容；修改固定模板并让全部测试重跑。
